#!/usr/bin/env bash
#cron
/etc/init.d/cron start
cd /webapps/
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
