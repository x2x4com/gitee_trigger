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
import subprocess
import shlex
import datetime
import time
import lib.MyLog as log
from cfg import jenkins, token_list, dd_9chain_tech_robot


app = Flask(__name__)


listen = '0.0.0.0'
port = 10080
processes = 4
debug = True


# 输出规范
stand = OrderedDict()
stand['ret'] = 200
stand['data'] = None
stand['msg'] = None

# 日志输出
log.set_logger(filename="/tmp/UpdateHook.log", level='INFO', console=False)

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


class ShellExeTimeout(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def exec_shell(cmd, cwd=None, timeout=None, shell=False):
    """
        封装一个执行shell的方法
        封装了subprocess的Popen方法，支持超时判断，支持读取stdout和stderr
        参数：
            cwd: 运行路径，如果被设定，子进程会切换到cwd
            timeout: 超时时间， 秒， 支持小数，精度0.1秒
            shell: 是否通过shell运行
        返回： [return_code(int),'stdout(file handle)','stderr(file handle)']
        Raises: ShellExeTimeout: 执行超时
        在外部捕捉此错误
        注意：如果命令带有管道，必须用shell=True

    :param cmd:  string, 执行的命令
    :param cwd:  string, 运行路径，如果被设定，子进程会切换到cwd
    :param timeout:  float, 超时时间， 秒， 支持小数，精度0.1秒
    :param shell:  bool, 是否通过shell运行
    :return:  list, [return_code(int),'stdout(file handle)','stderr(file handle)']
    :raise ShellExeTimeout: 运行超时
    """
    try:
        if shell:
            cmd_list = cmd
        else:
            cmd_list = shlex.split(cmd)
        if timeout:
            end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        sub = subprocess.Popen(cmd_list, cwd=cwd, stdin=subprocess.PIPE, shell=shell, bufsize=4096,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while sub.poll() is None:
            time.sleep(0.1)
            if timeout:
                if end_time < datetime.datetime.now():
                    raise ShellExeTimeout("Shell Run Timeout(%s sec): %s" % (timeout,cmd))
        return [int(sub.returncode),sub.stdout,sub.stderr]
    except OSError as e:
        return [1,[],[e]]


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
    #
    if request.method == 'POST':
        content = request.get_json(force=True)

        token = request.args.get('token')
        if token not in token_list:
            return [400, "", "Access deny, token failed"]
        print(content)
        namespace = content['project']['namespace']
        name = content['project']['name']
        url = [content['project']['git_ssh_url'], content['project']['git_http_url']]
        password = content['password']
        return run(namespace, name, url, password)
    return "hello"


@app.route("/oschina/update", methods=['GET', 'POST'])
def update_form():
    return "form"


def run(namespace, name, url, password):
    """
    run 开始执行操作

    :param namespace: string, 项目的命名空间
    :param name: string, 项目名称
    :param url: dict, ssh和http的repo url
    :param password: string, 更新秘钥
    :return: list, [ code, data, msg ]
    """
    # try to get config

    return [200, 'run', ""]


def is_existed(repo):
    return path.exists(repo + '/.git/config')


def get_local_repo_url(repo, branch):
    config = ConfigParser()
    config.read(repo + '/.git/config')
    try:
        remote = config['branch "'+branch+'"']['remote']
        url = config['remote "'+remote+'"']['url']
    except KeyError as e:
        url = "Git config parser error, %s" % e
    return url



def check_git_dir(target):
    pass


if __name__ == '__main__':
    app.run(host=listen, port=port, debug=debug)
