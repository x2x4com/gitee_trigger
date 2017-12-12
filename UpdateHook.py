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
from os import path
from functools import wraps
import json
from flask import Response
from collections import OrderedDict
from configparser import ConfigParser


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
        "UpdateHook": {
            "password": "",
            "local_dir": "/home/runner/UpdateHook",
            "branch": "master",
        },
    },
}

# 输出规范

stand = OrderedDict()
stand['ret'] = 200
stand['data'] = None
stand['msg'] = None


def json_output():
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if type(result) == list:
                try:
                    stand['ret'] = int(result[0])
                except IndexError:
                    stand['ret'] = 500
                    stand['data'] = None
                    stand['msg'] = "return String error"
                    return json.dumps(stand)
                try:
                    stand['data'] = result[1]
                except IndexError:
                    pass
                try:
                    stand['msg'] = result[2]
                except IndexError:
                    pass
            else:
                stand['data'] = result
            result = json.dumps(stand)
            return Response(result, mimetype='application/json')
        return wrapper
    return decorate


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
    # password = request.args.get('token')
    if request.method == 'POST':
        content = request.get_json(force=True)
        password = content['password']
        if password not in password_dict:
            return [400, "", "Access Deny"]
        namespace = content['project']['namespace']
        name = content['project']['name']
        url = [content['project']['git_ssh_url'], content['project']['git_http_url']]
        return run(namespace, name, url)
    return "hello"


@app.route("/oschina/update", methods=['GET', 'POST'])
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
        repo_url = url
    except KeyError as e:
        return [400, "", "config key error, %s" % e]
    try:
        branch = repos[namespace][name]['branch']
    except KeyError:
        branch = "master"
    if not is_existed(repo_root):
        return [400, "", "local repo not existed"]
    local_config_repo_url = get_local_repo_url(repo_root, branch)
    if local_config_repo_url not in url:
        return [400, "", "%s not in %s" % (local_config_repo_url, url)]
    return [200, "data", "msg"]


def is_existed(repo):
    return path.exists(repo + '/.git/config')


def get_local_repo_url(repo, branch):
    config = ConfigParser()
    config.read(repo + '/.git/config')
    try:
        remote = config['branch "'+branch+'"']['remote']
        url = config['remote "'+remote+'"']['url'] + "1111"
    except KeyError as e:
        url = "Git config parser error, %s" % e
    return url



def check_git_dir(target):
    pass


if __name__ == '__main__':
    app.run(host=listen, port=port, processes=processes, debug=debug)
