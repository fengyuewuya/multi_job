# coding=utf-8
import requests
import json
import time
for line in f:
    data = {
     'job_type':'get_test',
     'input_data': line.strip()
    }
    url = 'http://127.0.0.1:5005/insert_job'
    headers = {'Content-Type': 'application/json'} ## headers中添加上content-type这个参数，指定为json格式
    time.sleep(0.2)
    res = requests.post(url=url, headers=headers, data=json.dumps(data)) ## post的时候，将data字典形式的参数用json包转换成json格式。
