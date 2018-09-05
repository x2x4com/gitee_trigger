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
import requests
from cfg import jenkins, token_list, dd_9chain_tech_robot, git_user, global_password
import re
from functools import reduce

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
            return Response(result, mimetype='application/json', status=stand['ret'])
        return wrapper
    return decorate


class ShellExeTimeout(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class DictToObj(object):
    def __init__(self, _dict:dict):
        self.__dict__.update(_dict)


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


def ip_into_int(ip):
    # 先把 192.168.1.13 变成16进制的 c0.a8.01.0d ，再去了“.”后转成10进制的 3232235789 即可。
    # (((((192 * 256) + 168) * 256) + 1) * 256) + 13
    return reduce(lambda x,y:(x<<8)+y,map(int,ip.split('.')))

def is_internal_ip(ip):
    ip = ip_into_int(ip)
    net_a = ip_into_int('10.255.255.255') >> 24
    net_b = ip_into_int('172.31.255.255') >> 20
    net_c = ip_into_int('192.168.255.255') >> 16
    return ip >> 24 == net_a or ip >>20 == net_b or ip >> 16 == net_c


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
            return [403, "", "Access deny, token failed"]
        return run(content)
    return "hello"


@app.route('/jenkins/callback', methods=['GET'])
@json_output()
def jenkins_callback():
    # only allow from jenkins server
    token = request.args.get('token')
    if not is_internal_ip(request.remote_addr) or token not in token_list:
        return [403, '', 'Not allow']
    commit_hash = request.args.get('commit_hash')
    is_deploy = request.args.get('is_deploy')
    job_name = request.args.get('job_name')
    build_tag = request.args.get('build_tag')
    print(is_deploy, commit_hash, job_name, build_tag)
    msg = "{job_name}:{commit_hash} 已经构建完成, 构建TAG: {build_tag}\n镜像地址: 192.168.1.234:5000/{job_name}:{commit_hash}".format(job_name=job_name, commit_hash=commit_hash, build_tag=build_tag)
    if is_deploy == 'true':
        msg = msg + "\n开始部署测试环境"
    notify_dingding(msg)
    return "done"


def notify_dingding(msg, at_mobiles:list=None):
    data = {
        "msgtype": "text",
        "text": {
            "content": str(msg)
        },

    }
    if at_mobiles is not None and type(at_mobiles) == list:
        if len(at_mobiles) > 0:
            data['at'] = dict()
            data['at']['atMobiles'] = at_mobiles
            data['at']['isAtAll'] = False
    ret = requests.post(dd_9chain_tech_robot, json=data)
    if ret.status_code == requests.codes.ok:
        print('%s 发送成功' % msg)
    else:
        print('%s 发送失败' % msg)
    print(ret.text)


def run(content):
    """
    run 开始执行操作

    :param content: string, 回调结构
    :return: list, [ code, data, msg ]
    """
    # try to get config
    namespace = content['project']['namespace']
    name = content['project']['name']
    hook_name = content['hook_name']
    try:
        project = jenkins['repos'][namespace][name]
    except Exception:
        print('target not find')
        return [400, '', 'target not find, %s/%s' %(namespace, name)]
    if project['password'] not in global_password:
        print('authorization failure')
        return [403, '', 'authorization failure']
    if hook_name not in ['push_hooks']:
        print('hook %s, not support' % hook_name)
        return [400, '', 'hook %s, not support' % hook_name]
    # ref 必须为 配置文件中指定的，否则跳出
    ref = content['ref'].split('/')[-1]
    if ref not in project['branch']:
        print('branch %s, not support' % ref)
        return [400, '', 'branch %s, not support' % ref]
    # 开始正式干活儿, 搜索commit 信息
    head_commit = content['head_commit']
    message = head_commit['message']
    # 找所有at的对象
    print('Search for at')
    re_at = re.compile(r'@[^@\s]+')
    want_at_users = re_at.findall(message)
    # print(want_at_users)
    existed_at_users = list()
    # 看看@的对象有没有对应dingding手机号码
    for want_at_user in want_at_users:
        want_at_user = want_at_user.lstrip('@')
        if str(want_at_user) in git_user.keys():
            existed_at_users.append(str(want_at_user))
    print('at users: %s' % existed_at_users)
    # 找所有的 CMD
    is_deploy = False
    is_build = False
    print('Search for cmd')
    re_cmd = re.compile(r'#CMD:(build(?:\+deploy)?)')
    cmds = re_cmd.findall(message)
    for cmd in cmds:
        if cmd == 'build+deploy':
            is_build = True
            is_deploy = True
        if cmd == 'build':
            is_build = True
    print('isBuild: %s' % is_build)
    print('isDeploy: %s' % is_deploy)

    pusher = content['pusher']
    git_hash = content['after']
    gitee_user = content['user_name']

    jenkins_hosts = jenkins['host']
    jenkins_user = jenkins['user']
    jenkins_secret = jenkins['secret']

    msg = '%s在分支%s上提交了代码%s\n提交信息%s\n' % (gitee_user, ref, git_hash, message)
    existed_at_user_mobiles = list()
    for existed_at_user in existed_at_users:
        existed_at_user_mobile = '@' + str(git_user[existed_at_user])
        msg.replace(existed_at_user, existed_at_user_mobile)
        existed_at_user_mobiles.append(existed_at_user_mobile)

    if is_build:
        msg = '收到了构建请求!!\n' + msg + '开始向Jenkins提交构建请求\n'
        print('msg: %s' % msg)
        notify_dingding(msg, existed_at_user_mobiles)
        cause_msg = '%s+build' % git_hash
        if is_deploy:
            cause_msg = cause_msg + '_deploy'
            request_url = '%s%s/buildWithParameters?token=%s&is_deploy=true&cause=%s' % (jenkins_hosts,
                                                                project['jenkins_url'],
                                                                project['jenkins_token'],
                                                                cause_msg)
        else:
            request_url = '%s%s/buildWithParameters?token=%s&is_deploy=false&cause=%s' % (jenkins_hosts,
                                                        project['jenkins_url'],
                                                        project['jenkins_token'],
                                                        cause_msg)

        print(request_url)
        ret = requests.get(request_url, auth=(jenkins_user, jenkins_secret))
        print(ret.status_code)
        if ret.status_code == 201:
            location = ret.headers['location']
            print('location: %s' % location )
            print('get task info')
            task = requests.get(location + 'api/json', auth=(jenkins_user, jenkins_secret))
            print(task.json())
        else:
            print('requests not ok')
            print(ret.text)
    elif len(existed_at_users) > 0:
        print('不构建，就通知一下')
        notify_dingding(msg, existed_at_user_mobiles)
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
