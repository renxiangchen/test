#!/bin/sh -l 
cd /xcalagent/tools

ls -al
eval `python3 xcal-scanner.py -d -sc ../workdir/run.conf -pc xcal-project.conf --build-path /goaccess-1.3 --project-path /goaccess-1.3 -usc`
#python3 /xcalagent/tools/xcal-scanner.py -d -sc /xcalagent/workdir/run.conf -pc /xcalagent/tools/xcal-project.conf -usc 
#time=$(date)

time=`echo $total_issues`
echo "::set-output name=time::$time"
