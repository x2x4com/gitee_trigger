#!/usr/bin/env python
# encoding: utf-8
# ===============================================================================
#
#         FILE:
#
#        USAGE:
#
#  DESCRIPTION:
#
#      OPTIONS:  ---
# REQUIREMENTS:  ---
#         BUGS:  ---
#        NOTES:  ---
#       AUTHOR:  YOUR NAME (),
#      COMPANY:
#      VERSION:  1.0
#      CREATED:
#     REVISION:  ---
# ===============================================================================

from flask import Flask, request, Response, abort
import lib.MyLog as Log
from lib.Dingding import DRobot
from flask_cors import CORS
from cfg import token_list, dingding_db, dingding_secret, dingding_token

listen = '0.0.0.0'
port = 10080

app = Flask(__name__)

CORS(app)

Log.set_logger(filename="/tmp/PrometheusAlertToDingDing.log", level='INFO', console=True)

dingding_robot = DRobot(
    robot_url='https://oapi.dingtalk.com/robot/send',
    is_sign=True,
    token=dingding_token,
    secret=dingding_secret,
    db_file=dingding_db
)


@app.route("/")
def root():
    return abort(404, 'Nothing')


# for Prometheus metrics
@app.route("/metrics")
def metrics():
    return Response('dingding_alert_total %s' % 3)


