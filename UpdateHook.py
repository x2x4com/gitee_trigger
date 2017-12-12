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
from JsonFormat import json_output
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

# namespace: { "name": { xxxx } }
repos = {
    "ninechain": {
        "name": {
            "ssh_url": "git@gitee.com:ninechain/UpdateHook.git",
            "http_url": None,
            "local_dir": "/home/runner/UpdateHook",
            "branch": "master",
        },
    },
}


@app.route("/")
@json_output()
def index():
    """
    default router

    :return:
    """
    return "/ => index"


@app.route("/oschina/update.json", methods=['GET', 'POST'])
@json_output()
def update_json():
    """
    post data with json format

    :return:
    """
    #password = request.args.get('auth')
    if request.method == 'POST':
        content = request.get_json(force=True)
        password = content['password']
        if password not in password_dict:
            return [400, "", "Access Deny"]
        namespace = content['project']['namespace']
        name = content['project']['name']
        url = {"ssh": content['project']['git_ssh_url'], "http": content['project']['git_http_url']}
        return run(namespace, name, url)
    return "hello"


@app.route("/oschina/update", methods=['GET','POST'])
def update_form():
    return "form"


def run(namespace, name, url):
    """
    run 开始执行操作

    :param namespace: string, 项目的命名空间
    :param name: string, 项目名称
    :param url: dict, ssh和http的repo url
    :return: list, [ code, data, msg ]
    """
    # try to get config
    try:
        repo_root = repos[namespace][name]['local_dir']
    except KeyError as e:
        return [400, "", "config key error, %s" % e]

    return [200, "data", "msg"]



def is_match_repo_url(url, ssh_url, http_url):
    pass

def check_git_dir(target):
    pass


if __name__ == '__main__':
    app.run(host=listen, port=port, processes=processes, debug=debug)