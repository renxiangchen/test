#!/bin/sh -l 

cd /
mkdir test
ls
echo "aafdaae:wq"
echo "Hello $1"
time=$(date)
echo "::set-output name=time::$time"
