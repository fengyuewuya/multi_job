# coding=utf-8
from flask import Flask, request, jsonify, json, send_file, g
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
import zipfile
import io
import os
import time
from multiprocess import Process, Queue
import logging, logging.handlers, logging.config
def main():
    all_config = json.load(open("./config.json"))
    host = all_config["host"]
    port = all_config["port"]
    debug = all_config["debug"]
    app.run(host=host, port=port, debug=debug)

base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
# 0. 读取相关配置文件
log_config = json.load(open("./log_config.json"))
all_config = json.load(open("./config.json"))

# 0.1 读取logger 配置
logging.config.dictConfig(log_config)

# 0.2 初始化flask 设置数据库相关信息
app = Flask(__name__)

# 0.2.1 设置数据库相关参数
app.config['SQLALCHEMY_DATABASE_URI'] = all_config['db']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 让返回的json结果显示中文
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)

# 0.2.2 初始化Jobs参数
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

def convert_rowproxy_to_dict(data):
    # 将fetchall 返回的list 转换为 json list
    return_data = []
    for line in data:
        return_data.append(dict((zip(line.keys(), line))))
    return return_data

# 0.2.3 进行表格创建
db.create_all()

# 0.3 设置flask
# 0.3.1 运行状态等信息
global host, port
host = all_config["host"]
port = all_config["port"]
debug = all_config["debug"]
# 0.3.2 设置flask函数
def operate_return_data(data):
    import os
    import sys
    import importlib
    import requests
    import time
    import json
    file_path = 'jobs/' + data['job_type'] + '/'
    os.chdir(file_path)
    sys.path.append('./')
    result = data
    try:
        main = importlib.import_module('return_main')  # 绝对导入
        tmp_result = main.work(data)
        result['result'] = str(result['result']) + '\n' + str(tmp_result)
        result['status'] = 3
        logging.info("operate return data of %s, %s" % (data['job_type'], result['result']))
    except Exception as e:
        result['result'] = str(result['result']) + '\n' + str(e)
        logging.exception("error in open return data , %s" % result['job_id'])
        result['status'] = -2
    url = 'http://localhost:%s/' % port + 'update_job'
    headers = {'Content-Type': 'application/json'}
    result['return_data'] = ''
    res = requests.post(url=url, headers=headers, data=json.dumps(result))

@app.route('/')
def hello_world():
    return 'Hello, World!'

# 获取所有的jobs
@app.route('/get_all_job')
def get_all_job():
    data = []
    for line in Jobs.query.all():
        data.append(line.to_json())
    result = {'data': data}
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
    logging.info("insert a job of %s" % job_type)
    return jsonify(code=200, status=1, message='ok', data=new_job.to_json())

# 检测任务文件的状态 如果状态比较旧就返回 1
@app.route('/check_job_file_status')
def check_job_file_status():
    time_local = request.args.get("local_time", -1)
    time_local = int(time_local)
    job_type = request.args.get("job_type", -1)
    version_file = os.path.join('./', 'jobs', job_type, '.VERSION')
    st_mtime_0 = os.stat(version_file).st_mtime
    # 说明 job 文件已经更新
    if st_mtime_0 > int(time_local):
        return jsonify(code=200, message='ok', status=1)
    else:
        return jsonify(code=200, message='ok', status=-1)

# 检测任务文件的状态 如果状态比较旧就返回 1
@app.route('/update_job_file_status')
def update_job_file_status():
    job_type = request.args.get("job_type", -1)
    job_path = os.path.join('./', 'jobs', job_type)
    version_file = os.path.join(job_path, ".VERSION")
    tmp_time = str(time.time())
    w = open(version_file, 'w')
    w.write(tmp_time)
    w.close()
    return jsonify(code=200, time_now=tmp_time, message='ok', data={})

@app.route('/get_data')
def get_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 将附件打包成zip
    memory_file = io.BytesIO()
    job_type = request.args.get('job_type')
    job_path = os.path.join(base_dir, 'jobs', job_type)
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for tmp_file in os.listdir(job_path):
            if tmp_file != '__pycache__' and "return_main" not in tmp_file:
                with open(os.path.join(job_path, tmp_file), 'rb') as fp:
                    zf.writestr(tmp_file, fp.read())
    memory_file.seek(0)
    return send_file(memory_file, as_attachment=True,
                     attachment_filename=job_type+'.zip',
                     mimetype='application/zip')

# 更新任务状态，为运行成功或者失败
# 任务状态 0 等待分发， 1 运行中， 2 运行成功， -1 运行失败, -2 回调函数计算失败
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
    logging.info("update job status of %s and %s" % (job_id, job_type))
    return jsonify(code=200, status=status, message='ok', data={})

# machine 获取特定job
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

# 随便获取一个job
@app.route('/get_job_info')
def get_job_info():
    job_type = request.args.get('job_type')
    query_0 = Jobs.query
    # 如果存在特定的job_type，就筛选特定的job_type
    if job_type:
        query_0 = query_0.filter_by(job_type=job_type)
    data = query_0.first()
    if data is None:
        return jsonify(code=302, status=0, message='No Job', data='')
    data = data.to_json()
    return jsonify(code=200, status=1, message='ok', data=data)

# 获取job的完成统计情况
@app.route('/get_job_summary')
def get_job_summary():
    res = db.session.execute("select job_type, status, count(1) as job_count from jobs group by job_type, status")
    data = convert_rowproxy_to_dict(res.fetchall())
    return jsonify(code=200, data=data)

# 获取job的完成详情
@app.route('/get_job_details')
def get_job_details():
    #res = db.session.execute("select job_type, status, count(1) as job_count from jobs group by job_type, status")
    res = db.session.execute("select  *,strftime('%s', update_time) - strftime('%s', create_time) as spend_time from jobs where status > 1")
    data = convert_rowproxy_to_dict(res.fetchall())
    return jsonify(code=200, data=data)
if __name__ == '__main__':
    main()
