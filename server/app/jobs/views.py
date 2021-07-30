#coding=utf-8
import sys
import os
import json
import time
from app import db, cache
import app.jobs.proc as proc
import app.utils as utils
from app.models import Jobs, JobFile
from . import router
from flask import Flask, request, jsonify, json, send_file, g
from app.env import JOB_WAITING, MACHINE_OK, MACHINE_DENY

# 插入一条jobs
@router.route('/insert_job', methods=['POST'])
def insert_job():
    data = json.loads(request.data)
    job_type = data.get('job_type')
    if not JobFile.get_by_job_type(job_type=job_type):
        return jsonify(code=300, message='Failed, job_type not found!', data={})
    job_id = proc.insert_job(data)
    return jsonify(code=200, status=1, message='ok', data={"job_id":job_id})

# 更新任务状态，为运行成功或者失败
# 任务状态 0 等待分发， 1 运行中， 2 运行成功， -1 运行失败, -2 回调函数计算失败
@router.route('/update_job',  methods=['POST'])
def update_job():
    data = json.loads(request.data)
    job_id = data.get('id')
    status = data.get('status')
    result = {}
    # 判断 job_id 和 status 是否存在
    if not (job_id and status):
        return jsonify(code=301, message='failed', data=result)
    result['result'] = proc.update_job_status(data)
    return jsonify(code=200, message='ok', data=result)

# machine 获取特定job, 并且获取是否需要进行额外处理的任务 如停止正在进行的任务 status_id = -3
@router.route('/get_job')
def get_job():
    result = {}
    job_type = request.args.get('job_type')
    tag = request.cookies.get('tag', '')
    machine_id = request.cookies.get('machine_id')
    if not machine_id:
        return jsonify(code=301, message='No Machine', data=result)
    # 获取任务
    jobs = proc.get_job(job_type=job_type, tag=tag, machine_id=machine_id)
    # 获取需要进行的操作
    operation_id = proc.get_job_operation(machine_id=machine_id)
    result = {}
    result["jobs"] = jobs
    result["operation_id"] = operation_id
    return jsonify(code=200, message='ok', data=result)

# 重跑任务
@router.route('/rerun_job', methods=['POST'])
def rerun_job():
    data = json.loads(request.data)
    result = {}
    job_type = data.get('job_type')
    batch = data.get('batch')
    machine_id = data.get('machine_id')
    job_id = data.get('job_id')
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data=result)
    tmp_result = proc.rerun_job(job_id=job_id, job_type=job_type, batch=batch, machine_id=machine_id)
    result['result'] = tmp_result
    return jsonify(status=200, data=result)

# 删除任务
@router.route('/delete_job', methods=['POST'])
def delete_job():
    data = json.loads(request.data)
    result = {}
    job_type = data.get('job_type')
    batch = data.get('batch')
    machine_id = data.get('machine_id')
    job_id = data.get('job_id')
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data=result)
    tmp_result = proc.delete_job(job_id=job_id, job_type=job_type, batch=batch, machine_id=machine_id)
    result['result'] = tmp_result
    return jsonify(status=200, data=result)

# 停止任务
@router.route('/kill_job', methods=['POST'])
def kill_job():
    data = json.loads(request.data)
    result = {}
    job_type = data.get('job_type')
    batch = data.get('batch')
    machine_id = data.get('machine_id')
    job_id = data.get('job_id')
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data=result)
    tmp_result = proc.kill_job(job_id=job_id, job_type=job_type, batch=batch, machine_id=machine_id)
    result['result'] = tmp_result
    return jsonify(status=200, data=result)

# 复制重提任务
@router.route('/copy_job', methods=['POST'])
def copy_job():
    data = json.loads(request.data)
    result = {}
    batch = data.get('batch')
    job_id = data.get('job_id')
    job_type = data.get('job_type')
    machine_id = data.get('machine_id')
    # 空数据的话 就不用管他了
    if not (job_type or batch or machine_id or job_id):
        return jsonify(status=301, data=result)
    tmp_result = proc.copy_job(job_id=job_id, job_type=job_type, batch=batch, machine_id=machine_id)
    result['result'] = tmp_result
    return jsonify(status=200, data=result)

# 清除任务的 result 信息, 防止占用过多空间
@router.route('/clear_job', methods=['POST'])
def clear_job():
    data = json.loads(request.data)
    result = {}
    job_id = data.get('job_id')
    if not job_id:
        return jsonify(status=301, data=result)
    tmp_result = proc.clear_job(job_id=job_id)
    result['result'] = tmp_result
    return jsonify(status=200, data=result)

# 获取任务的列表信息
@router.route('/get_job_list')
def get_job_list():
    job_type = request.args.get('job_type')
    batch = request.args.get('batch')
    offset_num = request.args.get('offset', 0)
    limit_num = request.args.get('limit', 10)
    machine_id = request.args.get('machine_id')
    status = request.args.get('status')
    clear = request.args.get('clear')
    result = {}
    result = proc.get_job_list(job_type=job_type, batch=batch, machine_id=machine_id, status=status, offset_num=offset_num, limit_num=limit_num, clear=clear)
    return jsonify(code=200, message='ok', data=result)

# 获取job的完成统计情况
@router.route('/get_job_statistics')
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
@router.route('/get_job_summary')
@cache.cached(timeout=3)
def get_job_summary():
    # 从任务的类型 、 batch等维度统计任务计算情况
    job_type = request.args.get('job_type')
    batch = request.args.get('batch')
    result = {}
    result = proc.get_job_summary(job_type, batch)
    return jsonify(code=200, data=result)

# 获取job详情
@router.route('/get_job_details')
def get_job_details():
    job_id = request.args.get('job_id')
    result = {}
    if not job_id:
        return jsonify(code=301, data=result)
    tmp_job = Jobs.get_by_job_id(job_id=job_id)
    if not tmp_job:
        return jsonify(code=301, data=result)
    result = tmp_job.to_json()
    return jsonify(code=200, data=result)

# 获取可筛选的信息
@router.route('/get_distinct_select')
@cache.cached(timeout=30)
def get_distinct_select():
    result = proc.get_distinct_select(limit_time=30)
    result['time'] = time.time()
    return jsonify(code=200, data=result)

# 获取历史任务
@router.route('/get_history_job')
def get_history_job():
    limit_time = request.args.get('limit_time', 24)
    result = {}
    if limit_time > 100 or limit_time <= 0:
        return jsonify(code=301, data=result)
    result = proc.get_history_job(limit_time=limit_time)
    return jsonify(code=200, data=result)

# 获取所有的任务类型
@router.route('/get_all_job_type')
def get_all_job_type():
    data = proc.get_all_job_type()
    return jsonify(code=200, data=data)

# 获取需要二次处理的任务

