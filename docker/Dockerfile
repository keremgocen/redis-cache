FROM python:3.6
LABEL maintainer="Kerem Gocen <keremgocen@gmail.com>"

WORKDIR /opt/app/src

ADD . .

# Add and install Python modules
RUN pip install -r requirements.txt

EXPOSE 8005
