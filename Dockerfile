FROM clusterlab/linuxbase:1
ENV PYTHONUNBUFFERED 1
RUN mkdir /webapps
WORKDIR /webapps
# Installing OS Dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
libsqlite3-dev
RUN pip install -U pip setuptools
RUN pip install --upgrade pip
COPY requirements.txt /webapps/
RUN pip install -r /webapps/requirements.txt
ADD . /webapps/
WORKDIR /webapps/
# CRONTAB
RUN cp -f /webapps/src/cron_* /etc/cron.d
# Django service
EXPOSE 8000
RUN chmod +x run_web.sh
CMD ./run_web.sh