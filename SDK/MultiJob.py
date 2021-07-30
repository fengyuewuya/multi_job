#coding=utf-8
import os
import sys
import time
import json
import zipfile
import requests
import importlib
from urllib.parse import urljoin

class MultiJob(object):
    def __init__(self, base_url="", username="", password=""):
        self.base_url = base_url
        self.username = ""
        self.__password = password
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.job_dir = os.path.join(self.base_dir, "jobs")
        self.cwd_dir = os.getcwd()
        self.main = None
        self.return_main = None
        self.limit_count = 1
        self.priority = 0
        self.batch = ""
        self.tag = ""
        sys.path.append('./')
        pass

    # 从 config.json 获取参数信息
    def load_config_from_json(self, json_path):
        json.loads()
        pass

    # 设定 base_url
    def set_base_url(self, base_url):
        self.base_url = base_url
        pass

    # 设定 user_name(self, username, password)
    def set_username(self, username, password):
        self.username = username
        self.__password = password
        pass

    # 用户登录
    def login(self):
        pass

    # get 请求
    def __get_url(self, url, retry=5, **kwargs):
        # 封装的requests, get, 防止请求失败 导致程序挂
        url = urljoin(self.base_url, url)
        for i in range(retry):
            time.sleep(i + 0.1)
            try:
                res = requests.get(url, params=kwargs, timeout=3)
                return res.json()
            except Exception as e:
                print("get url %s error: %s" % (url, str(e)))
        return {}

    # 封装的requests, post, 防止请求失败 导致程序挂
    def __post_url(self, url, retry=5, headers={'Content-Type': 'application/json'}, **kwargs):
        url = urljoin(self.base_url, url)
        json_data = kwargs
        for i in range(retry):
            time.sleep(i + 0.1)
            try:
                res = requests.post(url, json=json_data, headers=headers, timeout=3)
                return res.json()
            except Exception as e:
                print("post url %s error: %s" % (url, str(e)))
        return {}

    #  设定 任务类型
    def set_batch(self, batch):
        self.batch = batch
        return 1

    #  设定 任务类型
    def set_tag(self, tag):
        self.tag = tag
        return 1

    #  设定 优先级 0-9999 越大优先级越高
    def set_priority(self, priority=0):
        self.priority = priority
        return 1

    #  设定 重试次数
    def set_limit_count(self, limit_count=1):
        self.limit_count = limit_count
        return 1

    #  设定 任务类型
    def set_tag(self, tag):
        self.tag = tag
        return 1

    # 插入一个任务
    def insert_job(self, job_type, *args, **kwargs ):
        input_data = {}
        input_data['args'] = args
        input_data['kwargs'] = kwargs
        url = "jobs/insert_job"
        result = self.__post_url(url, job_type=job_type, input_data=input_data, batch=self.batch, tag=self.tag, limit_count=self.limit_count, priority=self.priority)
        if "code" not in result:
            return -1
        if result:
            job_id = result['data']['job_id']
        return job_id


    # 停止 Job
    def kill_job(self, job_id=None, job_type=None, machine_id=None, batch=None):
        if not (job_id or job_type or machine_id or batch):
            return 0
        url = "jobs/kill_job"
        result = self.__post_url(url, job_id=job_id, job_type=job_type, machine_id=machine_id, batch=batch)
        if not result:
            return 0
        if result.get('code') == 200:
            return 1

    # 删除 Job 正在运行中的任务状态为1 是无法删除的
    def delete_job(self, job_id=None, job_type=None, machine_id=None, batch=None):
        if not (job_id or job_type or machine_id or batch):
            return 0
        url = "jobs/delete_job"
        result = self.__post_url(url, job_id=job_id, job_type=job_type, machine_id=machine_id, batch=batch)
        if not result:
            return 0
        if result.get('code') == 200:
            return 1

    # 重跑任务 正在运行(状态为1)和排队中的任务(状态为0)无法 rerun
    def rerun_job(self, job_id=None, job_type=None, machine_id=None, batch=None):
        if not (job_id or job_type or machine_id or batch):
            return 0
        url = "jobs/rerun_job"
        result = self.__post_url(url, job_id=job_id, job_type=job_type, machine_id=machine_id, batch=batch)
        if not result:
            return 0
        if result.get('code') == 200:
            return 1
        pass

    # 将旧任务复制一个新的任务 并且设定状态为排队中
    def copy_job(self, job_id=None, job_type=None, machine_id=None, batch=None):
        if not (job_id or job_type or machine_id or batch):
            return 0
        url = "jobs/copy_job"
        result = self.__post_url(url, job_id=job_id, job_type=job_type, machine_id=machine_id, batch=batch)
        if not result:
            return 0
        if result.get('code') == 200:
            return 1

    # 获取任务信息
    def get_job_detail(self, job_id):
        url = "jobs/get_job_details"
        result = self.__get_url(url, job_id=job_id)
        return result

    # 清理 任务的 result , 减少储存压力
    def clear_job(self, job_id):
        url = "jobs/clear_job"
        result = self.__post_url(url, job_id=job_id)
        return result

    # 获取任务列表信息
    def get_job_list(self, job_type=None, batch=None, offset=0, limit=10, machine_id=None, status=None, clear=None):
        if not (job_type or batch or machine_id or status):
            return 0
        if offset < 0:
            return 0
        if limit < 0:
            return 0
        url = "jobs/get_job_list"
        result = self.__get_url(url, job_type=job_type, batch=batch, offset=offset, limit=limit, machine_id=machine_id, status=status, clear=clear)
        return result

    # 获取任务列表信息
    # 如果batch为-1 表示展现全部的batch信息，只对job_type维度进行聚合分析
    # 如果同时存在 batch 和 job_type 则以两个维度进行聚合分析
    # 如果 只有job_type batch=None 则对 job_type batch的多种情况进行分析
    def get_job_summary(self, job_type=None, batch=None):
        url = "jobs/get_job_summary"
        result = self.__get_url(url, job_type=job_type, batch=batch)
        return result

    # 更新任务类型
    def update_job_file_status(self, job_type, job_path=None):
        # 如果存在job_path 则将本地的 job_path 打包上传
        if job_path:
            zip_file_name = self.zip_file(path=job_path)
            res = self.__upload_job_file(zip_file_name, job_type)
            os.remove(zip_file_name)
        url = "job_file/update_job_file_status"
        result = self.__get_url(url, job_type=job_type)
        return result

    # 获取当前的所有任务类型
    def get_all_job_type(self):
        url = "jobs/get_all_job_type"
        result = self.__get_url(url)
        return result

    # 获取job_file
    def get_job_file(self, job_type):
        os.makedirs(self.job_dir, exist_ok=True)
        file_name = os.path.join(self.job_dir, job_type + '.zip')
        url = "job_file/get_job_file"
        url = urljoin(self.base_url, url)
        # 尝试下载5次文件，不成功的话 开启任务也会报错 输出报错日志
        for i in range(5):
            try:
                res = requests.get(url, params={"job_type":job_type})
                with open(file_name, "wb") as code:
                    code.write(res.content)
                return 1
            except Exception as e:
                print("下载任务文件失败 %s" % str(e))
        return 0

    # 检测job文件是否更新
    def check_job_file_version(self, job_type):
        # 返回 0 需要更新， 1 不需要更新
        file_name = os.path.join(self.job_dir, job_type + ".zip")
        job_path = os.path.join(self.job_dir, job_type)
        if not os.path.exists(job_path):
            print("不存在 %s 文件，等待下载更新!" % job_type)
            return 0
        version = json.loads(open(os.path.join(job_path, '.info')).read()).get('version', -1)
        #check_job_file_url = self.base_url + 'check_job_file_status?job_type=' + job_type
        #check_job_file_url = check_job_file_url + '&version=' + str(version)
        url = 'job_file/check_job_file_status'
        result = self.__get_url(url=url, job_type=job_type, version=str(version))
        if not result or 'data' not in result:
                print("访问失败， %s 等待下载更新!" % job_type)
                return 0
        # status 为 1文件需要更新， -2 文件不存在 ，0 文件不需要更新
        if result['data']['status'] == 0:
            print("%s 版本为最新，无需下载更新!" % job_type)
            return 1
        print("%s 版本过低，等待下载更新!" % job_type)
        return 0

    # 本地加载任务包 job_type 和 job_type 只能同时填一个
    def load_job_file(self, job_type=None, job_path=None):
        if (job_type and job_path):
            return 0
        if not (job_type or job_path):
            return 0
        self.__clear_load_job()
        if job_path:
            job_path = os.path.abspath(job_path)
        if job_type:
            # 等于0 表示版本比较低 需要重新下载更新
            if self.check_job_file_version(job_type) == 0:
                self.get_job_file(job_type)
                self.unzip_file(job_type=job_type)
            job_path = os.path.join(self.job_dir, job_type)
        os.chdir(job_path)
        # 加载 main 的任务文件
        main = importlib.import_module('main')
        self.main = main.work
        # 加载 return_main 的任务文件
        if os.path.exists("return_main"):
            return_main = importlib.import_module('return_main')
            self.return_main = return_main.work
        os.chdir(self.cwd_dir)
        return 1
        """
        main = importlib.import_module('main')  # 绝对导入
        self.job_type = job_type
        self.main = main.work
        self.return_main = return_main.work
        tmp_result = main.work(data)
        """

    # 解压zip文件
    def unzip_file(self, job_type):
        job_type = str(job_type)
        job_path = os.path.join(self.job_dir, job_type)
        file_name = job_path + '.zip'
        if zipfile.is_zipfile(file_name):
            fz = zipfile.ZipFile(file_name, 'r')
            for tmp_file in fz.namelist():
                tmp_file_0 = os.path.join(job_path, tmp_file)
                if os.path.exists(tmp_file_0):
                    os.remove(tmp_file_0)
                fz.extract(tmp_file, job_path)
            os.remove(file_name)
        else:
            print("该文件不是ZIP文件")

    def zip_file(self, path):
        job_path = os.path.abspath(path)
        zip_file_name = job_path + '.zip'
        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zf:
            for tmp_file in os.listdir(job_path):
                if tmp_file != '__pycache__' :
                    with open(os.path.join(job_path, tmp_file), 'rb') as fp:
                        zf.writestr(tmp_file, fp.read())
        return zip_file_name

    # 上传任务文件 zip 格式
    def __upload_job_file(self, zip_path, job_type):
        url = urljoin(self.base_url, "job_file/upload_file")
        files={'file': open(zip_path, 'rb')}
        res = requests.post(url=url, files=files, data={"job_type":job_type})
        return res

    # 清理 load_job后的 main 和 return_main, 及其他参数
    def __clear_load_job(self):
        self.main = None
        self.return_main = None
"""
# 注册任务类型
requests.get("http://127.0.0.1:5006/update_job_file_status", params={"job_type":"test_job"})
#增加任务
for i in range(100):
    data = {
     'job_type':'test_job',
     'input_data': {"seed":i},
     'tag':''
    }
"""
if __name__ == "__main__":
    base_url = "http://127.0.0.1:5006"
    tmp = MultiJob(base_url)
    tmp.load_job_file(job_type="test_job")
    #tmp.load_job_file(job_path="jobs/test_job")
    #print(tmp.main({"input_data":{"seed":1}}))
    # 查看 job 详情
    print(tmp.get_job_detail(2))
    # 查看 job 的列表
    print(tmp.get_job_list(job_type='test_job'))
    # 查看所有的任务类型
    print(tmp.get_all_job_type())
    # 对任务进行统计分析
    print(tmp.get_job_summary(job_type="test_job", batch=-1))
    # 重跑任务
    tmp.rerun_job(job_id=2)
    #tmp.insert_job(1, 2)
    # 加载本地任务
    tmp.load_job_file(job_type='test_job')
    #print(tmp.username)
    #print(tmp.__password)
    """
    # 更新 test_job 的状态
    tmp.update_job_file_status(job_type="test_job")
    # 直接从本地上传文件
    #tmp.update_job_file_status(job_type="test_job", job_path="jobs/test_job/")
    #result = tmp.insert_job(job_type="test_job", input_data={"seed":1}, batch="test")
    #print(result)
    #file_name = tmp.zip_file("jobs/test_job/")
    #print(file_name)
    #result = tmp.upload_job_file(file_name)
    #print(result)
    """
