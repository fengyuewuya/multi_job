# coding=utf-8
from flask import Flask, request, jsonify, json, send_file
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
import zipfile
import io
import os
from multiprocess import Process, Queue
app = Flask(__name__)
# 设置数据库相关信息
config_all = json.load(open("./config.json"))
app.config['SQLALCHEMY_DATABASE_URI'] = config_all['db']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# 初始化Jobs参数
class Jobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.Text)
    input_data = db.Column(db.Text)
    params = db.Column(db.Text)
    limit_count = db.Column(db.Integer, default=1)
    status = db.Column(db.Integer, default=0)
    return_count = db.Column(db.Integer, default=0)
    result = db.Column(db.Text, default='')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, job_type, input_data, params, limit_count=1, status=1, return_count=1, result=''):
        self.job_type = job_type
        self.input_data = input_data
        self.params = params
        self.limit_count = limit_count
        self.status = status
        self.return_count = return_count
        self.result = result

    def __repr__(self):
        return '<User %r>' % self.username

    def to_json(self):
        dic_0 = self.__dict__
        if "_sa_instance_state" in dic_0:
            del dic_0["_sa_instance_state"]
        for k, v in dic_0.items():
            if isinstance(v, datetime.datetime):
                dic_0[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return dic_0

def operate_return_data(data):
    import os
    import sys
    import importlib
    import requests
    import time
    import json
    time.sleep(10)
    file_path = 'jobs/' + data['job_type'] + '/'
    os.chdir(file_path)
    sys.path.append('./')
    result = data
    try:
        main = importlib.import_module('main')  # 绝对导入
        tmp_result = main.operate_return_data(data)
        result['result'] = str(result['result']) + '\n' + str(tmp_result)
    except Exception as e:
        result['result'] = str(result['result']) + '\n' + str(e)
    url = 'http://localhost:5000/' + 'update_job'
    headers = {'Content-Type': 'application/json'}
    result['return_data'] = ''
    result['status'] = 3
    res = requests.post(url=url, headers=headers, data=json.dumps(result))
    print(res.text)

# 1. 进行一些前置操作
# create_tables(db)
db.create_all()
@app.route('/')
def hello_world():
    return 'Hello, World!'


# 获取所有的jobs
@app.route('/get_all_job')
def get_all_job():
    data = []
    for line in Jobs.query.all():
        data.append(line.to_json())
    print(data
          )
    result = {'data': data}
    #return json.dumps(result, indent=4)
    return jsonify(code=200, result=result)

# 插入一条jobs
@app.route('/insert_job', methods=['POST'])
def insert_job():
    data = json.loads(request.data)
    job_type = data.get('job_type', '')
    if len(str(job_type)) <= 1:
        return jsonify(code=300, status=0, message='failed', data='job_type not found')
    input_data = data.get('input_data', '')
    params = data.get('params', '')
    limit_count = data.get('limit_count', 1)
    new_job = Jobs(job_type, input_data, params, limit_count, 0)
    db.session.add(new_job)
    db.session.commit()
    return jsonify(code=200, status=1, message='ok', data=new_job.to_json())

# 下载数据
@app.route('/get_data')
def get_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 将附件打包成zip
    memory_file = io.BytesIO()
    job_type = request.args.get('job_type')
    job_path = os.path.join(base_dir, 'jobs', job_type)
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for tmp_file in os.listdir(job_path):
            if tmp_file != '__pycache__':
                with open(os.path.join(job_path, tmp_file), 'rb') as fp:
                    zf.writestr(tmp_file, fp.read())
    memory_file.seek(0)
    return send_file(memory_file, as_attachment=True,
                     attachment_filename=job_type+'.zip',
                     mimetype='application/zip')

# 更新任务状态，为运行成功或者失败
# 任务状态 0 等待分发， 1 运行中， 2 运行成功， -1 运行失败
@app.route('/update_job',  methods=['POST'])
def update_job():
    data = json.loads(request.data)
    job_id = data.get('id')
    status = data.get('status', -1)
    return_count = data.get('count', 0 if status < 0 else 1)
    result = data.get('result', '')
    result = str({'result':result})
    return_data = data.get('return_data', '')
    if not job_id:
        return jsonify(code=300, status=-1, message='failed', data={})
    # 进行回调操作
    if status == 2:
        if return_data != '' :
            p = Process(target=operate_return_data, args=(data, ))
            p.dameon = False
            p.start()
        else:
            status = 3
    Jobs.query.filter_by(id=job_id).update({'status':status, 'return_count':return_count, 'result':result})
    db.session.commit()
    return jsonify(code=200, status=status, message='ok', data={})

# 获取所有的jobs
@app.route('/get_job')
def get_job():
    job_type = request.args.get('job_type')
    query_0 = Jobs.query.filter_by(status=0)
    # 如果存在特定的job_type，就筛选特定的job_type
    if job_type:
        query_0 = query_0.filter_by(job_type=job_type)
    data = query_0.order_by('create_time').first()
    if data is None:
        return jsonify(code=302, status=0, message='No Job', data='')
    data = data.to_json()
    # 对该id的任务便跟状态为2
    Jobs.query.filter_by(id=data['id']).update({'status':1})
    db.session.commit()
    return jsonify(code=200, status=1, message='ok', data=data)

# 如果当前这个文件是作为入口程序运行，那么久执行app.run()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
