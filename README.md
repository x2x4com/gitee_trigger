# Gitee WebHook回调用工具集

## 安装与依赖

代码需要Python3(请自行安装)

### 创建虚拟环境

```bash
python3 -m venv webhook
```

### 激活虚拟环境

```bash
cd webhook && . bin/activate
```

### 安装依赖
```bash
pip install -r requirements.txt
```

### 拉代码
```bash
git clone https://github.com/x2x4com/gitee_trigger.git src
```

## 脚本介绍

### cfg.py
所有的脚本都会从cfg.py里面读取各自需要的参数，请从example文件内复制格式过去自行修改


### 日志输出
各脚本内都有类似这样的语句

```python
log.set_logger(filename="/tmp/UpdateHook.log", level='INFO', console=False)
```

- filename 日志文件保存文件名，最好写全路径
- level 日志级别
- console 是否在终端上打印出日志


### 1. UpdateHook.py

最老的原始版本，主要设计用途是在git提交后自动在服务器上拉代码

默认监听10080，可以在脚本头上面自行修改

运行方式

```bash
python3 UpdateHook.py
```

回调入口

http://ip:10080/oschina/update.json


### 2. UpdateGitMirror.py

码云并不支持Git库的镜像，因为我们用的是GCP的K8S服务，但是GCP支持Github和Bitbucket(当时Github私有库并没有完全开放)，
所以我们需要将gitee的仓库自动镜像一份到Bitbucket，然后通过Bitbucket授权GCP的触发器来自动打包业务镜像，于是就有了这个工具

工作原理几乎和原始版本一致，就只是调用的命令不一样而已


### 3. UpdateDev.py

dev分支
这个脚本主要用户测试环境的自动构建，研发通过特定的commit字段来触发自动构建或者自动部署，脚本会与后端的Jenkins服务通讯，
并远程触发Jenkins的流程，在Jenkins完成流程后再回调通知脚本并触发钉钉的信息提示

alpha分支
当发现alpha分支merge后，自动为负责运维的小伙伴下个alpha更新的工单

master分支
还没做TODO

脚本会保存信息到SQLite，默认在/data/update_dev.db，可以在脚本头的地方改

## 如何使用

TODO



