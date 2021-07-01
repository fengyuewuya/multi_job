![avatar](https://pic.rmb.bdstatic.com/bjh/f4b531e188c54e69e3f1ec2434a1c7e9.png)
# Multi Job
### 0. 介绍
Multi Job 是基于文件级别, 轻量级, 多进程, 大规模, 高效率实现 Python 程序脚本运行的任务分发并行框架.

### 0.1 背景
2018年, 我需要在多台服务器上进行大规模的爬虫和数据分析, 这些服务器的配置不一, 不在同一个云平台, 现有方案难以满足需求.

#### 0.1.1 业务基础
 - 我已经完成 Python 任务文件
 - 我有很多台机器, 包括个人 PC, 不同云平台的服务器
 - 爬取和计算的的数据量大 并且 周期长

#### 0.1.2 核心需求
 - 可以将单例脚本在不同机器上大规模执行
 - 只需要输入任务参数, 其他均不需要关心
 - 可以自动化分配任务和均衡负载
 - 可以自动化回传数据
 - 可以统计程序运行的效率, 成功率等
 - 可以便捷进行任务文件的版本更新
 - 可以方便的管理任务和程序文件
 - 可以监控不同机器的负载情况
 - 可以修改不同机器的负载参数

### 0.2 架构
Multi Job 采用的是 Client - Server 架构, 包含以下 4 部分.
 - Server: 负责任务的存储, 分发, 统计和前端展示, 部署在服务节点.
 - Client: 负责从Server获取任务, 传结果, 可以控制任务负责数量, 部署在计算节点.
 - SDK: 负责用户的便捷接入.
 - 前端: 负责任务情况, 机器情况等统计分析的展示和交互.

### 0.3 特性
 - 部署简单
 - 多机器高并发: 该框架能够快速在多台机器部署并运行任务, 回传结果.
 - 自动化程序分发和版本控制: 在 Server 端添加任务类型后, Client 会自动进行版本比较和更新.
 - 任务全生命周期监控:
 - 任务效率统计分析: 后台会自动计算任务的运行时间, 成功率等指标.
 - 可视化前端:
 - Client 可控: 可以在前端直接控制 Client 的运行参数, 启停等信息. 
 - SDK支持: 可以加载 SDK 进行任务的更新, 提交和查询和控制.

### 0.4 技术选型
在设计和开发该框架时, 核心原则是简单, 高效, 可靠, 因此做了如下的技术选择:
 - 后台: Flask
 - 数据库: 基于SQLAlchemy, 支持Sqlite3, Mariadb, Mysql
 - 前端: Vue, Iview
 - 缓存层: Flask-Cache(基于内存), 未来引入Redis
 - Server 的任务分发队列: 暂无. 采用竞争性获取任务, 未来将会加入MQ.
 - Client 的任务运行队列: Multiprocessing 的 Queen.

### 0.5 任务流
#### 0.5.1 注册&跑任务
用户需要以下3步 实现自动化批量跑任务(具体操作见帮助信息):
1. 定义好自己的任务类型, python运行脚本及文件( main 文件和 return_main 文件)
2. 使用SDK或使用前端注册任务
3. 使用SDK添加任务和参数

#### 0.5.2 任务生命周期
需要运行的任务分为5个生命周期:
 - 状态码  0: 排队
 - 状态码  1: 在远端运行, 执行main中的work方法
 - 状态码  2: 运行结束, 任务结果回传成功, 如果存在 return_main 文件则在server所在机器执行 return_main 中的work方法
 - 状态码  3: 运行结束
 - 状态码 -1: 远端运行出错
 - 状态码 -2: 本地回传运行出错


### 0.6 开发人员
 - 项目负责人: fengyuewuya
 - 后端: fengyuewuya
 - 前端: fengyuewuya
 - 测试: fengyuewuya
 - logo: zixun

# 使用手册
### 1. 快速部署
从 github 拉取相关文件后:
 - 安装依赖环境:  
   + cd server; pip install -r requirements.txt
   + cd client; pip install -r requirements.txt
   + cd SDK; pip install -r requirements.txt
 - 启动 server: cd server; python run.py  (默认端口为 5006, 可以自行修改)(熟悉 flask 可以使用 python manager.py runserver 启动)
 - 启动 client: cd client; python controller.py
 - 整体流程测试: cd tests; python work.py
 - 查看网页前端: 浏览器访问 127.0.0.1:5006/home

### 2. 增加任务类型
注意, 需要添加的任务(假如任务名为 new_job )结构必须如下:  
new_job/     
|-- main.py:  主运行程序. 远端 client 执行, 包含work方法, 返回json,  如  {"result": "multi_job", "count":6, "return_data":1}.   
|-- return_main.py:  回调程序. server 执行, 包含work方法, 输入为上一步的 return_data.    
|-- ..... : 其他依赖相关文件
    
注意:
 - 分发时, 将会将该文件夹下的内容(不包含return_main.py 文件) 更新到 Client 节点
 - 增加任务类型, 任务的版本 version = 0, 更新时 version = version + 1
 - 版本信息 在 new_job/.info 文件内.

##### 2.1 添加/更新 一个简单任务 new_job
在 Server 服务器的 server/static/jobs 的目录增加文件类型    
以添加/更新 new_job 为例:
- a. 创建任务文件夹: 在 server/static/jobs/new_job
- b. 写业务代码: server/static/jobs/new_job/main.py
  ```
  # coding=utf-8
  
  # 测试任务, 输入 x, y, label 返回一个组合的字符串
  import random
  import time
  
  # work是远端运行的主方法, multi_job 会将该文件夹下的程序分发到其他Client, 并进行参数传递和结果回传
  
  def work(x, y, label='new_job'):
      z = x + y
      time_0 = time.time()
      result = "sum result:%s, label: %s, unix_time: %s " % (z, label, time_0)
      # work 的返回结果必须是 json, 字段为 result, count, return_result, 要求如下:
      # result 必填字段,该结果将会入库展示;
      # count 选填字段, 默认为1, 用来进行性能统计分析
      # return_result 选填字段, 默认为None, 不等 None 的话, 则传给 return_main.py 的work方法
      return {"result": result, "count":1, "return_result": None}
  
  
  if __name__ == "__main__":
      data = work(x=1, y=2, label='new_job')
      print(data)

  ```
- c. 添加该任务类型, 有两种方法:
  - 网页前端方法: 
    在 url/#/job_type ==> 点击左上角 增加任务类型 ==> 选择job_type ==> 点击 更新任务种类 ==> 选择 new_job ==> 点击更新任务种类
  
  - SDK方法:
    ```
    from MultiJob import MultiJob
    client = MultiJob(base_ur="http://127.0.0.1:5006")
    # 注册任务
    client.update_job_file_status(job_type="new_job")
      ```
- d. 插入一条任务:
    ```
    from MultiJob import MultiJob
    # base_url 即是 server 的地址
    client = MultiJob(base_url="http://127.0.0.1:5006")
    # 注册任务
    job_id = client.insert_job(job_type="new_job", x=1, y=2, label="multi_job")
    # 查看任务状态
    result = client.get_job_detail(job_id)
    print(result)
    ```

##### 2.2 添加复杂任务 save_stock_data
以添加 save_stock_data (参考: https://www.zhihu.com/question/438404653/answer/1717279374) 数据为例子.   
实现目标, 爬取股票数据, 并保存在本地.
 - a. 创建任务文件夹: 在 server/static/jobs/save_stock_data
 - b. 业务代码:   
   server/static/jobs/save_stock_data/get_stock_data.py   
  ```
# coding=utf-8
import requests
import random
import time
# 爬取一条数据, 并返回给数据库
# 如何用 python 获取实时的股票数据？ - sheen的回答 - 知乎
# https://www.zhihu.com/question/438404653/answer/1717279374

def get_stock_data(id, scale, data_len):
    symsol = '股票代码'
    scale = scale
    data_len = data_len
    url = 'http://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData'
    res = requests.get(url, params={"symbol":id, "scale":scale, "datalen":data_len})
    data = res.json()
    bar_list = []
    data.reverse()
    for tmp_dict in data:
        bar = {}
        bar['date'] = tmp_dict['day']
        bar['open'] = float(tmp_dict['open'])
        bar['high'] = float(tmp_dict['high'])
        bar['low'] = float(tmp_dict['low'])
        bar['close'] = float(tmp_dict['close'])
        bar['volume'] = int(tmp_dict['volume'])
        bar_list.append(bar)
    return bar_list

if __name__ == "__main__":
    result = get_stock_data('sz000829', 30, 1)
    print(result)

  ```   
   server/static/jobs/save_stock_data/main.py
  ```
# coding=utf-8
# 任务的主运行代码
import requests
from get_stock_data import get_stock_data
def work(stock_id, time_sep, time_length):
    result = get_stock_data(stock_id, time_sep, time_length)
    count = len(result)
    result = {stock_id:result}
    return {'result':result, 'count':count, 'return_data':result}

if __name__ == "__main__":
    print(work('sz000829', 30, 1))
   ```
server/static/jobs/save_stock_data/return_main.py
  ```
# coding=utf-8
# 将爬取的股票结果 保存到本地
# 任务的回调代码,  在 server 端执行, 不会分发到 client 端
# work 中返回的 return_data 的数据 将会传入到这个方法中
# 强烈建议！不要向 return_main 添加复杂功能,  否则会对server性能产生巨大影响
import requests
import os
import json
dir = "" # 注意改成你自己的本机路径
def work(return_data):
    save_dir = open(dir).read().strip()
    for stock_id in return_data:
        tmp_dir = os.path.join(save_dir, stock_id)
        with open(tmp_dir, 'w') as w:
            w.write(json.dumps(return_data[stock_id], indent=2))

if __name__ == "__main__":
    return_data = {'sz000829': [{'date': '2021-06-21 15:00:00', 'open': 7.01, 'high': 7.03, 'low': 6.99, 'close': 7.02, 'volume': 2421500}]}
    work(return_data)

   ```
- c. 添加该任务类型, 有两种方法:
    - 网页前端方法:
      在 url/#/job_type ==> 点击左上角 增加任务类型 ==> 选择job_type ==> 点击 更新任务种类 ==> 选择 new_job ==> 点击更新任务种类

    - SDK方法:
      ```
      from MultiJob import MultiJob
      client = MultiJob(base_ur="http://127.0.0.1:5006")
      # 注册任务
      client.update_job_file_status(job_type="new_job")

- d. 插入一条任务:
    ```
    from MultiJob import MultiJob
    # base_url 即是 server 的地址
    client = MultiJob(base_url="http://127.0.0.1:5006")
    # 注册任务
    job_id = client.insert_job(job_type="new_job", stock_id='sz000829', time_sep=30, time_length=1)
    # 查看任务状态
    result = client.get_job_detail(job_id)
    print(result)
    ```

##### 2.3 在非 server 节点添加/更新任务
在非 server 节点添加和更新任务也很简单     
以 new_job 为例子, 假设文件夹路径为本机  /Path/new_job, 目录结构和 2.1 中一致
 - 使用SDK的方式添加任务:
```
    from MultiJob import MultiJob
    client = MultiJob(base_url="http://127.0.0.1:5006")
    # 注册任务
    client.update_job_file_status(job_type="new_job", job_path="/Path/new_job")
```

### 3. Server 操作说明
Server 配置文件为 config/config.json, 包含如下几个字段:  
 - host: 运行的地址, 本地运行设为 127.0.0.1, 公网运行设为 0.0.0.0 .
 - port: 监听端口, 默认为 5006.
 - db: 数据库的链接, 默认为 sqlite3. 支持sqlite3 和 pymysql.
 - debug: 是否开启debug模式, 默认为true, 生产环境建议改为 false.

#### 3.1 部署在公网
跨云多平台运行, 机器必须在公网/该段局域网 有独立IP、映射端口等.    
将host设为 0.0.0.0, port 设为对应的映射端口即可.

#### 3.2 部署在域名模式
部署在域名模式, 建议采用 nginx + gevent + gunicorn 的模式运行, 在 nginx 下配置域名.

#### 3.3 调整数据库
将server的运行数据库调整为mysql数据库, 可以将 db 设为 mysql相关语法, 如下:   
mysql+pymysql://user:password@host/table_name?charset=utf8

#### 3.4 调整高负载模式
提高负载能力, 建议采用mysql + gunicorn + gevent 的模式. 
最高可以同时支持1000台以内 client 节点.

### 4. Client 操作说明
Client 的配置文件在 Client/config/config.json, 包含如下几个字段:
 - host: Server 的ip/域名地址.
 - port: Server 运行的端口.
 - limit_process: 该 Client 最大同时运行多少任务, 整型, 修改config.json / 网页前端修改, 无需重启任务.
 - machine_id: 机器的唯一标识, 会自动向 server 获取.
 - name: 你给机器起的名字.
 - tag: 该机器能运行哪些任务.

#### 4.1 查看 Client 的状态
在前端的 机器列表 页面可查看 机器负载, 完成任务情况 等信息, 并修改运行参数.

#### 4.2 多机器部署
 - 需要保证 Client 服务器可以访问到server, 建议server为公网模式.
 - 在新的服务器的 config 中设置 host 和 port 为 server 相关地址, 启动 controller.py 即可.
 - Linux 后台挂载运行 controller.py 可以使用 nohup 相关命令.

#### 4.3 调整 Client 的任务负载 limit_process
 limit_process 最小为1, 有两种方式进行修改:
 - 热修改: 无需重启, 直接修改 client/config/config.json 中的 limit_process 的值.
 - 前端修改：在网页前端手动修改机器的 limit_process, 等待 1 分钟后会自动同步.

#### 4.4 调整 Client 的可执行任务类型 tag
有两种方式进行修改: 
 - 热修改: 直接修改client/config/config.json 中的 tag 的值, 注意英文逗号分割.
 - 前端修改: 在网页前端手动修改机器的 tag, 注意英文逗号分割, 等待 1 分钟后会自动同步.

#### 4.5 暂停 Client 接收任务 
有两种方式进行暂停:
 - 热暂停: 在想暂停的那台机器 client/目录下创建 Pause 文件.
 - 前端暂停: 在网页前端点击 暂停按钮.

激活机器:
 - 热暂停: 在你想暂停的那台机器client/目录下 删除 Pause 文件.
 - 前端暂停: 在网页前端点击 继续 按钮.

#### 4.6 关闭 Client
有两种方式关闭 Client:
- 热关闭: 在client/目录下 创建 End 文件.
- 前端关闭: 在网页前端点击机器的 关闭 按钮.

### 5. 任务 Job 操作说明
该部分主要针对的是任务相关的插入和查看, 可以参考 tests/work.py 的相关例子.

#### 5.1 添加任务
通过SDK方式添加任务, 提交任务包含如下几个字段:
 - job_type: 任务类型
 - 任务参数: main.work 运行的输入参数.
 - batch: 任务的批次, 用来进行分组统计分析性能, 不设置则默认为 年-月-日 (2020-01-01), 需要在提交任务前设置.
 - tag: 任务的标签, 决定了哪些机器可以执行该任务. Client 的 tag 必须包含 Job 的 tag, 该 Client 才能执行该任务. 默认为空, 即不限制执行机器, 需要在提交任务前设置.
 - priority: 任务的优先级, 默认为0, 该值越大, 优先级越高, 越快进行处理, 需要在提交任务前设置.
 - limit_count: 任务失败后的重试次数, 默认为1, 需要在提交任务前设置.
```
from MultiJob import MultiJob
# base_url 即是 server的地址
client = MultiJob(base_url="http://127.0.0.1:5006")
# 注册任务
job_id = client.insert_job(job_type="test_job", 1, 2, data=3)
# 查看结果
result = client.get_job_detail(job_id)
print(result)
```

#### 5.2 设置任务批次 batch
batch 任务的批次, 用来进行分组和统计分析性能, 默认为 年-月-日 (2020-01-01).
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 设置 batch 为 test
client.set_batch("test")
```

#### 5.3 设定任务的标签 tag
tag 任务的标签, 决定了哪些机器可以执行该任务. 机器的tag必须包含任务tag, 该机器才能执行该任务. 默认为空, 即不限制执行机器.
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 设置 tag 为 test, 决定了哪些机器可以跑该任务. 只有 machine 的 tag 包含 test 的机器才可以接受该任务.
client.set_tag("test")
```

#### 5.4 设定任务的优先级 priority
任务的优先级, 默认为0. 该值越大, 优先级越高, 越快进行处理, 需要在提交任务前设置.
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 设置 tag 为 test, 决定了哪些机器可以跑该任务. 只有machine 的 tag 包含 test 的机器才可以接受该任务. 
client.set_priority(66)
```

#### 5.5 设定任务的重试次数 limit_count
任务失败后的重试次数, 默认为1, 需要在提交任务前设置.
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 设置 tag 为 test, 决定了哪些机器可以跑该任务. 只有machine 的 tag 包含 test 的机器才可以接受该任务. 
client.set_limit_count(2)
```

#### 5.6 查看任务结果 get_job_detail
使用 SDK/网页前端 查看任务的详情信息
 - 单条任务的结果包含以下字段:
   - id: 任务的id
   - job_type: 任务类型
   - status: 任务状态. 0: 排队. 1: 运行. 2: 远端运行成功, 正在回调. 3: 回调成功. -1: 远端运行出错. -2: 回调运行出错
   - input_data: 输入的参数
   - result: 返回的任务结果
   - machine_id: 执行任务的机器(任务们没有被执行时, 该值为空)
   - limit_count: 重试的次数
   - priority: 任务的优先级
   - return_count: 返回的数据条数
   - spend_time: 跑任务的时间
   - tag: 任务的标签
   - version: 跑该任务的程序版本(任务没有被执行的时, 为-1)
   - create_time: 创建时间
   - update_time: 任务的更新时间
   -


 - 使用SDK查看任务结果
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 查看结果
job_id = 1
result = client.get_job_detail(job_id)
print(result)
```
 - 从前端可以直接查看结果

#### 5.7 任务debug
任务debug可以采用如下方法:
 - 查看任务状态. 当任务运行失败, 任务失败的错误日志会回传到 job 的 result 字段, 查看该字段以debug.
 - 加载云端任务到本地. 可以将注册好的任务加载到本地的实际运行.
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 加载任务
client.load_job_file(job_type="test_job")
# client.main 即是运行 main的work方法 
# 查看结果 
result = client.main(1, 2, 3)
# 如果有 return_main 可以运行 return_main
result_0 = client.return_main(result) 
```
 - 直接加载本地文件. 在上线之前可以加载本地的任务文件, 测试运行. 
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# jobs/test_job 就是你的任务所在的文件地址
job_path = "jobs/test_job"
client.load_job_file(job_path=job_path)
# 查看结果
result = client.main(1, 2, 3)
# 如果有 return_main 可以运行 return_main
result_0 = client.return_main(result) 
```

#### 5.8 查看任务统计信息 get_job_summary 
使用 SDK/网页前端 查看任务的统计信息
- 任务统计分析的输入参数为
    - job_type: 需要查询的任务类型
    - batch: 任务批次. 默认为 -1, 表示不需要使用batch字段进行分组分析.   
      batch=None 的时候, 表示使用 job_type 和 和全部 batch 统计分析.   
      batch=特定值, 表示使用 job_type 和 特定 batch 进行统计分析.
      
- 结果返回的为 list 包含以下字段:
    - job_type: 任务类型
    - batch: 任务批次
    - finished_task: 已经完成的任务
    - waiting_task: 排队任务
    - working_task: 运行中任务
    - failed_task: 失败任务
    - count: 返回的数据量
    - spend_time: 成功任务的平均消耗时间 秒.
    - begin_time: 任务的最早开始时间
    - update_time: 任务的最近更新时间
    - tag: 任务的标签
    
例子:
```
[
  {
    "batch": "2021-06-30",
    "begin_time": "2021-06-23 15:15:17.048781",
    "count": 2,
    "failed_task": 0,
    "finished_task": 2,
    "job_type": "test_job",
    "spend_time": 0.0006,
    "tag": "",
    "update_time": "2021-06-30 16:43:23.688588",
    "waiting_task": 4,
    "working_task": 0
  }
]
```

 - SDK方式
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 
result = client.get_job_summary(job_type="test_job", batch=-1)
# 查看结果
print(result)
```

 - 网页前端, 网页前端直接访问即可
#### 5.9 重跑任务 rerun job
可以使用 SDK/网页前端 重跑任务, 注意!重跑任务的话, 任务ID不会改变, 只会改变任务状态为等地啊中.  
同时, 可以进行批量的重跑任务
- 重跑任务的参数, 至少有一个参数非空
    - job_id: 需要重跑的任务ID, 默认为None
    - job_type: 过滤 任务类型, 默认为None
    - machine_id: 过滤 任务的machine_id, 默认为None
    - batch: 过滤 任务的batch, 默认为None
    
- 返回结果
  - 1: 提交成功
  - 0: 提交失败
    
 - SDK方式
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 查看结果
job_id = 1
result = client.rerun_job(job_id=job_id)
print(result)
```
 - 网页前端, 网页前端直接点击按钮即可.

#### 5.10 复制任务 copy_job
可以使用 SDK/网页前端 复制任务, 注意!复制任务的话, 任务ID为全新.  
同时, 可以进行批量的复制任务
- 复制任务的参数, 至少有一个参数非空
    - job_id: 需要重跑的任务ID, 默认为None
    - job_type: 过滤 任务类型, 默认为None
    - machine_id: 过滤 任务的machine_id, 默认为None
    - batch: 过滤 任务的batch, 默认为None

- 返回结果
    - 1: 提交成功
    - 0: 提交失败

- SDK方式
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 查看结果
job_id = 1
result = client.copy_job(job_id=job_id)
print(result)
```
- 网页前端, 网页前端直接点击按钮即可.
#### 5.11 停止任务 kill_job
使用 SDK/网页前端 停止任务, 注意只有 等待中的任务 和 运行中任务 可以停止任务.  
同时, 可以进行批量的停止任务
- 复制任务的参数, 至少有一个参数非空
    - job_id: 需要重跑的任务ID, 默认为None
    - job_type: 过滤 任务类型, 默认为None
    - machine_id: 过滤 任务的machine_id, 默认为None
    - batch: 过滤 任务的batch, 默认为None

- 返回结果
    - 1: 提交成功
    - 0: 提交失败
    
- SDK方式
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 查看结果
job_id = 1
result = client.stop_job(job_id)
print(result)
```
- 网页前端.网页前端直接点击按钮.

#### 5.12 删除任务 delete_job
使用 SDK/网页前端 删除任务, 注意! 运行中任务不能删除.  
同时, 可以进行批量的删除任务.
- 复制任务的参数, 至少有一个参数非空
    - job_id: 需要重跑的任务ID, 默认为None
    - job_type: 过滤 任务类型, 默认为None
    - machine_id: 过滤 任务的machine_id, 默认为None
    - batch: 过滤 任务的batch, 默认为None

- 返回结果
    - 1: 提交成功
    - 0: 提交失败

- SDK方式
```
from MultiJob import MultiJob
client = MultiJob(base_url="http://127.0.0.1:5006")
# 查看结果
job_id = 1
result = client.delete_job(job_id)
print(result)
```
- 网页前端.网页前端直接点击按钮即可.
