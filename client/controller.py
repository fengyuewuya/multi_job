#coding=utf-8
import sqlite3
import os
import sys
import gc
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
    import time
    file_path = 'jobs/' + data['job_type'] + '/'
    os.chdir(file_path)
    sys.path.append('./')
    result = {}
    begin_time = time.time()
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
    end_time = time.time()
    result['id'] = data['id']
    result['job_type'] = data['job_type']
    result['spend_time'] = end_time - begin_time
    queue_0.put(result)

# 0. 读取logger配置文件, 并配置logger
log_config = json.load(open("./log_config.json"))
logging.config.dictConfig(log_config)

# 1. 配置 controller相关配置
queue_0 = Queue(9999)
class controller(object):
    def __init__(self, config = "./config.json"):
        logging.info("开始初始化")
        self.config = config
        # 初始化 运行参数
        self.get_config()
        # 记录运行情况
        self.count_process = 0
        self.count_done_job = 0
        self.count_all_job = 0
        # 记录网络参数
        self.headers = {'Content-Type': 'application/json'}
        self.cookies = {"machine_id":self.machine_id, "tag":self.tag}

    # 获取 config 信息
    def get_config(self):
        all_config = json.loads(open(self.config).read())
        self.all_config = all_config
        self.machine_id = all_config['machine_id']
        self.name = all_config['name']
        self.tag = all_config['tag']
        self.base_url = all_config['host'].strip('/') + ":%s" % all_config['port'] + '/'
        self.limit_process = all_config['limit_process']

    # 获取一个job
    def get_job(self):
        try:
            data_all = requests.get(self.base_url + 'get_job', cookies=self.cookies, timeout=3).json()
        except Exception as e:
            logging.error(('获取任务失败', e))
            return 1
        data = data_all['data']
        if data_all['status'] == 1:
            logging.info("开启了 %s 的任务" % data['job_type'])
            if self.check_job_file(job_type=data['job_type']) == 0:
                self.get_job_file(job_type=data['job_type'])
                self.unzip_file(job_type=data['job_type'])
                logging.info("获取了一个任务 %s" % data['job_type'])
            self.run(data)
        return data

    # 检测job文件是否更新
    def check_job_file(self, job_type):
        # 返回 0 需要更新， 1 不需要更新
        if not os.path.exists("jobs/" + job_type):
            return 0
        version = json.loads(open("jobs/" + job_type + '/.info').read()).get('version', -1)
        check_job_file_url = self.base_url + 'check_job_file_status?job_type=' + job_type
        check_job_file_url = check_job_file_url + '&version=' + str(version)
        flag = 0
        for i in range(5):
            try:
                result = requests.get(check_job_file_url, timeout=3).json()
                flag = 1
                break
            except Exception as e:
                logging.error(('check_job_file', i, e))
        if flag == 0:
            return 0
        # status 为 1文件需要更新， -2 文件不存在 ，0 文件不需要更新
        if result['status'] == 0:
            return 1
        return 0

    # 获取job_file
    def get_job_file(self, job_type):
        logging.info("获取的程序文件 %s" % job_type)
        file_name = 'jobs/' + job_type + '.zip'
        data_url = self.base_url + 'get_job_file?job_type=' + job_type
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
                tmp_file_0 = os.path.join(file_path, tmp_file)
                if os.path.exists(tmp_file_0):
                    os.remove(tmp_file_0)
                fz.extract(tmp_file, file_path)
        else:
            logging.error("This is not zip")

    # 2. 注册服务器
    def append_machine(self):
        # 更新下参数信息
        self.get_config()
        # 注册服务器，并上传服务器的各种信息, 获取uuid
        url = self.base_url + 'append_machine'
        tmp_data = {'machine_id': self.machine_id, "tag": self.tag, "limit_process": self.limit_process, "name": self.name, "count_process": self.count_process, "status":1}
        machine_info = self.get_machine_info()
        for k, v in machine_info.items():
            tmp_data[k] = v
        flag = 0
        # 限制5次请求
        for i in range(5):
            time.sleep(0.1)
            try:
                res = requests.post(url=url, data=json.dumps(tmp_data), headers=self.headers, cookies=self.cookies, timeout=3)
                flag = 1
                data = res.json()['data']
                break
            except Exception as e:
                logging.error(("上传机器信息错误", e))
        if flag == 0:
            return 0
        # 更新 machine_id
        if self.machine_id == '':
            self.machine_id = data['machine_id']
            self.all_config['machine_id'] = self.machine_id
            self.cookies['machine_id'] = self.machine_id
        # 更新 limit_count
        self.limit_process = data['limit_process']
        self.all_config['limit_process'] = self.limit_process
        # 更新 tag
        self.tag = data['tag']
        self.all_config['tag'] = self.tag
        # 更新任务
        self.update_config()
        return 1

    # 3. 获取服务器的运行状态
    def get_machine_info(self):
        data = {}
        cpu_info = psutil.cpu_percent(interval=1, percpu=True)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        data['cpu_ratio'] = int(sum(cpu_info) / len(cpu_info))
        data['cpu_core'] = len(cpu_info)
        data['memory_used'] = int(memory_info.used / 1000000) # 单位 M
        data['memory_free'] = int(memory_info.free / 1000000) # 单位 M
        data['disk_free'] = int(disk_info.free / 1000000) # 单位 M
        data['disk_used'] = int(disk_info.used / 1000000) # 单位 M
        return data

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
            # 如果状态是-1， 表明存在错误
            if data['status'] == -1:
                logging.error(data)
            if data:
                # 上传数据
                self.upload_data(data)
            gc.collect()
        return data

    # 7. 上传结果
    def upload_data(self, data):
        url = self.base_url + 'update_job'
        flag = 0
        for i in range(5):
            time.sleep(0.1)
            try:
                res = requests.post(url=url, data=json.dumps(data), headers=self.headers, cookies=self.cookies, timeout=3)
                flag = 1
                logging.info("上传数据成功 job_id %s " % data['id'])
                break
            except Exception as e:
                logging.error(('上传数据失败 job_id %s ' % data['id'], flag, data))
        return flag

    # 8. 更新config信息
    def update_config(self):
        w = open('config.json', 'w')
        w.write(json.dumps(self.all_config, indent=2, ensure_ascii=False))
        w.close()

    def work(self):
        self.append_machine()
        while True:
            self.get_result()
            self.append_machine()
            if self.exit_work():
                exit()
            if self.pause_work():
                time.sleep(30)
                continue
            if self.count_process < self.limit_process:
                logging.info("总体任务 %s，完成任务 %s，运行任务 %s" % (self.count_all_job,
                    self.count_done_job, self.count_process))
                self.get_job()
                time.sleep(0.1)
            else:
                # 任务满载
                time.sleep(30)


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

    def exit_work(self):
        # 退出work
        if os.path.exists("End"):
            logging.info("退出了work")
            os.remove('./End')
            return True
        else:
            return False

    def pause_work(self):
        # 暂停work
        if os.path.exists("Pause"):
            logging.info("暂停 work 30秒")
            time.sleep(30)
            return True
        else:
            return False

    def test_post(self):
        res = requests.post('http://httpbin.org/post', data=json.dumps({"a":1}), headers=self.headers, cookies=self.cookies)
        print(res.json())
if __name__ == '__main__':
    tmp = controller()
    #print(tmp.get_machine_info())
    #print(tmp.test_post())
    tmp.work()
    '''
    while True:
        time.sleep(5)
        data = tmp.get_job()
        print(data)
        if not data.get('id'):
            continue
        tmp.assign_job(data)
    '''
