# coding=utf-8
from copy import deepcopy
from flask import Flask, request, jsonify, json, send_file, g
from flask_sqlalchemy import SQLAlchemy
from flask_docs import ApiDoc
from werkzeug.utils import secure_filename
from sqlalchemy import and_, or_, UniqueConstraint
import datetime
import json
import zipfile
import io
import os
import time
from multiprocess import Process, Queue
import logging, logging.handlers, logging.config
import uuid
import decimal
import sqlalchemy
from flask_cache import Cache
from werkzeug.utils import secure_filename
# 改变全局的路径
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

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

# server flask服务运行的主程序
def main():
    all_config = json.load(open("./config.json"))
    host = all_config["host"]
    port = all_config["port"]
    debug = all_config["debug"]
    app.run(host=host, port=port, debug=debug, threaded=True)

# 0. 读取相关配置文件
log_config = json.load(open("./log_config.json"))
all_config = json.load(open("./config.json"))
port = all_config['port']

# 0.1 读取logger 配置
logging.config.dictConfig(log_config)

# 0.2 初始化flask 设置数据库相关信息
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'}, with_jinja2_ext=False)
app.config['UPLOAD_FOLDER'] = "./static/upload/"
app.config['STATIC_URL_PATH'] = ""

# 0.3 设定api docs相关信息
app.config['JOBS_FOLDER'] = "./static/jobs/"
app.config['API_DOC_MEMBER'] = ['insert_job']
ApiDoc(app)

# 0.2.1 设置数据库相关参数
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False                          # 是否显示mysql配置
app.config['SQLALCHEMY_DATABASE_URI'] = all_config['db']                      # 数据库的连接配置
if 'mysql' in all_config['db']:
    app.config['SQLALCHEMY_POOL_SIZE'] = all_config.get('SQLALCHEMY_POOL_SIZE', 100)  # 数据库连接的数量
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = all_config.get('SQLALCHEMY_MAX_OVERFLOW', -1) # 配置数据库超负载的链接数 -1表示不限制。如果是int的话，可能会触发爆内存bug
app.config['JSON_AS_ASCII'] = False                                           # 让返回的json结果显示中文
db = SQLAlchemy(app)

# 0.2.2 初始化Jobs表的相关参数
class Jobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(64), index=True)
    priority = db.Column(db.Integer, default=0)
    input_data = db.Column(db.Text)
    machine_id = db.Column(db.String(64), index=True)
    limit_count = db.Column(db.Integer, default=1)
    tag = db.Column(db.Text)
    status = db.Column(db.Integer, default=0)
    return_count = db.Column(db.Integer, default=0)
    result = db.Column(db.Text, default='')
    spend_time = db.Column(db.Integer)
    batch = db.Column(db.String(64), index=True) # 生产批次
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)
    UniqueConstraint('job_type', 'batch', name='job_type_batch')

    def __init__(self, job_type, input_data, limit_count=1, tag='', status=1, return_count=1, result='', spend_time=0, batch='', priority=0):
        self.job_type = job_type
        self.input_data = input_data
        self.limit_count = limit_count
        self.tag = tag
        self.status = status
        self.return_count = return_count
        self.result = result
        self.spend_time = spend_time
        self.priority = priority
        if batch == '':
            batch = time.strftime("%Y-%m-%d", time.localtime())
        self.batch = batch

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

# 0.2.2 初始化 machine 表的参数
class Machine(db.Model):
    machine_id = db.Column(db.String(128), primary_key=True)
    platform = db.Column(db.String(128))
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
    def __init__(self, machine_id, name, tag, count_process, limit_process, cpu_ratio, cpu_core, memory_used, memory_free, disk_free, disk_used, status, platform):
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
        self.platform = platform

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

# 0.2.3 进行表格创建
db.create_all()

machine_operation = {}
# 0.2.4 设置一些常用函数
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

# 对 return_data 进行处理
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
        logging.exception("error in open return data , %s" % result['id'])
        result['status'] = -2
    url = 'http://localhost:%s/' % port + 'update_job'
    headers = {'Content-Type': 'application/json'}
    result['return_data'] = ''
    res = requests.post(url=url, headers=headers, data=json.dumps(result))

# 压缩 job 文件
def zip_job_file(job_type):
    # 将附件打包成zip
    base_dir = os.path.dirname(os.path.abspath(__file__))
    #memory_file = io.BytesIO()
    job_path = os.path.join(base_dir, app.config['JOBS_FOLDER'], job_type)
    zip_file_name = job_path + '.zip'
    with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for tmp_file in os.listdir(job_path):
            if tmp_file != '__pycache__' and "return_main" not in tmp_file:
                with open(os.path.join(job_path, tmp_file), 'rb') as fp:
                    zf.writestr(tmp_file, fp.read())
    #memory_file.seek(0)
    return zip_file_name

# 0.3 设置flask
# 0.3.1 设置flask函数
@app.route('/')
def hello_world():
    return 'This is Multi-job!'

 # 首页
@app.route('/home')
def home():
    return send_file("static/index.html")

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
    """Del some data

    @@@
    #### args

    | args | nullable | type | remark |
    |--------|--------|--------|--------|
    |    title    |    false    |    string   |    blog title    |
    |    name    |    true    |    string   |    person's name    |

    #### return
    - ##### json
    > {"msg": "success", "code": 200}
    @@@
    """
    data = json.loads(request.data)
    job_type = data.get('job_type', '')
    if len(str(job_type)) <= 1:
        return jsonify(code=300, status=0, message='failed', data='job_type not found')
    input_data = str(data.get('input_data', ''))
    # 可跑的机器标签
    tag = data.get('tag')
    if not tag:
        tag = job_type
    # 重跑次数
    limit_count = data.get('limit_count')
    if not limit_count:
        limit_count = 0
    # 任务批次
    batch = data.get('batch', '')
    # 任务优先级 越大越优先
    priority = data.get('priority')
    if not priority:
        priority = 0
    status = 0
    new_job = Jobs(job_type, input_data, limit_count, status=status, tag=tag, batch=batch, priority=priority)
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
    job_path = os.path.join(app.config['JOBS_FOLDER'], job_type)
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


# 删除job_type_file
@app.route('/delete_job_file')
def delete_job_file():
    job_type = request.args.get("job_type", -1)
    if not job_type:
        return jsonify(code=301, message='no job_type', data={})
    job_type = str(job_type)
    tmp_query = Job_file.query.filter_by(job_type=job_type)
    tmp_query.delete(synchronize_session=False)
    db.session.commit()
    return jsonify(code=200, message='delete success', data={})

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

# 下载job相关的文件
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
    status = data.get('status')
    # 判断 job_id 和 status 是否存在
    if not job_id or not status:
        return jsonify(code=300, status=-1, message='failed', data={})
    tmp_job = Jobs.query.filter_by(id=job_id).first()
    if not tmp_job:
        return jsonify(code=300, status=-1, message='failed', data={})
    return_count = data.get('count', 0 if status < 0 else 1)
    result = str(data.get('result', ''))
    #result = str({'result':result})
    spend_time = data.get('spend_time', -1)
    return_data = data.get('return_data', '')
    # 进行回调操作
    if status == 2:
        if return_data != '' :
            try:
                return_data = eval(return_data)
                data['return_data'] = return_data
            except:
                pass
            p = Process(target=operate_return_data, args=(data, ))
            p.dameon = False
            p.start()
        else:
            status = 3
    if status == -1:
        logging.error(result)
    # 任务失败的话 如果limit_count > 0 说明有重跑的机会, 进行重跑
    # 没有重跑机会 就更新数据库相关结果
    if int(status) < 0 and tmp_job.limit_count > 0:
        tmp_job.status = 0
        tmp_job.limit_count -= 1
    else:
        res = Jobs.query.filter_by(id=job_id).update({'status':status, 'return_count':return_count, 'result':result, 'spend_time':spend_time})
    db.session.commit()
    logging.info("update job status of %s" % (job_id))
    return jsonify(code=200, status=status, message='ok', data={})

# machine 获取特定job, 并且获取是否需要进行额外处理的任务 如停止正在进行的任务 status_id = -3
@app.route('/get_job')
def get_job():
    job_type = request.args.get('job_type')
    tag = request.cookies.get('tag', '')
    machine_id = request.cookies.get('machine_id', '')
    if not machine_id:
        return jsonify(code=301, status=0, message='No Machine', data='')
    # 后期可以批量多任务
    query_0 = Jobs.query.filter(Jobs.status==0).filter(or_(Jobs.tag == '', Jobs.tag.in_(tag.replace(' ', '').split(','))))
    # 如果存在特定的job_type，就筛选特定的job_type
    if job_type:
        query_0 = query_0.filter(job_type=job_type)
    # 获取最新的任务
    data = query_0.order_by(Jobs.priority.desc(), Jobs.create_time).first()
    if data:
        data = data.to_json()
        try:
            data['input_data'] = eval(data['input_data'])
        except:
            pass
        # 对该id的任务便更新状态为2
        Jobs.query.filter_by(id=data['id']).update({'status':1, 'machine_id':machine_id})
        db.session.commit()
    else:
        data = {}
    # 获取需要进行的任务操作
    operation_id = []
    for tmp_job in Jobs.query.filter_by(status=-3).filter_by(machine_id=machine_id).all():
        operation_id.append(tmp_job.id)
    return jsonify(code=200, message='ok', data=data, operation_id=operation_id)

# 重跑任务
@app.route('/rerun_job', methods=['POST'])
def rerun_job():
    data = json.loads(request.data)
    job_type = data.get('job_type')
    batch = data.get('batch')
    machine_id = data.get('machine_id')
    job_id = data.get('job_id')
    tmp_query = Jobs.query
    #data = Jobs.query.filter(Jobs.status!=0).filter(Jobs.id.in_(job_id)).update({'status':0, 'machine_id':''}, synchronize_session=False)
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data={})
    if job_type:
        tmp_query = tmp_query.filter(Jobs.job_type==job_type)
    if batch:
        tmp_query = tmp_query.filter(Jobs.batch==batch)
    if machine_id:
        tmp_query = tmp_query.filter(Jobs.machine_id==machine_id)
    if job_id:
        if type(job_id) is not list:
            job_id = [job_id]
        tmp_query = tmp_query.filter(Jobs.id.in_(job_id))
    tmp_query.filter(Jobs.status!=0).filter(Jobs.status!=1).update({'status':0, 'machine_id':''}, synchronize_session=False)
    db.session.commit()
    return jsonify(status=200, data={})

# 删除任务
@app.route('/delete_job', methods=['POST'])
def delete_job():
    data = json.loads(request.data)
    job_type = data.get('job_type')
    batch = data.get('batch')
    machine_id = data.get('machine_id')
    job_id = data.get('job_id')
    tmp_query = Jobs.query
    #data = Jobs.query.filter(Jobs.status!=1).filter(Jobs.id.in_(job_id)).delete(synchronize_session=False)
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data={})
    if job_type:
        tmp_query = tmp_query.filter(Jobs.job_type==job_type)
    if batch:
        tmp_query = tmp_query.filter(Jobs.batch==batch)
    if machine_id:
        tmp_query = tmp_query.filter(Jobs.machine_id==machine_id)
    if job_id:
        if type(job_id) is not list:
            job_id = [job_id]
        tmp_query = tmp_query.filter(Jobs.id.in_(job_id))
    tmp_query.filter(Jobs.status!=1).delete(synchronize_session=False)
    db.session.commit()
    return jsonify(status=200, data={})

# 停止任务
@app.route('/kill_job', methods=['POST'])
def kill_job():
    data = json.loads(request.data)
    job_type = data.get('job_type')
    batch = data.get('batch')
    machine_id = data.get('machine_id')
    job_id = data.get('job_id')
    tmp_query = Jobs.query
    #query = Jobs.query.filter(Jobs.status==1).filter(Jobs.id.in_(job_id)).update({'status':-3}, synchronize_session=False)
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data={})
    if job_type:
        tmp_query = tmp_query.filter(Jobs.job_type==job_type)
    if batch:
        tmp_query = tmp_query.filter(Jobs.batch==batch)
    if machine_id:
        tmp_query = tmp_query.filter(Jobs.machine_id==machine_id)
    if job_id:
        if type(job_id) is not list:
            job_id = [job_id]
        tmp_query = tmp_query.filter(Jobs.id.in_(job_id))
    tmp_query.filter(Jobs.status.in_([0, 1])).update({'status':-3}, synchronize_session=False)
    db.session.commit()
    return jsonify(status=200, data={})

# 复制任务
@app.route('/copy_job', methods=['POST'])
def copy_job():
    data = json.loads(request.data)
    batch = data.get('batch')
    job_id = data.get('job_id')
    job_type = data.get('job_type')
    machine_id = data.get('machine_id')
    tmp_query = Jobs.query
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data={})
    if job_type:
        tmp_query = tmp_query.filter(Jobs.job_type==job_type)
    if batch:
        tmp_query = tmp_query.filter(Jobs.batch==batch)
    if machine_id:
        tmp_query = tmp_query.filter(Jobs.machine_id==machine_id)
    if job_id:
        if type(job_id) is not list:
            job_id = [job_id]
        tmp_query = tmp_query.filter(Jobs.id.in_(job_id))
    data = tmp_query.all()
    count = len(data)
    for line in data:
        new_job = Jobs(line.job_type, line.input_data, line.limit_count, status=0, tag=line.tag, batch=line.batch, priority=line.priority)
        db.session.add(new_job)
    db.session.commit()
    return jsonify(status=200, data={})

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

# 获取任务的列表信息
@app.route('/get_job_list')
def get_job_list():
    job_type = request.args.get('job_type')
    batch = request.args.get('batch')
    offset_num = request.args.get('offset', 0)
    limit_num = request.args.get('limit', 10)
    machine_id = request.args.get('machine_id')
    status = request.args.get('status')
    query_0 = Jobs.query
    # 如果存在特定的job_type，就筛选特定的job_type
    if job_type:
        query_0 = query_0.filter_by(job_type=job_type)
    if batch:
        query_0 = query_0.filter_by(batch=batch)
    if machine_id:
        query_0 = query_0.filter_by(machine_id=machine_id)
    if status:
        query_0 = query_0.filter_by(status=status)
    # 计算数据量
    count = db.session.query(sqlalchemy.func.count(1)).select_from(query_0.subquery()).one()[0]
    data = query_0.order_by(Jobs.id.desc()).limit(limit_num).offset(offset_num).all()
    if data is None:
        return jsonify(code=302, status=0, message='No Job', data='')
    data = convert_rowproxy_to_dict(data)
    return jsonify(code=200, status=1, message='ok', data=data, count=count)

# 获取job的完成统计情况
@app.route('/get_job_statistics')
def get_job_statistics():
    job_type = request.args.get('job_type', -1)
    mysql_1 = ''
    if job_type != -1:
        mysql_1 = " where job_type = '%s' " % job_type
    mysql_0 = "select job_type, batch, status, count(1) as count_job, sum(return_count) as all_count, avg(return_count) as return_count, max(update_time) as update_time, avg(spend_time) as spend_time from jobs"
    #mysql_0 = "select job_type, status, count(1) as count_job, avg(return_count) as return_count,max(update_time) as update_time from jobs"
    mysql_2 = " group by job_type, status, batch"
    mysql_0 = mysql_0 + mysql_1 + mysql_2
    res = db.session.execute(mysql_0)
    data = convert_rowproxy_to_dict(res.fetchall())
    return jsonify(code=200, data=data)

# 获取job的summary
@app.route('/get_job_summary')
@cache.cached(timeout=3)
def get_job_summary():
    # 从任务的类型 、 batch等维度统计任务计算情况
    job_type = request.args.get('job_type')
    batch = request.args.get('batch')
    mysql_1 = ''
    if job_type:
        mysql_1 = " where job_type = '%s' " % job_type
    if batch != "-1" and batch != None:
        mysql_1 += " and batch = '%s'" % batch
    mysql_0 = "select a.job_type, a.batch, a.tag, sum(a.return_count * (case when a.status = 3 then 1 else 0 end)) as count, sum(a.spend_time) / sum(case when a.status = 3 then 1 else 0 end) as spend_time, sum(case when a.status = 0 then 1 else 0 end) as waiting_task, sum(case when a.status = 1 then 1 else 0 end) as working_task, sum(case when a.status = 3 then 1 else 0 end) as finished_task, sum(case when a.status = -1 then 1 else 0 end) as failed_task, min(a.create_time) as begin_time, max(a.update_time) as update_time from jobs a %s group by a.job_type" % mysql_1
    # 如果 batch == -1 表示不需要batch进行分类统计功能, 否则就需要
    # 不等于 -1, 就增加batch级别的group by
    if batch != "-1":
        mysql_0 += ", batch"
    mysql_0 += ' order by update_time desc'
    res = db.session.execute(mysql_0)
    tmp = res.fetchall()
    #data = convert_rowproxy_to_dict(res.fetchall())
    data = convert_rowproxy_to_dict(tmp)
    return jsonify(code=200, data=data)

# 获取job完成详情
@app.route('/get_job_details')
def get_job_details():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify(code=301, data={})
    res = db.session.execute("select  * from jobs where id = %s" % job_id)
    data = convert_rowproxy_to_dict(res.fetchall())
    if data:
        data = data[0]
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
    platform = data.get('platform', '')
    new_machine = Machine(machine_id, name, tag, count_process, limit_process,
            cpu_ratio, cpu_core, memory_used, memory_free, disk_free,
            disk_used, status, platform)
    # merge 如果存在就更新数据 ，不存在的话就插入新的数据
    db.session.merge(new_machine)
    db.session.commit()
    operation = {}
    if machine_id in machine_operation:
        if machine_operation[machine_id]:
            operation = machine_operation[machine_id].pop()
    return jsonify(code=200, data=new_machine.to_json(), operation=operation)

# 增加machine信息
@app.route('/get_machine_info', )
@cache.cached(timeout=3)
def get_machine_info():
    begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 30 * 60))
    #res = db.session.execute("select *  from machine where update_time > (now() - interval 10 minute)")
    res = db.session.execute("select *  from machine where update_time > '%s' " % begin_time)
    data = convert_rowproxy_to_dict(res.fetchall())
    for line in data:
        # -1 表示机器关机了
        if line['status'] == -1:
            continue
        tmp_update_time = time.mktime(time.strptime(line['update_time'], "%Y-%m-%d %H:%M:%S"))
        if (time.time() - 5 * 60) > tmp_update_time:
            line['status'] = -2
        #if (time.time() - 10 * 60) > tmp_update_time:
        #    line['status'] = -2
    return jsonify(code=200, data=data)

# 上传文件
@app.route('/upload_file', methods=['POST'])
def upload_file():
    tmp_file = request.files['file']
    job_type = request.form['job_type']
    #return jsonify(code=200, data="success", job_type=job_type)
    file_name = secure_filename(tmp_file.filename)
    job_type = secure_filename(job_type)
    if ".zip" in file_name:
        tmp_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        dir_path = os.path.join(app.config['JOBS_FOLDER'], job_type)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        tmp_file.save(tmp_path)
        unzip_file(tmp_path, dir_path)
    return jsonify(code=200, data="success", dir_path=dir_path, tmp_path=tmp_path)

# 获取可筛选的信息
@app.route('/get_distinct_select')
@cache.cached(timeout=30)
#@cache.cached(timeout=100, key_prefix='get_list')
def get_distinct_select():
    status = [''] + [-2, -1, 0, 1, 2, 3]
    res = db.session.execute("select distinct job_type from jobs")
    job_type = [''] + [x['job_type'] for x in convert_rowproxy_to_dict(res.fetchall())]
    job_type = list(filter(None, job_type))
    res = db.session.execute("select distinct batch from jobs")
    batch = [''] + [x['batch'] for x in convert_rowproxy_to_dict(res.fetchall())][::-1]
    batch = list(filter(None, batch))
    begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 30 * 60))
    res = db.session.execute("select distinct machine_id  from machine where update_time > '%s' " % begin_time)
    machine_id = [''] + [x['machine_id'] for x in convert_rowproxy_to_dict(res.fetchall())][::-1]
    machine_id = list(filter(None, machine_id))
    return jsonify(code=200, data="success", time=time.time(), job_type=job_type, batch=batch, status=status, machine_id=machine_id)

@app.route('/insert_machine_operation', methods=['POST'])
def insert_machine_operation():
    # status = 1 表示更新任务参数
    # status = 0 表示暂停机器
    # status = -1 表示机器下线
    data = json.loads(request.data)
    machine_id = data.get('machine_id')
    operation = data.get('operation')
    if not machine_id:
        return jsonify(code=301, data={})
    if not operation:
        return jsonify(code=301, data={})
    tmp_list = machine_operation.get(machine_id, [])
    # status=0 -1 历史操作全部清空
    if operation.get('status', 1) in [0, -1]:
        tmp_list = []
    tmp_list = [operation] + tmp_list
    machine_operation[machine_id] = tmp_list
    return jsonify(code=200, data=machine_operation)

@app.route('/get_history_job')
def get_history_job():
    n = 24
    # 取最近 24 小时的数据
    time_0 = time.strftime("%Y-%m-%d %H:00:00", time.localtime(time.time() - n * 3600))
    #mysql_0 = "select a.job_type, a.batch, a.tag, sum(a.return_count * (case when a.status = 3 then 1 else 0 end)) as count, count(1) as task_num, sum(a.spend_time) / sum(case when a.status = 3 then 1 else 0 end) as spend_time, sum(case when a.status = 0 then 1 else 0 end) as waiting_task, sum(case when a.status = 1 then 1 else 0 end) as working_task, sum(case when a.status = 3 then 1 else 0 end) as finished_task, sum(case when a.status = -1 then 1 else 0 end) as failed_task, min(a.create_time) "
    #mysql_0 += " as begin_time, DATE_FORMAT(max(a.update_time),'%Y-%m-%d %H:00:00') as update_time from jobs a where update_time > " + "'%s'" % time_0 + " group by a.job_type, DATE_FORMAT(`update_time`,'%Y-%m-%d %H:00:00')"
    mysql_0 = "select group_concat(distinct a.job_type) as job_type, sum(a.return_count * (case when a.status = 3 then 1 else 0 end)) as count, count(1) as task_num, sum(a.spend_time) / sum(case when a.status = 3 then 1 else 0 end) as spend_time, sum(case when a.status = 0 then 1 else 0 end) as waiting_task, sum(case when a.status = 1 then 1 else 0 end) as working_task, sum(case when a.status = 3 then 1 else 0 end) as finished_task, sum(case when a.status = -1 then 1 else 0 end) as failed_task, min(a.create_time) "
    mysql_0 += " as begin_time, DATE_FORMAT(max(a.update_time),'%Y-%m-%d %H:00:00') as update_time from jobs a where update_time > " + "'%s'" % time_0 + " group by DATE_FORMAT(`update_time`,'%Y-%m-%d %H:00:00')"
    res = db.session.execute(mysql_0)
    data = convert_rowproxy_to_dict(res.fetchall())
    # 数据再处理
    series = []
    tmp_data = {}
    for i in range(n):
        time_1 = time.strftime("%Y-%m-%d %H:00:00", time.localtime(time.time() - 86400 + i * 3600))
        tmp_data[time_1] = {'task_num':0, "count":0, "job_type":"", "failed_task":0, "waiting_task":0, "working_task":0, "finished_task":0 ,"update_time":time_1, "spend_time":0, "begin_time":time_1}
        series.append(time_1)
    for line in data:
        tmp_data[line['update_time']] = line
    data = tmp_data
    # 数据处理成 前端可以看的数据
    front_end_data = {}
    tmp_dic = {"name":"", "type":"bar", "stack": "任务信息", "emphasis":{"focus": "series"}, "data": []}
    key_list = ["task_num", "count", "job_type", "failed_task", "waiting_task", "working_task", "finished_task", "update_time", "spend_time", "begin_time"]
    summary_key_list = ["task_num", "count", "failed_task", "waiting_task", "working_task", "finished_task"]
    summary_data = dict.fromkeys(summary_key_list, 0)
    for tmp_key in key_list:
        tmp_dic_0 = deepcopy(tmp_dic)
        tmp_dic_0["name"] = tmp_key
        for tmp_series in series:
            tmp_dic_0['data'].append(data[tmp_series][tmp_key])
            if tmp_key in summary_data:
                summary_data[tmp_key] += data[tmp_series][tmp_key]
        front_end_data[tmp_key] = tmp_dic_0
    return jsonify(code=200, data=data, front_end_data=front_end_data, series=series, title=key_list, summary_data=summary_data)

@app.route('/get_all_job_type')
def get_all_job_type():
    data = {}
    for line in Job_file.query.all():
        line = line.to_json()
        # 增加其他信息
        line['tag'] = ''
        line['batch'] = ''
        line['count'] = 0
        line['spend_time'] = 0
        line['failed_task'] = 0
        line['waiting_task'] = 0
        line['working_task'] = 0
        line['finished_task'] = 0
        data[line['job_type']] = line
    return jsonify(code=200, data=data)

if __name__ == '__main__':
    main()
