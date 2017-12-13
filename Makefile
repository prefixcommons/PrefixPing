# prefix ping deploy

# web client <-> nginx <->  socket <-> uwsgi <-> flask-script
#
# (http)        (service)             (service? (  service  ))


# if not root, then just print steps
ifneq ($(shell whoami), root)
	# -n, --just-print, --dry-run, --recon
	MAKEFLAGS += n
endif

# different OS's have different conventions
UNAME := $(shell uname)

ifeq ($(UNAME), Linux)
	DIST := $(shell grep "^ID=" /etc/os-release |cut -f2 -d '=' | tr -d '"')
	ifeq ($(DIST), centos)
		SERVICE := /usr/lib/systemd/system
	else ifeq ($(DIST), ubuntu)
		SERVICE := /etc/system
	else ifeq ($(DIST), linuxmint)
		SERVICE := /etc/system
	#else ifeq ($(DIST), ???)
	#	SERVICE := /x/y/z
	endif
endif

# expecting to be under /srv/
PWD := $(shell pwd)

########################################################################

all : $(SERVICE)/prefixping.service /etc/nginx/sites-enabled/prefixping \
    /etc/nginx/sites-available/prefixping
	
	@echo $(UNAME)
	@echo $(DIST)
	@echo $(SERVICE)

# Distros may be converging on systemcrtl
# but not on where the bits should live
$(SERVICE)/prefixping.service : $(PWD)/prefixping.service
	unlink $(SERVICE)/prefixping.service
	ln -s $(PWD)/prefixping.service $(SERVICE)/prefixping.service

# are init scripts even needed with <service> files in place?
#/etc/init/prefixping.conf : ./prefixping.conf
#	unlink /etc/init/prefixping.conf
#	ln -s  $(PWD)/prefixping.conf /etc/init/prefixping.conf

/etc/nginx/sites-available : /etc/nginx/
	mkdir /etc/nginx/sites-available
	grep "include /etc/nginx/sites-enabled/\\*;" /etc/nginx/nginx.conf

/etc/nginx/sites-available/prefixping :  /etc/nginx/sites-available prefixping.nx_location
	unlink /etc/nginx/sites-available/prefixping
	cp prefixping.nx_location /etc/nginx/sites-available/prefixping

/etc/nginx/sites-enabled : /etc/nginx/sites-available
	mkdir /etc/nginx/sites-enabled

/etc/nginx/sites-enabled/prefixping : /etc/nginx/sites-available/prefixping 
	 unlink /etc/nginx/sites-enabled/prefixping
	 ln -s /etc/nginx/sites-available/prefixping /etc/nginx/sites-enabled/prefixping


start :
	 systemctl start prefixping
	 systemctl enable prefixping

clean : PHONY
