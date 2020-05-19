#coding=utf-8
import sqlite3
import os
import sys
abs_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(abs_path)
import time
from multiprocess import Process, Queue
import zipfile
import json
import requests
import logging
import psutil
import logging, logging.handlers, logging.config
def append_process(data, queue_0):
    # 开启多进程任务
    import os
    import sys
    import importlib
    file_path = 'jobs/' + data['job_type'] + '/'
    os.chdir(file_path)
    sys.path.append('./')
    result = {}
    try:
        main = importlib.import_module('main')  # 绝对导入
        tmp_result = main.work(data)
        result['count'] = tmp_result['count']
        result['result'] = tmp_result['result']
        result['return_data'] = tmp_result['return_data']
        result['status'] = 2
    except Exception as e:
        result = {'result': str(e), 'count': 0}
        result['status'] = -1
        result['return_data'] = ''
    result['id'] = data['id']
    result['job_type'] = data['job_type']
    queue_0.put(result)

# 0. 读取logger配置文件, 并配置logger
log_config = json.load(open("./log_config.json"))
logging.config.dictConfig(log_config)

# 1. 配置 controller相关配置
queue_0 = Queue(9999)
class controller(object):
    def __init__(self, config = "./config.json"):
        logging.info("开始初始化")
        all_config = json.load(open(config))
        self.base_url = all_config['host'].strip('/') + '/'
        self.limit_process = all_config['limit_process']
        # 设置相关的运行参数
        self.count_process = 0
        self.count_done_job = 0
        self.count_all_job = 0

    # 获取一个job
    def get_job(self):
        begin_time = time.time()
        data_all = requests.get(self.base_url + 'get_job').json()
        data = data_all['data']
        if data_all['status'] == 1:
            if self.check_job_file(job_type=data['job_type']) == 0:
                self.get_job_file(job_type=data['job_type'])
                self.unzip_file(job_type=data['job_type'])
            self.run(data)
        return data

    # 检测job文件是否更新
    def check_job_file(self, job_type):
        file_name = 'jobs/' + job_type + '.zip'
        if os.path.exists(file_name):
            return 1
        return 0

    # 获取job_file
    def get_job_file(self, job_type):
        file_name = 'jobs/' + job_type + '.zip'
        data_url = self.base_url + 'get_data?job_type=' + job_type
        res = requests.get(data_url)
        with open(file_name, "wb") as code:
            code.write(res.content)

    # 解压zip文件
    def unzip_file(self, job_type):
        file_name = 'jobs/' + job_type + '.zip'
        file_path = 'jobs/' + job_type
        if zipfile.is_zipfile(file_name):
            fz = zipfile.ZipFile(file_name, 'r')
            for tmp_file in fz.namelist():
                fz.extract(tmp_file, file_path)
        else:
            print('This is not zip')

    # 2. 注册服务器
    def append_machine(self):
        # 注册服务器，并上传服务器的各种信息
        url = self.base_url + 'append_machine'
        tmp_data = {'machine_id': self.machine_id, "name": self.name, "limit_process": self.limit_process}
        res = requests.post(url=url, data=tmp_data)
        return res.text

    # 3. 获取服务器的运行状态
    def get_machine_config(self):
        # 上传服务器信息
        url = self.base_url + 'get_machine_config'
        # cpu 信息
        cpu_data = "%s/%s" % (psutil.cpu_count(), psutil.cpu_count(logical=False))
        # 内存信息
        mem = psutil.virtual_memory()
        mem_data = "%s/%s" % (round(mem.free / 1024 / 1024 / 1024, 2), round(mem.total / 1024 / 1024 / 1024, 2))
        # 硬盘信息
        psutil.disk_partitions()
        psutil.disk_usage('/')
        disk_data = psutil.disk_usage(os.path.dirname(os.path.abspath(__file__)))
        disk_data = "%s/%s" % (
        round(disk_data.used / 1024 / 1024 / 1024, 2), round(disk_data.total / 1024 / 1024 / 1024, 2))
        # 开机时间
        boot_time = psutil.boot_time()
        # 正在运行的线程信息
        tmp_data = {'machine_id': self.machine_id, "limit_process": self.limit_process, "cpu_data": cpu_data,
                    "mem_data": mem_data, "disk_data": disk_data, "boot_time": boot_time,
                    "count_process": self.count_process}
        res = requests.post(url=url, data=tmp_data)
        return int(res.text)

    # 5. 多进程主程序
    def run(self, data):
        self.count_process += 1
        self.count_all_job += 1
        p = Process(target=append_process, args=(data, queue_0))
        p.dameon = False
        p.start()

    # 6. 获取任务结果, 并上传
    def get_result(self):
        data = -1
        if queue_0.qsize() > 0:
            self.count_done_job += 1
            self.count_process -= 1
            data = queue_0.get()
            if data:
                # 上传数据
                self.upload_data(data)
        return data

    # 7. 上传结果
    def upload_data(self, data):
        url = self.base_url + 'update_job'
        headers = {'Content-Type': 'application/json'}
        res = requests.post(url=url, headers=headers, data=json.dumps(data))

    def work(self):
        begin_time = time.time()
        while True:
            time.sleep(1.5)
            begin_time = time.time()
            begin_time = time.time()
            if self.count_process < self.limit_process:
                self.get_job()
            begin_time = time.time()
            self.get_result()

    # 分配任务 多进程执行
    def assign_job(self, data):
        job_type = data['job_type']
        if str(job_type) == '0':
            logging.info("开始爬虫任务")
            p = Process(target=crawl_data.get_stock_data_from_sina, args=(data,))
            p.start()
        if str(job_type) == 'qq':
            p = Process(target=crawl_data.get_data_from_qq, args=(data,))
            p.start()

if __name__ == '__main__':
    tmp = controller()
    #tmp.work()
    '''
    while True:
        time.sleep(5)
        data = tmp.get_job()
        print(data)
        if not data.get('id'):
            continue
        tmp.assign_job(data)
    '''
