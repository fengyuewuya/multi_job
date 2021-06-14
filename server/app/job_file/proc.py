from app import db
from app import app
from app.env import JOBS_DIR
from app.models import JobFile
import app.utils as utils
import os
import time
import json

# 更新任务文件的版本信息
def update_job_file_version(job_type, version=0):
    job_path = os.path.join(JOBS_DIR, job_type)
    info_file = os.path.join(job_path, ".info")
    w = open(info_file, 'w')
    w.write(json.dumps({"version":version, "time":int(time.time())}, indent=2))
    w.close()
    # 压缩任务文件 并删除老文件
    utils.zip_job_file(job_type)
    return 1

