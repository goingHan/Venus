# Venus
文件流转工具，目前支持sftp，ftp，本地流转三种方式
#### 介绍
----
应用于文件接口的场景。文件接口在系统之间传播往往是用文件的形式，比如A系统会把自己的文件接口放在本系统的文件服务器上（ftp,sftp）,B系统通过ftp/sftp客户端
来获取文件接口。但是当文件接口数量多的时候，人为获取就令人头皮发麻了，所以使用Python写了一个程序Venus（维纳斯）完成这件事。Venus需要借助Linux的定时任务
来查找需要流转的文件。

#### 用到的工具
----
- Python3
- Python paramiko
- Python threadpool

#### 限制
----
- 支持 Linux和linux之间的流转
- 支持 Windows和Windows之间的流转
- 暂不支持Linux和Windows之间的流转（主要是路径得问题，计划下个版本解决）
#### 基本使用
----
Venus同时支持本地流转，SFTP，FTP，用户可以按照自己的需要配置。`#`表示注释。
- 修改备份目录
----
本地流转，本地上传到远端，在移动文件之前都会进行备份，所以需要备份目录。
```
main.py脚本的 self.bak_dir = 'D:\Game\Config' 这行代码是目前的备份目录。修改单引号内部的值为你的备份路径（绝对路径）。
```
- 本地流转
> 文件从本地的一个目录流转到本地的另一个目录
```
/app  venus???.txt  - - /app/01
```
上面配置的意思是在/app目录下查找 venus???.txt 模式的文件拷贝到/app/01目录下。切记不要不忘记两个 `-`。

- sftp上传
> 把本地文件上传到远端
```
/app,venus???.txt,192.168.200.12,sftpuser,123.com,/app/venus
```
意思是在本地/app目录下查找venus???.txt模式的文件，使用sftpuser用户和123.com密码把文件上传到192.168.200.12服务器的/app/venus目录下。
如果你的ssh端口不是22，这里的ip写成`ip:port`的形式即可，比如`192.168.200.12:1522`
- sftp 下载
```
192.168.200.12,sftpuser,123.com,/app,venus???.txt,/app/venus
```
意思是在192.168.200.12服务器上使用sftpuser用户和123.com密码，在/app目录下查找venus???.txt模式的文件，下载到本地的/app/venus目录下。
- ftp 上传
```
/app,windows???.txt,192.168.200.12,venus,123.com,/app/ftp
```
意思是在本地查找windows???.txt模式的文件，使用veuns用户和123.com密码，把文件上传到/app/ftp目录下

- ftp 下载
```
192.168.200.12,venus,123.com,/app,Es*.py,/app/ftp
```
意思是使用venus用户密码123.com在192.168.200.12服务器的/app目录下查找Es*.py模式的文件下载到本地的/app/ftp目录下。
#### 一对多
----
> 一对多规则是指一个文件流转到多个目标目录，暂时支持sftp的上传和下载和本地的上传和下载,配置文件是one_more
- 添加标志
```
python main.py insert sftp_up 001 hananmin /app /app01
```
| 例子     |解释|是否必填|可选值|
| -------- |--------|--------|--------|
|insert|固定字段|是||
|sftp_up|表示sftp上传时使用|是|sftp_up,sftp_down,local|
|001|标识的唯一值|是|可以自行定义，保持唯一|
|hananmin|备注|是|可自行定义|
|/app /app01|标志包含的目录名|是|可以写多个|
- 查询标志
```
python main.py  look 001
```
| 例子     |解释|是否必填|可选值|
| -------- |--------|--------|--------|
|look|固定字段|是||
|001|标识的唯一键|是||
- 添加配置文件
```
# sftp
sftp_up,/app,192.168.200.12,appmon,123.com,linux???.txt,sign_sftp_up
```
| 例子     |解释|是否必填|可选值|
| -------- |--------|--------|--------|
|sftp_up|表示该规则是用于sftp的上传|是|sftp_up sftp_down local|
|/app|源文件所在目录|是||
|192.168.200.12|对方服务器的IP|是|如果ssh的端口不是22，此处可以是IP:port的形式指定；如果是本地流转，此处填写"-"即可|
|appmon|对方服务器的用户|是||
|123.com|对方服务器的用户的密码|是||
|linux???.txt|对方服务器的用户|是||
|sign_sftp_up|标识的唯一key|是|事先添加好的标识的唯一key|
#### 运行
----
python main.py run '日志路径'
- 日志路径是用来存储日志
建议使用nohup运行,如：
`nohup python main.py run /app/log >> /app/log/venus.out 2>&1`

#### qq群
脚本和文档写的仓促，有问题就请加入 630300475 QQ群。@搬砖工即可。
