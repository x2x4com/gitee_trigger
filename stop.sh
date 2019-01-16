#!/bin/bash

[ ! -f '/tmp/UpdateDev.pid.log' ] && echo "/tmp/UpdateDev.pid.log not find" && exit 1
pid=$(cat /tmp/UpdateDev.pid.log)
kill -TERM $pid
