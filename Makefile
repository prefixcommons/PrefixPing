# prefix ping deploy

all : 



/ect/service/prefixping.service : ./prefixping.service
	sudo unlink /ect/service/prefixping.service
	sudo ln -s sudo ln -s ./prefixping.service /ect/service/prefixping.service

/etc/init/prefixping.conf : ./prefixping.conf
	sudo unlink /etc/init/prefixping.conf
	sudo ln -s  ./prefixping.conf /etc/init/prefixping.conf


/etc/nginx/sites-enabled: /etc/nginx/sites-available
	sudo mkdir /etc/nginx/sites-enabled

/etc/nginx/sites-available: /etc/nginx/
	sudo mkdir /etc/nginx/sites-available
	grep "include /etc/nginx/sites-enabled/*;" /etc/nginx/nginx.conf


/etc/nginx/sites-available/prefixping :  /etc/nginx/sites-available prefixping.nx_sites
	sudo unlink /etc/nginx/sites-available/prefixping
	sudo ln -s ./prefixping.nx_sites /etc/nginx/sites-available/prefixping


/etc/nginx/sites-enabled/prefixping : /etc/nginx/sites-available/prefixping 
	sudo unlink /etc/nginx/sites-enabled/prefixping
	sudo ln -s /etc/nginx/sites-available/prefixping /etc/nginx/sites-enabled/prefixping


/etc/nginx/nginx.conf : ./prefixping.nx_conf
	echo "update /etc/nginx/nginx.conf  with ./prefixping.nx_conf "

start :
	sudo systemctl start prefixping
	sudo systemctl enable prefixping


clean : PHONY
	sudo unlink /etc/init/prefixping.conf /ect/service/prefixping.service
