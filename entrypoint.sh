#!/bin/sh -l 

cd /
mkdir xc 
cd xc
echo Hello $1"
time=$(date)
echo "::set-output name=time::$time"
