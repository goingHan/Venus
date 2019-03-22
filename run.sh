#!/usr/bin/bash 
#run Venus
# add by hananmin 20190223

if [ -e "count" ];then
  countNums=$(cat count)
else
  countNums=0
fi

riqi=$(date +'%Y%-m-%d %H:%M:%S')
threadNums=$(ps -ef |grep main.py|wc -l)
if [ $threadNums -gt 1 ];then
    echo -e "$riqi" "\033[31m[PASS Already RUNNING]\033[0m"  '!!!!!!!!!!!!!!!!' 
    ps -ef |grep main.py|grep -v grep |tail -2
    if [ $countNums -gt 12 ];then
       echo -e "$riqi" "\033[31m[ beyond 12 KILLING ]\033[0m"  '!!!!!!!!!!!!!!!!' 
       ps -ef |grep main.py|awk '{print $2}'|xargs kill -15
    else
      countNums=$(expr $countNums + 1)
      echo $countNums > count
    fi
else
    echo -e "$riqi"  "\033[32m[Begin Run Venus]\033[0m" 
    cd /app/Venus/bin;python main.py run  /NSFTP/log/
    echo 0 > count
fi
