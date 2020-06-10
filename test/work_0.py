# coding=utf-8
import requests
import json
import time
import pymysql
conn = pymysql.connect(host='localhost', user='root', password='xczg7798', db='1688')
cursor = conn.cursor()
cursor.execute("select shop_id from shop_id WHERE member_id = '' ")
all_data = [k[0] for k in cursor.fetchall()]
list_tmp = []
for i in range(len(all_data)):
    list_tmp.append(all_data[i])
    if i != 0 and i % 1000 == 0:
        data = {
         'job_type':'get_member_id',
         'input_data': list_tmp
        }
        url = 'http://127.0.0.1:5006/insert_job'
        headers = {'Content-Type': 'application/json'} ## headers中添加上content-type这个参数，指定为json格式
        time.sleep(0.2)
        res = requests.post(url=url, headers=headers, data=json.dumps(data)) ## post的时候，将data字典形式的参数用json包转换成json格式。
        list_tmp = []

data = {
 'job_type':'get_member_id',
 'input_data': list_tmp
}
url = 'http://127.0.0.1:5006/insert_job'
headers = {'Content-Type': 'application/json'} ## headers中添加上content-type这个参数，指定为json格式
time.sleep(0.2)
res = requests.post(url=url, headers=headers, data=json.dumps(data)) ## post的时候，将data字典形式的参数用json包转换成json格式。
