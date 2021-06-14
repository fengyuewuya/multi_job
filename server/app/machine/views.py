#coding=utf-8
import sys
import os
from app import db
from app import app
from app.models import Machine
from app.env import MACHINE_OK
import app.machine.proc as proc
from . import router
from app.env import JOB_WAITING, MACHINE_DENY, MACHINE_UPDATE_STATUS_NO

# 注册或者更新 machine 信息
@router.route('/append_machine', methods=["POST"])
def append_machine():
    data = json.loads(request.data)
    return_data = {}
    if data['machine_id'] == '':
        data['machine_id'] = uuid.uuid1().hex
        return_data['machine_id'] = uuid.uuid1().hex
    machine_id = data['machine_id']
    # 检测是否存在machine_id 对应的machine，不存在的话 就新建machine
    tmp_machine = Machine.get_by_machine_id(machine_id)
    if not tmp_machine:
        tmp_machine = Machine(machine_id=machine_id)
    # 更新机器运行信息
    tmp_machine.cpu_ratio = data.get('cpu_ratio', -1)
    tmp_machine.cpu_core = data.get('cpu_core', -1)
    tmp_machine.memory_used = data.get('memory_used', -1)
    tmp_machine.memory_free = data.get('memory_free', -1)
    tmp_machine.disk_free = data.get('disk_free', -1)
    tmp_machine.disk_used = data.get('disk_used', -1)
    tmp_machine.platform = data.get('platform', '')
    tmp_machine.count_process = data['count_process']
    # 检测是否需要更新 配置信息, 函数返回1 就是需要下发云端参数， 0不需要下发, 则更新本地参数
    if not Machine.check_machine_update_status(machine_id=machine_id):
        tmp_machine.name = data['name']
        tmp_machine.tag = data['tag']
        limit_process = data['limit_process']
    tmp_machine.update_status = MACHINE_UPDATE_STATUS_NO
    # merge 如果存在就更新数据 ，不存在的话就插入新的数据
    db.session.add(tmp_machine)
    db.session.commit()
    return jsonify(code=200, data=tmp_machine.to_json())

# 增加machine信息
@router.route('/get_machine_info', )
#@cache.cached(timeout=3)
def get_machine_info():
    data = proc.get_machine_info(limit_time=30, offline_time=5)
    return jsonify(code=200, data=data)

# machine 的更新逻辑，可更新字段为name, tag, limit_process
# 云端和本地同时更新的话，则云端数据优先级更高
# 如果云端数据更新的话，将update_status 设为 MACHINE_UPDATE_STATUS_YES，当机器请求 append_machine 的时候，检测到需要更新，则返回 服务器的name，tag，limit_process, 并将 update_status 设为 MACHINE_UPDATE_STATUS_NO
@router.route('/update_machine_info', methods=['POST'])
def update_machine_info():
    result = {}
    data = json.loads(request.data)
    machine_id = data.get('machine_id')
    name = data.get("name")
    tag = data.get("tag")
    limit_process = data.get("limit_process")
    if not machine_id:
        return jsonify(code=301, message="", data={})
    if not (name or tag or limit_process):
        return jsonify(code=301, message="", data={})
    tmp_result = Machine.update_machine_info(machine_id, name=name, tag=tag, limit_process=limit_process)
    result['result'] = tmp_result
    return jsonify(code=200, data=result)
