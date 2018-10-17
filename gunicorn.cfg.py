# encoding: utf-8

import multiprocessing
 
# 监听本机的8000端口
bind = '0.0.0.0:8000'
 
preload_app = True
 
# 开启进程
# workers=4
workers = multiprocessing.cpu_count() * 2 + 1
 
# 每个进程的开启线程
# threads = multiprocessing.cpu_count() * 2
threads = multiprocessing.cpu_count()
 
backlog = 2048
 
#工作模式为meinheld
# pip install meinheld
worker_class = "egg:meinheld#gunicorn_worker"
 
# debug=True
 
daemon = True
 
# 进程名称
proc_name = 'gunicorn.pid'
 
# 进程pid记录文件
pidfile = 'app_pid.log'

chdir = '/home/runner/UpdateHook'

loglevel = 'info'
logfile = 'debug.log'
accesslog = 'access.log'
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'    #设置gunicorn访问日志格式，错误日志无法设置

"""
其每个选项的含义如下：
h          remote address
l          '-'
u          currently '-', may be user name in future releases
t          date of the request
r          status line (e.g. ``GET / HTTP/1.1``)
s          status
b          response length or '-'
f          referer
a          user agent
T          request time in seconds
D          request time in microseconds
L          request time in decimal seconds
p          process ID
"""
accesslog = "/tmp/gunicorn_access.log"      #访问日志文件
errorlog = "/tmp/gunicorn_error.log"
