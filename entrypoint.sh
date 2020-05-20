#!/bin/sh -l 

cd /
mkdir test
ls
echo "Hello $1"
time=$(date)
echo "::set-output name=time::$time"
