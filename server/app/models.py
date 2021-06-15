#coding=utf-8
from app import db
from app.env import MACHINE_OK, JOB_WAITING, MACHINE_UPDATE_STATUS_NO, MACHINE_UPDATE_STATUS_YES, MACHINE_PAUSE_YES, MACHINE_EXIT_YES, MACHINE_RERUN_YES
import os
import sys
import datetime
from sqlalchemy import and_, or_, UniqueConstraint, func

# 初始化Jobs表的相关参数
class Jobs(db.Model):
    __tablename__  = 'jobs'
    __table_args__ = {"useexisting":True, 'mysql_charset':'utf8', 'mysql_engine': 'InnoDB'}
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(64), index=True)
    priority = db.Column(db.Integer, default=0)
    input_data = db.Column(db.Text)
    machine_id = db.Column(db.String(64), index=True)
    limit_count = db.Column(db.Integer, default=1)
    tag = db.Column(db.Text)
    version = db.Column(db.Integer, default=-1)
    status = db.Column(db.Integer, default=JOB_WAITING)
    return_count = db.Column(db.Integer, default=0)
    result = db.Column(db.Text, default='')
    spend_time = db.Column(db.Integer)
    batch = db.Column(db.String(64), default=lambda: time.strftime("%Y-%m-%d", time.localtime()), index=True) # 生产批次
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)
    UniqueConstraint('job_type', 'batch', name='job_type_batch')

    """
    def __init__(self, job_type, input_data, limit_count=1, tag='', version=-1, status=1, return_count=1, result='', spend_time=0, batch='', priority=0):
        self.job_type = job_type
        self.input_data = input_data
        self.limit_count = limit_count
        self.tag = tag
        self.version = version
        self.status = status
        self.return_count = return_count
        self.result = result
        self.spend_time = spend_time
        self.priority = priority
        if batch == '':
            batch = time.strftime("%Y-%m-%d", time.localtime())
        self.batch = batch
    """

    def __repr__(self):
        return '<job_id %r>' % self.id

    def to_json(self):
        result = {}
        dic_0 = self.__dict__
        for k, v in dic_0.items():
            if k == "_sa_instance_state":
                continue
            result[k] = v
            if isinstance(v, datetime.datetime):
                result[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return result

    @classmethod
    def get_by_job_id(cls, job_id):
        if not job_id:
            return None
        tmp_job = Jobs.query.filter_by(id=job_id).first()
        return tmp_job

# 初始化 Job_file 参数
class JobFile(db.Model):
    __tablename__  = 'job_file'
    __table_args__ = {"useexisting":True, 'mysql_charset':'utf8', 'mysql_engine': 'InnoDB'}
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
        result = {}
        dic_0 = self.__dict__
        for k, v in dic_0.items():
            if k == "_sa_instance_state":
                continue
            result[k] = v
            if isinstance(v, datetime.datetime):
                result[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return result

    @classmethod
    def get_by_job_type(cls, job_type):
        print(job_type)
        if not job_type:
            return None
        job_type = str(job_type)
        tmp_job_file = JobFile.query.filter_by(job_type=job_type).first()
        return tmp_job_file

    @classmethod
    def delete_job_type(cls, job_type):
        tmp_query = JobFile.query.filter_by(job_type=job_type)
        tmp_query.delete(synchronize_session=False)
        db.session.commit()
        return 1

# 初始化 machine 表的参数
class Machine(db.Model):
    __tablename__  = 'machine'
    __table_args__ = {"useexisting":True, 'mysql_charset':'utf8', 'mysql_engine': 'InnoDB'}
    machine_id = db.Column(db.String(128), primary_key=True)
    platform = db.Column(db.String(32))
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
    status = db.Column(db.Integer, default=MACHINE_OK)
    update_status = db.Column(db.Integer, default=MACHINE_UPDATE_STATUS_NO)
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, machine_id):
        self.machine_id = machine_id

    """
    def __init__(self, machine_id, name, tag, count_process, limit_process, cpu_ratio, cpu_core, memory_used, memory_free, disk_free, disk_used, platform):
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
        self.platform = platform
        self.status = status
    """

    def __repr__(self):
        return '<machine_id %r>' % self.machine_id

    def to_json(self):
        result = {}
        dic_0 = self.__dict__
        for k, v in dic_0.items():
            if k == "_sa_instance_state":
                continue
            result[k] = v
            if isinstance(v, datetime.datetime):
                result[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return result

    @classmethod
    def get_by_machine_id(cls, machine_id):
        if not machine_id:
            return None
        machine_id = str(machine_id)
        tmp_machine = Machine.query.filter_by(machine_id=machine_id).first()
        return tmp_machine

    # 更新 machine 的 特定信息
    @classmethod
    def updata_machine_info(cls, machine_id, name=None, tag=None, limit_process=None, update_status=MACHINE_UPDATE_STATUS_NO):
        if not machine_id:
            return 0
        machine_id = str(machine_id)
        tmp_machine = Machine.query.filter_by(machine_id=machine_id).first()
        if not tmp_machine:
            return 0
        # 更新 参数
        if update_status == MACHINE_UPDATE_STATUS_YES:
            tmp_machine.update_status = MACHINE_UPDATE_STATUS_YES
            if name:
                tmp_machine.name = name
            if tag:
                tmp_machine.tag = tag
            if limit_process:
                tmp_machine.limit_process = limit_process
        # 暂停机器
        if update_status == MACHINE_PAUSE_YES:
            tmp_machine.update_status = MACHINE_PAUSE_YES
        # 机器退出
        if update_status == MACHINE_EXIT_YES:
            tmp_machine.update_status = MACHINE_EXIT_YES
        # 机器 从暂停到接着跑 rerun
        if update_status == MACHINE_RERUN_YES:
            tmp_machine.update_status = MACHINE_RERUN_YES
        db.session.add(tmp_machine)
        db.commit()
        return 1

    # 检测 machine 是否需要更新, 1 需要更新，0 不需要更新
    @classmethod
    def check_machine_update_status(cls, machine_id):
        if not machine_id:
            return 0
        machine_id = str(machine_id)
        tmp_machine = Machine.query.filter_by(machine_id=machine_id).first()
        if not tmp_machine:
            return 0
        if tmp_machine.update_status == MACHINE_UPDATE_STATUS_YES:
            return 1
        else:
            return 0
