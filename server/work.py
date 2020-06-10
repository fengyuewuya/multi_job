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
import uuid
def main():
    all_config = json.load(open("./config.json"))
    host = all_config["host"]
    port = all_config["port"]
    debug = all_config["debug"]
    app.run(host=host, port=port, debug=debug)

# 全局一些变量
global host, port, base_dir
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
        return '<job_id %r>' % self.id

    def to_json(self):
        dic_0 = self.__dict__
        if "_sa_instance_state" in dic_0:
            del dic_0["_sa_instance_state"]
        for k, v in dic_0.items():
            if isinstance(v, datetime.datetime):
                dic_0[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return dic_0

# 0.2.3 初始化Job_file参数
class Job_file(db.Model):
    job_type = db.Column(db.String(32), primary_key=True)
    job_file = db.Column(db.String(128))
    version = db.Column(db.Integer, default=0)
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, job_type, job_file):
        self.job_type = job_type
        self.job_file = job_file

    def __repr__(self):
        return '<job_type %r>' % self.job_type

    def to_json(self):
        dic_0 = self.__dict__
        if "_sa_instance_state" in dic_0:
            del dic_0["_sa_instance_state"]
        for k, v in dic_0.items():
            if isinstance(v, datetime.datetime):
                dic_0[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return dic_0

# 0.2.2 初始化Jobs参数
class Machine(db.Model):
    machine_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.Text)
    tag = db.Column(db.Text)
    count_process = db.Column(db.Integer, default=0)
    limit_process = db.Column(db.Integer, default=0)
    cpu_ratio = db.Column(db.Integer, default=0)
    cpu_core = db.Column(db.Integer, default=0)
    memory_used = db.Column(db.Integer, default=0)
    memory_free = db.Column(db.Integer, default=0)
    disk_free = db.Column(db.Integer, default=0)
    disk_used = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=0)
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)
    def __init__(self, machine_id, name, tag, count_process, limit_process, cpu_ratio, cpu_core, memory_used, memory_free, disk_free, disk_used, status):
        self.machine_id = machine_id
        self.name = name
        self.tag = tag
        self.count_process = count_process
        self.limit_process = limit_process
        self.cpu_ratio = cpu_ratio
        self.cpu_core = cpu_core
        self.memory_used = memory_used
        self.memory_free = memory_free
        self.disk_free = disk_free
        self.disk_used = disk_used
        self.status = status

    def __repr__(self):
        return '<machine_id %r>' % self.machine_id

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
host = all_config["host"]
port = all_config["port"]
debug = all_config["debug"]
base_dir = os.path.dirname(os.path.abspath(__file__))
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

def zip_job_file(job_type):
    # 将附件打包成zip
    base_dir = os.path.dirname(os.path.abspath(__file__))
    #memory_file = io.BytesIO()
    job_path = os.path.join(base_dir, 'jobs', job_type)
    zip_file_name = job_path + '.zip'
    with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for tmp_file in os.listdir(job_path):
            if tmp_file != '__pycache__' and "return_main" not in tmp_file:
                with open(os.path.join(job_path, tmp_file), 'rb') as fp:
                    zf.writestr(tmp_file, fp.read())
    #memory_file.seek(0)
    return zip_file_name

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

    input_data = str(data.get('input_data', ''))
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
    local_version = int(request.args.get("version", -1))
    job_type = request.args.get("job_type", -1)
    tmp_job_file = Job_file.query.filter_by(job_type=job_type).first()
    if not tmp_job_file:
        # 说明不存在该 jobs_type
        return jsonify(code=200, message='ok', status=-2)
    if tmp_job_file.version > local_version:
        # 说明 job 文件已经更新
        return jsonify(code=200, message='ok', status=1)
    else:
        # 说明 job 文件没更新
        return jsonify(code=200, message='ok', status=0)

# 更新job_file 状态
@app.route('/update_job_file_status')
def update_job_file_status():
    job_type = request.args.get("job_type", -1)
    job_type = str(job_type)
    job_path = os.path.join('./', 'jobs', job_type)
    tmp_job_file = Job_file.query.filter_by(job_type=job_type).first()
    version = 0
    if tmp_job_file:
        tmp_job_file.version = tmp_job_file.version + 1
        version = tmp_job_file.version
    else:
        tmp_job_file = Job_file(job_type, job_path)
    db.session.merge(tmp_job_file)
    db.session.commit()
    info_file = os.path.join(job_path, ".info")
    w = open(info_file, 'w')
    w.write(json.dumps({"version":version,"time":int(time.time())}))
    w.close()
    zip_job_file(job_type)
    return jsonify(code=200, message='ok', version=version)

# 获取 job的file文件, zip格式
@app.route('/get_job_file')
def get_job_file():
    if 'job_type' not in request.args:
        return jsonify(code=203, message='error')
    job_type = request.args.get('job_type')
    job_file = os.path.join(base_dir, 'jobs', job_type + '.zip')
    job_file_name = job_type + '.zip'
    return send_file(job_file, as_attachment=True,
                     attachment_filename=job_file_name,
                     mimetype='application/zip')

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
    zip_file_name = job_type+'.zip'
    return zip_file_name
    #return send_file(memory_file, as_attachment=True,
    #                 attachment_filename=job_type+'.zip',
    #                 mimetype='application/zip')

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
    if status == -1:
        logging.error(result)
    db.session.commit()
    logging.info("update job status of %s" % (job_id))
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
    job_type = request.args.get('job_type', -1)
    mysql_1 = ''
    if job_type != -1:
        mysql_1 = " where job_type = '%s' " % job_type
    mysql_0 = "select job_type, status, count(1) as count_job, sum(return_count) as all_count, avg(return_count) as return_count, max(update_time) as update_time, round(avg(strftime('%s', update_time) - strftime('%s', create_time)), 2)  as spend_time from jobs"
    mysql_2 = " group by job_type, status"
    mysql_0 = mysql_0 + mysql_1 + mysql_2
    res = db.session.execute(mysql_0)
    data = convert_rowproxy_to_dict(res.fetchall())
    return jsonify(code=200, data=data)

# 获取job的完成详情
@app.route('/get_job_details')
def get_job_details():
    #res = db.session.execute("select job_type, status, count(1) as job_count from jobs group by job_type, status")
    res = db.session.execute("select  *,strftime('%s', update_time) - strftime('%s', create_time) as spend_time from jobs where status > 1")
    data = convert_rowproxy_to_dict(res.fetchall())
    return jsonify(code=200, data=data)

# 增加machine信息
@app.route('/append_machine', methods=["POST"])
def append_machine():
    data = json.loads(request.data)
    return_data = {}
    if data['machine_id'] == '':
        data['machine_id'] = uuid.uuid1().hex
        return_data['machine_id'] = uuid.uuid1().hex
    machine_id = data['machine_id']
    name = data['name']
    tag = data['tag']
    count_process = data['count_process']
    limit_process = data['limit_process']
    cpu_ratio = data.get('cpu_ratio', -1)
    cpu_core = data.get('cpu_core', -1)
    memory_used = data.get('memory_used', -1)
    memory_free = data.get('memory_free', -1)
    disk_free = data.get('disk_free', -1)
    disk_used = data.get('disk_used', -1)
    status = data.get('status', 1)
    new_machine = Machine(machine_id, name, tag, count_process, limit_process,
            cpu_ratio, cpu_core, memory_used, memory_free, disk_free,
            disk_used, status)
    # merge 如果存在就更新数据 ，不存在的话就插入新的数据
    db.session.merge(new_machine)
    db.session.commit()
    return jsonify(code=200, data=return_data)

# 增加machine信息
@app.route('/get_machine_info', )
def get_machine_info():
    res = db.session.execute("select *  from Machine")
    data = convert_rowproxy_to_dict(res.fetchall())
    return jsonify(code=200, data=data)
if __name__ == '__main__':
    main()
