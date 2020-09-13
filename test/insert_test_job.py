# coding=utf-8
import requests
import json
import time
# 注册任务类型
requests.get("http://127.0.0.1:5006/update_job_file_status", params={"job_type":"test_job"})
#增加任务
for i in range(100):
    data = {
     'job_type':'test_job',
     'input_data': {"seed":i},
     'tag':''
    }
    url = 'http://127.0.0.1:5006/insert_job'
    headers = {'Content-Type': 'application/json'} ## headers中添加上content-type这个参数，指定为json格式
    time.sleep(0.001)
    ## post的时候，将data字典形式的参数用json包转换成json格式。
    try:
        res = requests.post(url=url, headers=headers, data=json.dumps(data), timeout=3)
    except:
        pass
