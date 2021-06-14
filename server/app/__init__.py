#coding=utf-8
import datetime
import json
import zipfile
import io
import os
import time
from copy import deepcopy
from werkzeug.utils import secure_filename
from sqlalchemy import and_, or_, UniqueConstraint
from multiprocessing import Process, Queue
import logging, logging.handlers, logging.config
import uuid
import decimal
import sqlalchemy
from flask import Flask, request, jsonify, json, send_file, g
from flask_sqlalchemy import SQLAlchemy
from flask_docs import ApiDoc
from flask_cache import Cache
from app.env import BASE_DIR, JOBS_DIR, CWD_DIR, CONFIG_DIR, UPLOAD_DIR, LOG_CONFIG, APP_CONFIG
# 0.1 读取logger 配置
logging.config.dictConfig(LOG_CONFIG)

# 0.2 初始化flask 设置数据库相关信息
app = Flask(__name__)
# 设缓存
cache = Cache(app, config={'CACHE_TYPE': 'simple'}, with_jinja2_ext=False)
app.config['BASE_DIR'] = BASE_DIR
app.config['JOBS_DIR'] = JOBS_DIR
app.config['CWD_DIR'] = CWD_DIR
app.config['CONFIG_DIR'] = CONFIG_DIR
app.config['UPLOAD_DIR'] = UPLOAD_DIR
app.config['STATIC_URL_PATH'] = ""

# 0.3 设定api docs相关信息
app.config['API_DOC_MEMBER'] = ['insert_job']
ApiDoc(app)

# 0.2.1 设置数据库相关参数
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False                          # 是否显示mysql配置
app.config['SQLALCHEMY_DATABASE_URI'] = APP_CONFIG['db']                      # 数据库的连接配置
if 'mysql' in APP_CONFIG['db']:
    app.config['SQLALCHEMY_POOL_SIZE'] = APP_CONFIG.get('SQLALCHEMY_POOL_SIZE', 100)  # 数据库连接的数量
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = APP_CONFIG.get('SQLALCHEMY_MAX_OVERFLOW', -1) # 配置数据库超负载的链接数 -1表示不限制。如果是int的话，可能会触发爆内存bug
app.config['JSON_AS_ASCII'] = False                                           # 让返回的json结果显示中文
db = SQLAlchemy(app)
from app.jobs import router as jobs_router
from app.job_file import router as job_file_router
from app.machine import router as machine_router
app.register_blueprint(jobs_router)
app.register_blueprint(job_file_router)
app.register_blueprint(machine_router)
db.create_all()

# 设定一些初级的api

# 0.3 设置flask
# 0.3.1 设置flask函数
@app.route('/')
def hello_world():
    return 'This is Multi-job!'

 # 首页
@app.route('/home')
def home():
    return send_file("static/index.html")
if __name__ == "__main__":
    host = all_config["host"]
    port = all_config["port"]
    debug = all_config["debug"]
    app.run(host=host, port=port, debug=debug, threaded=True)
