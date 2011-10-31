#!/bin/sh
pgrep Xvfb > /dev/null || nohup Xvfb :1 -screen 0, 1440x6000x24 >/dev/null 2>/dev/null &
export DISPLAY=':1'
