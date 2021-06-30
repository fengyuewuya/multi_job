#coding=utf-8
import sys
import os
import json
from app import app, db, cache
from app.env import JOBS_DIR, UPLOAD_DIR, logging
import app.job_file.proc as proc
from app.models import JobFile
from . import router
from flask import Flask, request, jsonify, json, send_file, g
from werkzeug.utils import secure_filename
import app.utils as utils

# 检测任务文件的状态 如果状态比较旧就返回 1
@router.route('/check_job_file_status')
def check_job_file_status():
    data = {}
    status = 0
    job_type = request.args.get("job_type")
    tmp_job_file = JobFile.get_by_job_type(job_type=job_type)
    # 说明不存在该 job_type
    if not tmp_job_file:
        return jsonify(code=301, message='Job type not found', data={})
    # local_version 必须是数字类型
    local_version = str(request.args.get("version", -1))
    if local_version.isdigit():
        local_version = int(local_version)
    else:
        return jsonify(code=301, message='Local version is not right', data={})
    # 如果 tmp_job_file.version > local_version, status 为 1 说明 任务文件已经更新了，需要重新下载
    if tmp_job_file.version > local_version:
        status = 1
    data['status'] = status
    return jsonify(code=200, message='ok', data=data)

# 更新job_file 状态
@router.route('/update_job_file_status')
def update_job_file_status():
    data = {}
    version = 0
    job_type = request.args.get("job_type")
    # 更新下文件中的version 信息， 并重新压缩文件
    result = proc.update_job_file_version(job_type=job_type)
    data["version"] = version
    return jsonify(code=200, message='ok', data=data)

# 删除job_type_file
@router.route('/delete_job_file')
def delete_job_file():
    data = {}
    job_type = request.args.get("job_type")
    tmp_job_file = JobFile.get_by_job_type(job_type=job_type)
    # 说明不存在该 job_type
    if not tmp_job_file:
        return jsonify(code=301, message='Job type not found', data={})
    JobFile.delete_job_type(job_type=job_type)
    return jsonify(code=200, message='delete success', data=data)

# 获取 job的file文件, zip格式
@router.route('/get_job_file')
def get_job_file():
    job_type = request.args.get('job_type')
    tmp_job_file = JobFile.get_by_job_type(job_type=job_type)
    # 说明不存在该 job_type
    if not tmp_job_file:
        return jsonify(code=200, message='Job type not found', status=-2)
    job_file = os.path.join(JOBS_DIR, job_type) + ".zip"
    job_file_name = job_type + ".zip"
    return send_file(job_file, as_attachment=True,
                     attachment_filename=job_file_name,
                     mimetype='application/zip')

# 上传文件
@router.route('/upload_file', methods=['POST'])
def upload_file():
    data = {}
    tmp_file = request.files['file']
    job_type = request.form['job_type']
    #return jsonify(code=200, data="success", job_type=job_type)
    file_name = secure_filename(tmp_file.filename)
    job_type = secure_filename(job_type)
    if ".zip" in file_name:
        tmp_path = os.path.join(UPLOAD_DIR, file_name)
        dir_path = os.path.join(JOBS_DIR, job_type)
        #dir_path = JOBS_DIR
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        tmp_file.save(tmp_path)
        utils.unzip_file(tmp_path, dir_path)
    return jsonify(code=200, message="success", data=data)

# 检测 jobs 的目录情况
@router.route('/check_jobs_dir')
def check_jobs_dir():
    result = []
    for tmp_dir in os.listdir(JOBS_DIR):
        tmp_dir_0 = os.path.join(JOBS_DIR, tmp_dir)
        if os.path.isdir(tmp_dir_0):
            result.append(tmp_dir)
    data = {}
    data['job_type'] = result
    return jsonify(code=200, message="success", data=data)
