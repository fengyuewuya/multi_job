#coding=utf-8
import sys
import os
import time
import uuid
from . import router
from copy import deepcopy
from app.models import IP
from app import app, db, cache
from flask import Flask, request, jsonify, json, send_file, g
from app.env import APP_CONFIG
# 插入或者更新ip
@router.route('/insert_ip', methods=["POST"])
def insert_ip():
    data = json.loads(request.data)
    instance_id = data["instance_id"]
    ip = data["ip"]
    port = data["port"]
    sep_time = data["sep_time"]
    expire_time = data.get("expire_time")
    IP.update_ip(instance_id, ip, port, sep_time, expire_time)
    data = {}
    data["result"] = 1
    return jsonify(code=200, data=data)

# 获取存活的ip信息
@router.route('/get_ips', methods=["GET"])
@cache.cached(timeout=5)
def get_ips():
    limit_time = request.args.get('limit_time', 60)
    limit_time = int(limit_time)
    all_ips = IP.get_all_ips(limit_time)
    result = []
    for tmp_ip in all_ips:
        tmp_result = [tmp_ip.instance_id,
                tmp_ip.ip,
                tmp_ip.port,
                tmp_ip.expire_time.strftime("%Y-%m-%d %H:%M:%S")]
        result.append(tmp_result)
    data = {}
    data["result"] = result
    return jsonify(code=200, data=data)

# 获取 白名单ip 信息
@router.route('/get_whitelist', methods=["GET"])
@cache.cached(timeout=5)
def get_whitelist():
    whitelist = APP_CONFIG["whitelist"]
    data = {}
    data["whitelist"] = whitelist
    return jsonify(code=200, data=data)

