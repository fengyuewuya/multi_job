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
        self.cookies = {}
        self.platform = self.get_platform()
        # status = 1 表示正在运行 0 暂停 -1 关机
        self.status = 1
        # 初始化 运行参数
        self.get_config()
        # 记录运行情况
        self.count_process = 0
        self.count_done_job = 0
        self.count_all_job = 0
        self.job_process = {}
        # 记录网络参数
        self.headers = {'Content-Type': 'application/json'}
        self.cookies = {"machine_id":self.machine_id, "tag":self.tag}

    def get_url(self, url, **kwargs):
        # 封装的requests, get, 防止请求失败 导致程序挂
        url = self.base_url + url
        for i in range(5):
            time.sleep(i * i + 0.01)
            try:
                res = requests.get(url, params=kwargs, cookies=self.cookies, timeout=3)
                return res.json()
            except Exception as e:
                logging.error("get url %s error: %s" % (url, str(e)))
        return {}

    def post_url(self, url, json_data):
       # 封装的requests, post, 防止请求失败 导致程序挂
        url = self.base_url + url
        for i in range(5):
            time.sleep(i * i + 0.01)
            try:
                res = requests.post(url, json=json_data, headers=self.headers, cookies=self.cookies, timeout=3)
                return res.json()
            except Exception as e:
                logging.error("post url %s error: %s" % (url, str(e)))
        return {}

   # 获取 config 信息
    def get_config(self):
        all_config = json.loads(open(self.config).read())
        self.all_config = all_config
        self.machine_id = all_config['machine_id']
        self.name = all_config['name']
        self.tag = all_config['tag']
        self.base_url = all_config['host'].strip('/') + ":%s" % all_config['port'] + '/'
        self.limit_process = all_config['limit_process']

    # 获取一个job, 并获取需要进行处理的任务
    def get_job(self):
        data_all = self.get_url(url='get_job', timeout=3)
        if not data_all or 'data' not in data_all:
            logging.error(('获取任务失败'))
            return -1
        data = data_all.get('data', {})
        operation_id = data_all.get('operation_id', [])
        # 对任务进行操作
        if operation_id:
            for tmp_id in operation_id:
                if  tmp_id in self.job_process:
                    self.job_process[tmp_id].kill()
                    self.job_process.pop(tmp_id)
                    self.count_process -= 1
                    logging.info("关闭了一个任务 %s" % tmp_id)
                tmp_data = {"id":tmp_id, "status":-1}
                self.upload_data(tmp_data)
        # 开启新的任务
        if data:
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
        #check_job_file_url = self.base_url + 'check_job_file_status?job_type=' + job_type
        #check_job_file_url = check_job_file_url + '&version=' + str(version)
        params = {"job_type":job_type, "version":str(version)}
        result = self.get_url(url='check_job_file_status', params=params)
        if not result or 'status' not in result:
                logging.error('check_job_file failed')
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
        # 尝试下载5次文件，不成功的话 开启任务也会报错 输出报错日志
        for i in range(5):
            try:
                res = requests.get(data_url)
                with open(file_name, "wb") as code:
                    code.write(res.content)
                return 0
            except Exception as e:
                logging.error("下载任务文件失败 %s" % str(e))

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
        url = 'append_machine'
        tmp_data = {'machine_id': self.machine_id,
                "tag": self.tag,
                "name": self.name,
                "status": self.status,
                "platform":self.platform,
                "limit_process": self.limit_process,
                "count_process": self.count_process}
        # 获取cpu等负载信息
        machine_info = self.get_machine_info()
        for k, v in machine_info.items():
            tmp_data[k] = v
        data = self.post_url(url=url, json_data=tmp_data)
        if not data or 'data' not in data:
            return -1
        operation = data['operation']
        data = data['data']
        # 更新machine状态
        flag = 0
        # 更新 machine_id
        if self.machine_id == '':
            self.machine_id = data['machine_id']
            self.all_config['machine_id'] = self.machine_id
            self.cookies['machine_id'] = self.machine_id
            flag = 1
        if operation.get('status') == 1 and 'machine_info' in operation:
            # 更新 limit_count
            if self.limit_process != operation['machine_info'].get('limit_process', self.limit_process):
                self.limit_process = int(str(operation['machine_info']['limit_process']))
                self.all_config['limit_process'] = self.limit_process
                flag = 1
            # 更新 tag
            if self.tag != operation['machine_info'].get('tag', self.tag):
                self.tag = operation['machine_info']['tag'].strip().replace("，", ",")
                self.all_config['tag'] = self.tag
                self.cookies['tag'] = self.tag
                flag = 1
            # 更新name
            if self.name != operation['machine_info'].get('name', self.name):
                self.name = operation['machine_info']['name']
                self.all_config['name'] = self.name
                flag = 1
            # 删除 pause
            if os.path.exists("Pause"):
                os.remove("Pause")
        # 更新config 信息
        if flag == 1:
            self.update_config()
        # 暂停工作
        if operation.get('status') == 0:
            with open('./Pause', 'w') as w:
                w.write(' ')
        # 退出工作
        if operation.get('status') == -1:
            with open('./End', 'w') as w:
                w.write(' ')
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
        self.job_process[data['id']] = p

    # 6. 获取任务结果, 并上传
    def get_result(self):
        data = -1
        if queue_0.qsize() > 0:
            self.count_done_job += 1
            self.count_process -= 1
            data = queue_0.get()
            if data['id'] in self.job_process:
                self.job_process.pop(data['id'])
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
        res = self.post_url(url='update_job', json_data=data)
        if not res:
                logging.error('上传数据失败 job_id %s' % data['id'])
                return -1
        logging.info("上传数据成功 job_id %s " % data['id'])
        return data

    # 8. 更新config信息
    def update_config(self):
        w = open('config.json', 'w')
        w.write(json.dumps(self.all_config, indent=2, ensure_ascii=False))
        w.close()

    # 这是运行的主程序
    def work(self):
        self.append_machine()

        while True:
            job_data = {}
            self.get_result()
            self.append_machine()
            # 停止工作
            if self.exit_work():
                # 删除 pause
                if os.path.exists("Pause"):
                    os.remove("Pause")
                self.status = -1
                self.append_machine()
                exit()
            # 暂停工作
            if self.pause_work():
                self.status = 0
                self.append_machine()
                continue
            else:
                self.status = 1
            if self.count_process < self.limit_process:
                logging.info("总体任务 %s，完成任务 %s，运行任务 %s" % (self.count_all_job,
                    self.count_done_job, self.count_process))
                job_data = self.get_job()
            # 在没有找到job的情况下 或者满载的情况下
            if not job_data:
                time.sleep(30)
            else:
                time.sleep(0.1)

    # 退出work
    def exit_work(self):
        if os.path.exists("End"):
            logging.info("退出了work")
            os.remove('./End')
            return True
        else:
            return False

    # 暂停work
    def pause_work(self):
        if os.path.exists("Pause"):
            logging.info("暂停 work 30秒")
            time.sleep(30)
            return True
        else:
            return False

    # 检测是否可以post
    def test_post(self):
        res = requests.post('http://httpbin.org/post', data=json.dumps({"a":1}), headers=self.headers, cookies=self.cookies)

    # 检测 平台
    def get_platform(self):
        platform = ''
        if sys.platform.startswith("win"):
            platform = 'win'
        if sys.platform.startswith("dar"):
            platform = 'mac'
        if sys.platform.startswith('linux') or sys.platform.startswith('free'):
            platform = 'linux'
        return platform
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
