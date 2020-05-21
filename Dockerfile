#python container
FROM python:3.8

COPY entrypoint.sh /entrypoint.sh

RUN cd /
RUN mkdir xc

WORDKIR /xc

ADD PoC1-0-10-c.tar .

RUN ls

ENTRYPOINT ["/entrypoint.sh"]


