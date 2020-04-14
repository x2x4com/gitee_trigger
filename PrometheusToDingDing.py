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
from lib.tools import is_internal_ip
import json

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
    if not is_internal_ip(request.remote_addr):
        return abort(403, 'Not allow')
    return Response('dingding_alert_total %s\ndingding_alert_success_total %s\ndingding_alert_fail_total %s' % (3, 4, 5))


# for alert manager
@app.route("/alert", methods=['POST'])
def alert():
    token = request.args.get('token')
    if not is_internal_ip(request.remote_addr) or token not in token_list:
        return abort(403, 'Not allow')
    data = request.json
    # print(data)
    ret = dingding_robot.send_text(json.dumps(data), msg_from='prometheus')
    return Response(ret, content_type='application/json')


if __name__ == '__main__':
    from os import environ
    debug = True if environ.get('APP_DEBUG') in ['True', 'true'] else False
    app.run(host=listen, port=port, debug=debug, threaded=True)
