# 使用码云的Webhook完成K8S的自动构建与部署

Author: x2x4com@gmail.com

## 准备工作

- 码云账号
- Jenkins
- K8S环境
- 钉钉机器人
- 本地的镜像仓库
- 脚本运行服务器(虚机即可)
- Webhook的接收脚本
- 公网DNAT配置

## VMs
webhook脚本运行机, 192.168.1.234, ubuntu 18.04 64bit, Python3.6

镜像仓库用的是本地的仓库地址为192.168.1.234:5000


### 配置你的路由器
我这里使用的是默认的10080端口，请按照实际修改

![路由器配置](images/01.jpg)

### K8S环境
K8S环境部署这里不说了，请自行查看文档后部署

我的测试环境如下
```
NAME           STATUS    ROLES     AGE       VERSION   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION     CONTAINER-RUNTIME
kub-master-1   Ready     master    312d      v1.9.3    <none>        Ubuntu 16.04.3 LTS   4.4.0-87-generic   docker://17.12.1-ce
kub-node-1     Ready     <none>    312d      v1.9.3    <none>        Ubuntu 16.04.3 LTS   4.4.0-87-generic   docker://17.12.1-ce
kub-node-2     Ready     <none>    312d      v1.9.3    <none>        Ubuntu 16.04.3 LTS   4.4.0-87-generic   docker://17.12.1-ce
kub-node-3     Ready     <none>    312d      v1.9.3    <none>        Ubuntu 16.04.3 LTS   4.4.0-87-generic   docker://17.12.1-ce
```

我们这里简单粗暴点，登陆kub-master-1，将集群管理的配置文件复制到脚本运行机

```
sudo scp /etc/kubernetes/admin.conf runner@192.168.1.234:/home/runner
```

### Jenkins环境

需要用到的插件

- Generic Webhook Trigger
- 钉钉通知器


登陆Jenkins，创建项目，下面以blockscanner为例

1. 构建一个自由风格的软件项目
2. 勾选参数化构建过程

   添加下面的参数
   - 布尔值参数 is_deploy
   - 字符串参数 project_id 默认值 blockscanner
   - 字符串参数 local_registry 默认值 192.168.1.234:5000
   - 字符串参数 trigger_callback 默认值 http://192.168.1.234:10080/jenkins/callback
   - 字符串参数 trigger_token 默认值 abcdefg(自行更改)
   ![参数设置](images/02.jpg)
3. 源码管理选择Git， Repository URL: 你项目的地址，然后选择部署公钥Credentials下拉选择，分支写*/dev(请按照你想要的分支改动)
   ![源码管理](images/03.jpg)
(TODO 未完成)


### 脚本运行机

登陆脚本机， ssh runner@192.168.1.234

1. 安装kubectl
```
sudo apt-get update && sudo apt-get install -y apt-transport-https
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl
```

2. 复制授权文件
```
cd $HOME
[ ! -d ".kube" ] && mkdir .kube
[ ! -f "./kube/config" ] && mv ./kube/config ./kube/config.`date +%s`.bk
mv admin.conf .kube/config
```

3. 确认kubectl安装成功
```
$ kubectl version
Client Version: version.Info{Major:"1", Minor:"13", GitVersion:"v1.13.1", GitCommit:"eec55b9ba98609a46fee712359c7b5b365bdd920", GitTreeState:"clean", BuildDate:"2018-12-13T10:39:04Z", GoVersion:"go1.11.2", Compiler:"gc", Platform:"linux/amd64"}
Server Version: version.Info{Major:"1", Minor:"9", GitVersion:"v1.9.3", GitCommit:"d2835416544f298c919e2ead3be3d0864b52323b", GitTreeState:"clean", BuildDate:"2018-02-07T11:55:20Z", GoVersion:"go1.9.2", Compiler:"gc", Platform:"linux/amd64"}
```

```
$ kubectl get node
NAME           STATUS   ROLES    AGE    VERSION
kub-master-1   Ready    master   312d   v1.9.3
kub-node-1     Ready    <none>   312d   v1.9.3
kub-node-2     Ready    <none>   312d   v1.9.3
kub-node-3     Ready    <none>   312d   v1.9.3
```

4. 创建venv环境
```
cd $HOME
python3 -m venv webhook
```

5. 下载webhook接收脚本
```
cd webhook
git clone https://gitee.com/x2x4/gitee_trigger.git src
```

6. 激活venv环境
```
. bin/activate
```

7. 安装依赖文件
```
cd src
pip install -r requirements.txt
```

(TODO 未完成)
