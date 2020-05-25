#!/bin/sh -l 

cd /xcalagent/tools
ls -al
ping www.baidu.com -c 1
python3 xcal-scanner.py -d -sc ../workdir/run.conf -pc xcal-project.conf -usc -np
#python3 /xcalagent/tools/xcal-scanner.py -d -sc /xcalagent/workdir/run.conf -pc /xcalagent/tools/xcal-project.conf -usc -np
time=$(date)
echo "::set-output name=time::$time"
