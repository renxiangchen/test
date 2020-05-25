#!/bin/sh -l 
cd /goaccess-1.3
cd /xcalagent/tools
ls -al
python3 xcal-scanner.py -d -sc ../workdir/run.conf -pc xcal-project.conf -usc 
#python3 /xcalagent/tools/xcal-scanner.py -d -sc /xcalagent/workdir/run.conf -pc /xcalagent/tools/xcal-project.conf -usc 

time=$(date)
echo "::set-output name=time::$time"
