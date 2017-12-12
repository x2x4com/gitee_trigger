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

from flask import Flask, request
from JsonFormat import output
import json

app = Flask(__name__)

listen = '0.0.0.0'
port = 10080
processes = 4
debug = True

password_dict = [
    'Ck-_DevzEAB6Yiy2',
    'x2x4x2x4x2x4'
]

git_config = {
    "name": "",
    "root": ""
}


@app.route("/")
@output(format="json")
def index():
    """
    default router

    :return:
    """
    return "/ => index"


@app.route("/oschina/update.json", methods=['GET', 'POST'])
@output(format="json")
def update_json():
    """
    post data with json format

    :return:
    """
    password = request.args.get('auth')
    if request.method == 'POST':
        content = request.get_json(force=True)
        print(json.dumps(content))
        return [200, content, "demo"]
    return "hello"


@app.route("/oschina/update", methods=['GET','POST'])
def update_form():
    return "form"


def do():
    """

    :return:
    """
    pass


def check_git_dir(target):
    pass


if __name__ == '__main__':
    app.run(host=listen, port=port, processes=processes, debug=debug)