#!/bin/bash

export FLASK_ENV=production
# /usr/bin/screen -L -AdmS UpdateDev python3 /home/runner/UpdateHook/UpdateDev.py
gunicorn -c gunicorn.cfg.py UpdateDev:app
