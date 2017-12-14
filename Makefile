# prefix ping deploy
#
# Goal here is not so much to execute a process
# but to document a coherent approach on various systems
# the two I care about are
#	- redhat & derivatives for public servers
#	- debian & derivatives for desktop development
#
# web-client <-> nginx <->  socket <-> uwsgi <-> flask-script
#
# (http)   (web-service)     (service(internal-service))

# if there are a number of uwsgi services they may be under the
# umbrella of an "emperor" uwsgi that marshalles "vassel" services


# !!! CHANGE ME
# the base name of the app in the filesystem
APP := prefixping

# !!! CHANGE ME
# this is the non root owner of the app
# app should not be owned by nginx or uwsgi either
OWNER := tomc


# if not root (RECOMENDED)
# then just outputs the steps decorated with `sudo`
ifneq ($(shell whoami), root)
	# -n, --just-print, --dry-run, --recon
	MAKEFLAGS += n
	SUDO := sudo
else
	# hope you know what you are doing
	SUDO :=
endif

# different OS's have different conventions ...
UNAME := $(shell uname)


# Distros may be converging on systemd/systemcrtl
# but not on where the bits should live.
# Figure out distro we are on and adapt to local conventions
# WEBSRV is the owner of public facing webserver (nginx)

ifeq ($(UNAME), Linux)
	DIST := $(shell grep "^ID=" /etc/os-release |cut -f2 -d '=' | tr -d '"')
	ifeq ($(DIST), centos)
		SERVICE := /usr/lib/systemd/system
		WEBSRV := nginx
	else ifeq ($(DIST), ubuntu)
		SERVICE :=  /etc/systemd/system
		WEBSRV := www-data
	else ifeq ($(DIST), linuxmint)
		# system dir may not exist
		SERVICE := /etc/systemd/system
		WEBSRV := www-data
	#else ifeq ($(DIST), ???)
	#	SERVICE := /x/y/z
	#	WEBSRV := yomama
	endif
endif

# expecting to be served from a user owned dirctory
# named after the app under /srv/
PWD := $(shell pwd)

NX := /etc/nginx
########################################################################

all : start

socket :
	# communication between nginx and uwsgi
	#### centos -- consider adding uwsgi user to nginx group for selinux
	# usermod -a -G nginx uwsgi
	#### make group for directory /run/$(APP) be be the webserver
	$(SUDO) mkdir /run/$(APP)
	$(SUDO) chown $(OWNER):$(WEBSRV) /run/$(APP)
	### sticky too?
	$(SUDO) chmod g+s /run/$(APP)

service: $(SERVICE)/$(APP).service
	# systemd service in place

enabled: $(NX)/sites-enabled/$(APP)
	# nginx configuration enabled

$(SERVICE)/$(APP).service : $(PWD)/$(APP).service
	$(SUDO) unlink $(SERVICE)/$(APP).service
	$(SUDO) ln -s $(PWD)/$(APP).service $(SERVICE)$(APP).service

$(NX)/sites-available : $(NX)/
	$(SUDO) mkdir $(NX)/sites-available
	$(SUDO) grep "include $(NX)/sites-enabled/\\*;" $(NX)/nginx.conf

$(NX)/sites-available/$(APP) :  $(NX)/sites-available $(APP).nx_location
	$(SUDO) unlink $(NX)/sites-available/$(APP)
	$(SUDO) cp $(APP).nx_location $(NX)/sites-available/$(APP)

$(NX)/sites-enabled : $(NX)/sites-available
	$(SUDO) mkdir $(NX)/sites-enabled

$(NX)/sites-enabled/$(APP) : $(NX)/sites-available/$(APP)
	$(SUDO) unlink $(NX)/sites-enabled/$(APP)
	$(SUDO) ln -s $(NX)/sites-available/$(APP) $(NX)/sites-enabled/$(APP)

inichk:
	# check your "net user" is not commented out in the uwsgi ini filr
	grep $(WEBSRV) ./$(APP).ini

start : socket service enabled inichk
	$(SUDO) systemctl stop  $(APP)
	$(SUDO) systemctl start  $(APP)
#	$(SUDO) systemctl enable $(APP)
	$(SUDO) nginx -t &&  $(SUDO) nginx -s reload

clean :
	# These are ONLY to be done by hand
	#$(SUDO) unlink $(NX)/sites-enabled/$(APP)
	#$(SUDO) unlink $(NX)/sites-available/$(APP)
	#$(SUDO) unlink $(SERVICE)/$(APP).service
	#$(SUDO) unlink $(SERVICE)/$(APP).service
	#$(SUDO) rm /run/$(APP)/uwsgi_nginx.socketS
	#$(SUDO) systemctl stop  $(APP)
