import os
import json
import decimal
import zipfile
import datetime
import sqlalchemy
from app import app
from app.env import JOBS_DIR
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
