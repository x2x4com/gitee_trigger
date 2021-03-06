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
import lib.MyLog as log
import requests
from cfg import jenkins, token_list, dd_9chain_tech_robot, git_user, global_password, DEBUG, gitee_token, gitee_issue_api_url, default_isssue_assignee
import re
from functools import reduce
from lib.Dingding import DRobot
from lib.DB import Storage
from base64 import b64encode, b64decode
import subprocess
import shlex
import datetime
import time
import yaml
from io import open as ioOpen


app = Flask(__name__)


listen = '0.0.0.0'
port = 10080
processes = 4
debug = DEBUG


# 输出规范
std_out = OrderedDict()
std_out['ret'] = 200
std_out['data'] = None
std_out['msg'] = None

# 日志输出
log.set_logger(filename="/tmp/UpdateDev.log", level='INFO', console=True)

# 钉钉机器人
dingding_robot = DRobot(dd_9chain_tech_robot)

# DB文件
db_file = "/data/update_dev.db"


def json_output():
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            stand = std_out.copy()
            if type(result) == list or type(result) == tuple:
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
    :return: return_code(int), stdout(string), stderr(string)
    :raise RuntimeError: 运行超时
    """
    if timeout:
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    else:
        # 防止卡死，强制设定一个超时，10分钟
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=10*60)
    try:
        if shell:
            cmd_list = cmd
        else:
            cmd_list = shlex.split(cmd)
        sub = subprocess.Popen(cmd_list, cwd=cwd, stdin=subprocess.PIPE, shell=shell, bufsize=4096,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while sub.poll() is None:
            time.sleep(0.1)
            if end_time < datetime.datetime.now():
                raise RuntimeError("Shell Run Timeout(%s sec): %s" % (timeout,cmd))
        stdout = sub.stdout.read()
        stderr = sub.stderr.read()
        if type(stdout) == bytes: stdout = stdout.decode()
        if type(stderr) == bytes: stderr = stderr.decode()
        return int(sub.returncode), stdout, stderr
    except OSError as e:
        return 1, "", str(e)


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
        content = request.get_json(force=True, silent=True, cache=False)

        # token = request.args.get('token')
        # if token not in token_list:
        #     return [403, "", "Access deny, token failed"]
        if not content:
            return [400, "", "Illegal parameter"]
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
    project_id = request.args.get("project_id")
    # log.info(is_deploy, commit_hash, job_name, build_tag)
    msg = "{job_name}:{commit_hash} 已经构建完成, 构建TAG: {build_tag}\n镜像地址: 192.168.1.234:5000/{job_name}:{commit_hash}".format(job_name=job_name, commit_hash=commit_hash, build_tag=build_tag)
    log.info(msg)
    if is_deploy == 'true':
        msg = msg + "\n开始部署测试环境"
    dbs = Storage(db_file)
    # dbs.set(commit_hash=commit_hash, val=msg, project_id=project_id, is_success=True)
    return dingding_robot.send_text(msg=msg)


@app.route("/deploy/callback", methods=['POST', 'GET'])
@json_output()
def deploy_callback():
    if not is_internal_ip(request.remote_addr):
        return [403, '', 'Not allow']
    dbs = Storage(db_file)
    if request.method == 'GET':
        token = request.args.get('token')
        if token not in token_list:
            return [403, '', 'Not allow, Token failed']
        commit_hash = request.args.get('commit_hash')
        is_deploy = request.args.get('is_deploy')
        job_name = request.args.get('job_name')
        build_tag = request.args.get('build_tag')
        project_id = request.args.get("project_id")
        # log.info(is_deploy, commit_hash, job_name, build_tag)
        msg = "{job_name}:{commit_hash} 已经构建完成, 构建TAG: {build_tag}\n镜像地址: 192.168.1.234:5000/{job_name}:{commit_hash}".format(
            job_name=job_name, commit_hash=commit_hash, build_tag=build_tag)
        log.info(msg)
        if is_deploy == 'true':
            msg = msg + "\n开始部署测试环境"
        # dbs.set(commit_hash=commit_hash, val=msg, project_id=project_id, is_success=True)
        return dingding_robot.send_text(msg=msg)
    # POST
    content = request.get_json(force=True, silent=True, cache=False)
    token = content['token']
    if token not in token_list:
        return [403, '', 'Not allow, Token failed']
    # todo
    is_deploy = content["is_deploy"]
    project_id = content["project_id"]
    commit_hash = content["commit_hash"]
    build_tag = content["build_tag"]
    details = content["status_details"]
    tasks = list()
    exec_status = {
        "deploy_id": "",
        "deploy_file": "",
        "code": None,
        "stdout": "",
        "stderr": ""
    }
    for detail in details:
        log.info(detail.keys())
        for deploy_id, deploy_yaml in detail.items():
            target_yaml = "/tmp/" + deploy_id + ".yaml"
            with ioOpen(target_yaml, 'w') as outfile:
               yaml.dump_all(deploy_yaml, outfile, default_flow_style=False, allow_unicode=True)
            cmd = "kubectl apply -f %s" % target_yaml
            code, stdout, stderr = exec_shell(cmd)
            ts = exec_status.copy()
            ts["deploy_id"] = deploy_id
            ts["deploy_file"] = target_yaml
            ts["code"] = code
            ts["stdout"] = b64encode(stdout.encode()).decode()
            ts["stderr"] = b64encode(stderr.encode()).decode()
            tasks.append(ts)

    if sum([c["code"] for c in tasks]) == 0:
        # ok all cmd return is 0
        is_success = True
    else:
        is_success = False

    dbs.set(project_id=project_id, commit_hash=commit_hash, val=tasks, build_tag=build_tag, is_success=is_success)
    msg = "## 命令执行情况\n"
    url = "http://" + request.host + "/deploy/details/" + project_id + "/" + commit_hash
    if is_success:
        title = "%s 部署成功" % commit_hash
    else:
        title = "%s 部署失败" % commit_hash
    for task in tasks:
        dmsg = "### {deploy_id} \n- CMD: kubectl -f {yaml} \n- RETURN: {code} \n"
        dmsg = dmsg.format(
            deploy_id=task["deploy_id"],
            yaml=task["deploy_file"],
            code=task["code"],
        )
        msg = msg + dmsg
    return dingding_robot.send_action_card_single(title=title, single_title="点击查看详情", single_url=url, msg=msg)


@app.route("/deploy/details/<project_id>/<commit_hash>", methods=["GET"])
def deploy_details(project_id, commit_hash):
    # todo
    if not is_internal_ip(request.remote_addr):
        return [403, '', 'Not allow']
    dbs = Storage(db_file)
    build_tag, is_success, val = dbs.get(project_id=project_id, commit_hash=commit_hash)
    return "TODO"


def create_gitee_issue(content):
    project = "%s/%s" % (content['project']['namespace'], content['project']['name'])
    git_hash = content['after']
    branch = content['ref'].split('/')[-1]  # ref: refs/heads/alpha
    body = "project: %s\nbranch: %s\ncommit hash: %s\n" % (project, branch, git_hash)
    log.info("Create update issue: %s %s %s" % (project, branch, git_hash))
    url = gitee_issue_api_url
    payload = {
        "access_token": gitee_token,
        "title": "Update %s %s" % (branch.capitalize(), project),
        "body": body,
        "assignee": default_isssue_assignee,
    }
    log.info("url: %s" % url)
    r = requests.post(url, json=payload)
    log.info("code: %s" % r.status_code)
    if r.status_code == 201:
        try:
            rt = r.json()
            number = rt["number"]
        except json.JSONDecodeError:
            err = "decode json error, %s" % r.text
            log.error(err)
            return [500, "", err]
        except KeyError:
            err = "decode json error, number not find"
            log.error(err)
            return [500, "", err]
        log.info("Create issue %s" % number)
        return [200, number, ""]
    err = "server not return 200, %s" % r.text
    log.error(err)
    return [500, "", err]


def run(content):
    """
    run 开始执行操作

    :param content: string, 回调结构
    :return: list, [ code, data, msg ]
    """
    # try to get config
    # log.info(content)
    namespace = content['project']['namespace']
    name = content['project']['name']
    hook_name = content['hook_name']
    log.info("%s/%s pushed" % (namespace, name))
    try:
        project = jenkins['repos'][namespace][name]
    except Exception:
        log.error('target not find, %s/%s' %(namespace, name))
        return [400, '', 'target not find, %s/%s' %(namespace, name)]
    if content['password'] not in global_password:
        log.error('authorization failure')
        return [403, '', 'authorization failure']
    if hook_name not in ['push_hooks']:
        log.error('hook %s, not support' % hook_name)
        return [400, '', 'hook %s, not support' % hook_name]
    # ref 必须为 配置文件中指定的，否则跳出
    ref = content['ref'].split('/')[-1]
    log.info('target %s/%s ,branch %s' % (namespace, name, ref))
    # Create Gitee issue when is alpha or master branch
    if ref in ['alpha', 'master']:
        create_gitee_issue(content)

    if ref not in project['branch']:
        log.error('target %s/%s ,branch %s, not support' % (namespace, name, ref))
        return [400, '', 'branch %s, not support' % ref]
    # 开始正式干活儿, 搜索commit 信息
    head_commit = content['head_commit']
    message = str(head_commit['message'])
    log.info("Commit Message: %s" % message)
    # 找所有at的对象
    log.info('Search for at')
    re_at = re.compile(r'@[^@\s]+')
    want_at_users = re_at.findall(message)
    # print(want_at_users)
    existed_at_users = list()
    # 看看@的对象有没有对应dingding手机号码
    for want_at_user in want_at_users:
        want_at_user = want_at_user.lstrip('@')
        if str(want_at_user) in git_user.keys():
            existed_at_users.append(str(want_at_user))
    log.info('at users: %s' % existed_at_users)
    is_deploy = False
    is_build = False
    # 找所有的 CMD
    # only when not in alpha or master branch
    if ref not in ['alpha', 'master']:
        log.info('Search for cmd')
        #re_cmd = re.compile(r'#CMD:((?:build)?(?:\+deploy)?)')
        re_cmd = re.compile(r'#CMD:(build\+deploy|build|deploy)')
        cmds = re_cmd.findall(message)
        for cmd in cmds:
            if cmd in ['build+deploy', 'deploy']:
                is_build = True
                is_deploy = True
            if cmd == 'build':
                is_build = True

    # check auto_build_branch, auto_deploy_branch config
    if 'auto_build_branch' in project and ref in project['auto_build_branch']:
        is_build = True
    if 'auto_deploy_branch' in project and ref in project['auto_deploy_branch']:
        is_build = True
        is_deploy = True

    log.info('isBuild: %s' % is_build)
    log.info('isDeploy: %s' % is_deploy)

    pusher = content['pusher']
    git_hash = content['after']
    gitee_user = content['user_name']

    jenkins_hosts = jenkins['host']
    jenkins_user = jenkins['user']
    jenkins_secret = jenkins['secret']

    # find jenkins_url and jenkins_token
    try:
        if 'jenkins_url' in project and 'jenkins_token' in project:
            # single Jenkins job config
            jenkins_url = project['jenkins_url']
            jenkins_token = project['jenkins_token']
        elif 'jenkins_jobs' in project:
            # multiple Jenkins jobs config
            jenkins_url = project['jenkins_jobs'][ref]['jenkins_url']
            jenkins_token = project['jenkins_jobs'][ref]['jenkins_token']
        else:
            return [500, '', 'Missing jenkins_url config']
    except KeyError:
        return [500, '', 'Invalid jenkins_url config']

    msg = '%s在分支%s上提交了代码%s\n提交信息: %s\n' % (gitee_user, ref, git_hash, message)
    existed_at_user_mobiles = list()
    for existed_at_user in existed_at_users:
        existed_at_user_mobile = '@' + str(git_user[existed_at_user])
        msg.replace(existed_at_user, existed_at_user_mobile)
        existed_at_user_mobiles.append(existed_at_user_mobile)

    if is_build:
        """
        NOTE: 配置文件的结构决定了同一代码库只支持一个 Jenkins Job，原有的
        branch 列表其实是有迷惑性的，具体支持哪些分支其实是由 Jenkins Job 的
        配置决定的，原有代码里的 branch 列表其实只是做个拦截、筛选的作用
        auto_build_branch 和 auto_deploy_branch 同样也是有迷惑性的，真正 Job 做
        什么还得具体看 Job 的配置

        现改为以分支作为 Jenkins Job 的入口(尚不确定如果单次推送包含多个分支时
        Gitee 是按分支来分别触发 WebHook 事件还是单次事件中就包含该次推送的所有
        内容，从 Payload 的数据结构来看应该是按分支来多次触发推送)，同时支持原有
        格式的配置(即单一 Jenkins Job)，但新结构有个问题就是若仅有单 Jenkins
        Job 且该 Job 配置支持多个分支的话配置文件将比较冗余(建议单个 Job 不配置
        多分支)……
        """
        msg = '收到了构建请求!!\n' + msg + '开始向Jenkins提交构建请求\n'
        log.info('msg: %s' % msg)
        dingding_robot.send_text(msg=msg, at_mobiles=existed_at_user_mobiles)
        cause_msg = '%s+build' % git_hash
        if is_deploy:
            cause_msg = cause_msg + '_deploy'
            request_url = '%s%s/buildWithParameters?token=%s&is_deploy=true&cause=%s' % (jenkins_hosts, jenkins_url, jenkins_token, cause_msg)
        else:
            request_url = '%s%s/buildWithParameters?token=%s&is_deploy=false&cause=%s' % (jenkins_hosts, jenkins_url, jenkins_token, cause_msg)

        log.info(request_url)
        ret = requests.get(request_url, auth=(jenkins_user, jenkins_secret))
        log.info(ret.status_code)
        if ret.status_code == 201:
            location = ret.headers['location']
            log.info('location: %s' % location )
            log.info('get task info')
            try:
                task = requests.get(location + 'api/json', auth=(jenkins_user, jenkins_secret), timeout=10)
                if task.status_code != requests.codes.ok:
                    log.info(task.json)
                else:
                    log.error(task.text)
            except TimeoutError:
                log.error('request timeout')
        else:
            log.info('requests not ok')
            log.info(ret.text)
    elif len(existed_at_users) > 0:
        log.info('不构建，就通知一下')
        dingding_robot.send_text(msg=msg, at_mobiles=existed_at_user_mobiles)
    return [200, '%s/%s:%s done' % (namespace, name, ref), ""]


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
    app.run(host=listen, port=port, debug=debug, threaded=True)

