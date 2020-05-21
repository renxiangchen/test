#!/bin/sh -l 

cd /
mkdir xc 
cd xc
WORKDIR /xc
ADD PoC1-0-10-c.tar . 
ls
echo "aafdaae:wq"
echo "Hello $1"
time=$(date)
echo "::set-output name=time::$time"
