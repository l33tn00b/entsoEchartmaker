
FROM debian:stable-slim

# set timezone
ENV TZ="Europe/Berlin"
#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN date

# unattended upgrades
# we'd rather break the container 
# than having security issues
RUN apt update
RUN apt install unattended-upgrades -y

# stuff required for chart generation
RUN apt install python3 python3-pip -y
RUN python3 -m pip install pyyaml
RUN python3 -m pip install entsoe-py
RUN python3 -m pip install -U matplotlib
RUN apt install -y supervisor
RUN apt-get -y install locales locales-all
ENV LC_ALL de_DE.UTF-8
ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE.UTF-8
RUN apt install -y procps

RUN mkdir -p /var/log/supervisor

# add script user
RUN groupadd chartuser
RUN useradd --gid chartuser --create-home --shell /bin/bash chartuser

# add scraper script
USER chartuser
ADD --chown=chartuser:chartuser scripts /home/chartuser/scripts
RUN chmod a+x /home/chartuser/scripts/run_script.sh 
ADD nano_cust/.nanorc /home/chartuser



USER root
# work comfortably
RUN apt install nano -y
ADD nano_cust/.nanorc /root
RUN apt install mc -y

# install web server
# with config
RUN apt install nginx -y
ADD nginx_config/default-ssl /var/tmp
RUN mkdir -p /var/www/site
RUN chown -R chartuser:chartuser /var/www/site
RUN chmod 755 /var/www/site

# install cron for updating chart
RUN apt-get install cron -y
# add system-wide crontab for
# periodic scrape (seluser)
# unattended upgrades (root)
ADD crontab/crontab /etc/crontab
# we'll restart later, but why not
RUN service cron start


# start supervisord
# config for services
ADD conf_scripts /etc/supervisor/conf.d
# do startup of services
ADD startup_scripts /opt/bin
RUN chmod a+x /opt/bin/cronrestart.sh
RUN chmod a+x /opt/bin/gen-keys.sh
RUN chmod a+x /opt/bin/start-chart.sh
# add nodaemon config option
COPY supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
# start with config file given
CMD [ "/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf" ]
