# sync_aws_ecr_images
Synchronize all tags images between cn and us
该脚本用来同步cn和us 的ECR仓库以及所有版本的镜像，因为aws目前不支持国内外的ECR同步

# 环境部署
## 安装python3.8
我这里用的是python3.8，centos7的安装方法可以参考：
```shell
yum -y install yum-utils wget && yum -y groupinstall "Development tools" && yum -y install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel && yum install libffi-devel -y && mkdir /usr/local/python3 && cd && wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tgz && tar -zxvf  Python-3.8.3.tgz && cd Python-3.8.3 && ./configure --prefix=/usr/local/python3 && make && make install && rm -rf /usr/bin/python && ln -s /usr/local/python3/bin/python3 /usr/bin/python && rm -rf /usr/bin/pip && ln -s /usr/local/python3/bin/pip3 /usr/bin/pip && sed -i "s/python/python2/" /usr/bin/yum && sed -i "s/python/python2/" /usr/libexec/urlgrabber-ext-down && sed -i "s/python/python2/" /usr/bin/yum-config-manager && pip --no-cache-dir install boto3
```
其他系统自己安装一下吧，要保证执行`python`出来的版本是3.8，另外需要pip/pip3安装boto3依赖库，其他不需要了
## 安装docker
docker的安装大同小异，保证docker能用即可
## 安装AWS CLI
这里参考https://docs.aws.amazon.com/zh_cn/cli/latest/userguide/install-cliv2-linux.html
## AWS账号配置
sync脚本的开始有账户信息的配置，如下，按照实际的账户配置即可，不配置无法运行
```python
CN = {"region": "cn-north-2",
      "access_key_id": "string",
      "secret_access_key": "string"}
NET = {"region": "us-west-2",
       "access_key_id": "string",
       "secret_access_key": "string"}
```
然后配置aws的登录信息，这里可以参考https://docs.aws.amazon.com/zh_cn/cli/latest/userguide/cli-configure-quickstart.html
```shell
$ aws configure --profile cn-north-2
AWS Access Key ID [None]: AKIAI44QH2DHBFCAMPXE
AWS Secret Access Key [None]: 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
Default region name [None]: cn-north-2
Default output format [None]: 
```
需要注意的是`aws configure --profile [region]`中的`region`部分一定要和上面配置账户的`region`一样，你如果配置的是`CN = {"region": "cn-north-2",...`这里就需要执行`aws configure --profile cn-north-2`，然后根据提示输入对应的`access_key_id`和`secret_access_key`，`Default output format [None]:`可以回车跳过，这里需要将CN和NET的账户信息都配置好，请务必保证一一对应不要配错

# 开始
你可以单次执行：
```shell
chmod +x ./sync.py
./sync.py
```
也可以配合crontab执行定时计划任务，也可以通过hook触发执行。


