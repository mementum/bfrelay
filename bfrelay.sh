#! /bin/sh

while true; do

  PATH=/tmp/python/bin:$PATH ./bfrelay.py &> /dev/null
  ./bfrelay.py &> /dev/null
  sleep 3

done &
