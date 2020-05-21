From ubuntu:16.04

ENV AGENT_WORKDIR=/xc

WORKDIR $AGENT_WORKDIR

RUN apt-get update && \
    apt-get install -y build-essential gcc-multilib autoconf libtool-bin curl clang gcc-arm-none-eabi git cmake openjdk-8-jdk make python3.5 libstdc++6 python3-pip libreadline-dev libncurses5-dev rcs gawk libssl-dev && \
    pip3 install --upgrade pip && \
    pip3 install requests jaeger-client && \
    apt-get install libgit2-dev
    install 'pygit2<=1.0.0,<1.1.0'
    apt-get autoclean && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ADD PoC1-0-10-c.tar .
RUN cd /xc
RUN ls
RUN setup.sh

