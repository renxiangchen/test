From ubuntu:16.04

ENV AGENT_WORKDIR=/xcalagent

WORKDIR $AGENT_WORKDIR

RUN apt-get update && \
    apt-get install -y build-essential gcc-multilib autoconf libtool-bin maven curl clang gcc-arm-none-eabi git  cmake openjdk-8-jdk make python3.5 libstdc++6 python3-pip libreadline-dev libncurses5-dev rcs gawk libssl-dev  libgit2-dev && \
    pip3 install --upgrade pip && \
    pip3 install requests jaeger-client && \
    pip3 install lxml && \
    apt-get autoclean && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install 'pygit2<=1.0.0,<1.1.0' 
#ADD PoC1-0-10-c.tar .

RUN cd /

ADD xcalagent.tar /

RUN cd /xcalagent
RUN ls -al
RUN ./setup.sh

RUN cd /xcalagent
RUN mkdir tools

COPY xcal-scanner.py /xcalagent/tools/xcal-scanner.py

RUN cd /
COPY run.conf /xcalagent/workdir/run.conf

RUN cd /
RUN mkdir testApp

ADD goaccess-1.3.tar /testApp



RUN ping mac.xcalibyte.com


