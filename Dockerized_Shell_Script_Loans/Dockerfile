FROM ubuntu:23.10
RUN apt-get update && apt-get -y install unzip wget
COPY count.sh /var/run/count.sh
CMD ["/var/run/count.sh"]
