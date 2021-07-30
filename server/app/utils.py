import os
import sys
import json
import time
import decimal
import zipfile
import datetime
import sqlalchemy
from app import app
from app.models import Jobs
from app.env import JOBS_DIR, JOB_CALLBACK, logging
from multiprocessing import Process, Queue
# 解压数据到指定文件
def unzip_file(zip_path, dir_path):
    """
    解压到指定文件夹
    :param zip_path: 压缩文件路径+名称 /p/a/t/h/job.zip
    :param dir_path     解压文件目标路径
    return: 无
    """
    zip = zipfile.ZipFile(zip_path, "r", zipfile.ZIP_DEFLATED)
    for file in zip.namelist():
        zip.extract(file, dir_path)

# 解析数据为json格式
def parse_data_to_json(data):
    flag = 0
    if type(data) is dict:
        return data
    try:
        data = json.loads(data)
        return data
    except:
        pass
    try:
        data = eval(data)
        return data
    except:
        pass
    return 0

# 将fetchall 返回的list 转换为 json list
def convert_rowproxy_to_dict(data):
    return_data = []
    for line in data:
        tmp_dict = {}
        if isinstance(line, sqlalchemy.engine.result.RowProxy):
            all_keys = line.keys()
            for i in range(len(all_keys)):
                k = all_keys[i]
                v = line[i]
                if isinstance(v, decimal.Decimal):  # for decimal
                    v = float(v)
                if isinstance(v, datetime.datetime):  # for datetime
                    v = v.strftime("%Y-%m-%d %H:%M:%S")
                tmp_dict[k] = v
        else:
            tmp_dict = line.to_json()
        return_data.append(tmp_dict)
    return return_data

# 将附件打包成zip 注意地址要取绝对路径
def zip_job_file(job_type):
    job_path = os.path.join(JOBS_DIR, job_type)
    zip_file_name = job_path + '.zip'
    if os.path.exists(zip_file_name):
        os.remove(zip_file_name)
    with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for tmp_file in os.listdir(job_path):
            if tmp_file != '__pycache__' and "return_main" not in tmp_file:
                with open(os.path.join(job_path, tmp_file), 'rb') as fp:
                    zf.writestr(tmp_file, fp.read())
    return zip_file_name

# 对 return_data 进行处理
def operate_return_data(data, queue):
    import os
    import sys
    import importlib
    import requests
    import time
    import json
    job_path = os.path.join(JOBS_DIR, str(data['job_type']))
    os.chdir(job_path)
    sys.path.append('./')
    result = data
    begin_time = time.time()
    try:
        main = importlib.import_module('return_main')  # 绝对导入
        #tmp_result = main.work(data['return_data'])
        tmp_result = 1
        result['result'] = str(result['result']) + '\n' + str(tmp_result)
        result['status'] = 3
    except Exception as e:
        result['result'] = str(result['result']) + '\n error:' + str(e)
        result['status'] = -2
    end_time = time.time()
    result['spend_time'] += (end_time - begin_time)
    queue.put(result)

# 开始任务
def callback_job(n=2):
    from app.jobs.proc import update_job_status
    queue_0 = Queue(999)
    count_process = 0
    limit_process = n
    run_job = {}
    while True:
        if limit_process == count_process:
            time.sleep(1)
        # 获取结果
        if queue_0.qsize() > 0:
            result = queue_0.get()
            job_id = result["id"]
            # 判断 任务 状态
            # 任务完成 就不需要 return_data 了
            if result["status"] == 3:
                result["return_data"] = ""
                logging.info("任务ID: %s, 回调任务运行成功" % result['id'])
            if result["status"] == -2:
                logging.error("任务ID: %s, 任务运行失败，错误信息: %s" % (result['id'], result['result']))
            # 更新任务状态
            update_job_status(result)
            count_process -= 1
            del run_job[job_id]
        # 添加任务
        if count_process < limit_process:
            all_jobs = Jobs.query.filter(Jobs.status==JOB_CALLBACK).limit(n).all()
            for tmp_job in all_jobs:
                job_id = tmp_job.id
                if job_id in run_job:
                    continue
                # 添加任务
                data = tmp_job.to_json()
                data['return_data'] = parse_data_to_json(data['return_data'])
                logging.info("任务ID: %s, 添加回调任务, 类型 %s" %(data['id'], data['job_type']))
                p = Process(target=operate_return_data, args=(data, queue_0))
                p.dameon = False
                p.start()
                run_job[job_id] = 1
                count_process += 1
    return data



if __name__ == "__main__":
    print(1)
