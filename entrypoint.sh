#!/bin/sh -l 
cd /xcalagent/tools
export DEFECT_RESULT=12
ls -al
python3 xcal-scanner.py -d -sc ../workdir/run.conf -pc xcal-project.conf --build-path /goaccess-1.3 --project-path /goaccess-1.3 -usc
#python3 /xcalagent/tools/xcal-scanner.py -d -sc /xcalagent/workdir/run.conf -pc /xcalagent/tools/xcal-project.conf -usc 
echo $DEFECT_RESULT

time=$(date)
echo "::set-output name=time::$time"
