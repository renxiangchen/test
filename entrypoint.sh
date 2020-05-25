#!/bin/sh -l 

cd /xcalagent/tools
ls -al
ping mac.xcalibyte.com -c 1
#python3 /xcalagent/tools/xcal-scanner.py -d -sc /xcalagent/workdir/run.conf -pc /xcalagent/tools/xcal-project.conf -usc -np

time=$(date)
echo "::set-output name=time::$time"
