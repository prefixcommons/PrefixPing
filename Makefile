# prefix ping deploy

# web client <-> nginx <->  socket <-> uwsgi <-> flask-script
#
# (http)        (service)             (service? (  service  ))


# if not root, then just print steps
ifneq ($(shell whoami), root)
	# -n, --just-print, --dry-run, --recon
	MAKEFLAGS += n
	SUDO := sudo
#	$(shell echo "commands displayed only") 
else
	SUDO :=''
endif

# different OS's have different conventions
UNAME := $(shell uname)

OWNER := tomc

ifeq ($(UNAME), Linux)
	DIST := $(shell grep "^ID=" /etc/os-release |cut -f2 -d '=' | tr -d '"')
	ifeq ($(DIST), centos)
		SERVICE := /usr/lib/systemd/system
		NETUSR := nginx
		
	else ifeq ($(DIST), ubuntu)
		SERVICE :=  /etc/systemd/system
		NETUSR := www-data
	else ifeq ($(DIST), linuxmint)
		SERVICE := /etc/systemd
		NETUSR := www-data
	#else ifeq ($(DIST), ???)
	#	SERVICE := /x/y/z
	endif
endif

# expecting to be under /srv/
PWD := $(shell pwd)

APP := prefixping
########################################################################

all : start
#	@echo $(UNAME)
#	@echo $(DIST)
#	@echo $(SERVICE)

socket :
	#### add uwsgi user to nginx group
	# usermod -a -G nginx uwsgi
	#### make group for directory /run/prefixping be nginx
	$(SUDO) mkdir /run/$(APP)
	$(SUDO) chown $(OWNER):$(NETUSR) /run/$(APP)
	### sticky too? 
	$(SUDO) chmod g+s /run/$(APP)

# Distros may be converging on systemcrtl
# but not on where the bits should live
service: $(SERVICE)/$(APP).service
	# 

enabled: /etc/nginx/sites-enabled/$(APP)
	# 

$(SERVICE)/$(APP).service : $(PWD)/$(APP).service
	$(SUDO) unlink $(SERVICE)/$(APP).service
	$(SUDO) ln -s $(PWD)/$(APP).service $(SERVICE)$(APP).service

/etc/nginx/sites-available : /etc/nginx/
	$(SUDO) mkdir /etc/nginx/sites-available
	$(SUDO) grep "include /etc/nginx/sites-enabled/\\*;" /etc/nginx/nginx.conf

/etc/nginx/sites-available/$(APP) :  /etc/nginx/sites-available $(APP).nx_location
	$(SUDO) unlink /etc/nginx/sites-available/$(APP)
	$(SUDO) cp $(APP).nx_location /etc/nginx/sites-available/$(APP)

/etc/nginx/sites-enabled : /etc/nginx/sites-available
	$(SUDO) mkdir /etc/nginx/sites-enabled

/etc/nginx/sites-enabled/$(APP) : /etc/nginx/sites-available/$(APP) 
	$(SUDO) unlink /etc/nginx/sites-enabled/$(APP)
	$(SUDO) ln -s /etc/nginx/sites-available/$(APP) /etc/nginx/sites-enabled/$(APP)


start : socket service enabled
	$(SUDO) systemctl stop  $(APP)
	$(SUDO) systemctl start  $(APP)
#	$(SUDO) systemctl enable $(APP)

clean : PHONY
