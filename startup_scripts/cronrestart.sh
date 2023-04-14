#!/usr/bin/env bash

echo "Current Timezone is:"
echo $TZ
echo $TZ > /var/tmp/TZ
#echo "Current Display is:"
#echo $DISPLAY
#echo $DISPLAY > /var/tmp/DISPLAY
#echo "Current Zip Code is:"
#echo $PLZ
#echo $PLZ > /var/tmp/PLZ

#echo "Modifying system-wide crontab in /etc/crontab accordingly..."
sed -i "/SHELL=\/bin\/sh/aTZ=$(cat /var/tmp/TZ)" /etc/crontab

echo "Starting cron restart script..."
#sudo service cron restart
service cron restart

