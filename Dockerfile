#python container
FROM python:3.8

COPY entrypoint.sh /entrypoint.sh

RUN cd /
RUN mkdir xc

WORKDIR /xc

ADD PoC1-0-10-c.tar .

RUN mkdir tools

COPY xcal-scanner.py /xc/tools/xcal-scanner.py

RUN cd /xc/tools

RUN python3  xcal-scanner.py

RUN ls

ENTRYPOINT ["/entrypoint.sh"]


