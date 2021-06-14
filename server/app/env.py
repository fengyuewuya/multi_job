# coding=utf-8
"""
配置环境变量
"""
import os
import sys
import json

# 设定相关的路径地址
# 获取 BASE_DIR 也就是 server 所在的目录，所以需要做两次的 dirname
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)
# jobs 离线文件所在目录
JOBS_DIR = os.path.join(BASE_DIR, "static", "jobs")
# config 所在目录
CONFIG_DIR = os.path.join(BASE_DIR, "config")
# 进程启动的地址
CWD_DIR = os.getcwd()
# 上传文件 所在的地址
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "upload")
# app 配置文件 的地址
APP_CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
# log 配置文件 的地址
LOG_CONFIG_PATH = os.path.join(CONFIG_DIR, "log_config.json")

# 读取相关配置
# 读取APP的配置
APP_CONFIG = json.load(open(APP_CONFIG_PATH))
# 读取LOG的配置
LOG_CONFIG = json.load(open(LOG_CONFIG_PATH))

# JOB的相关状态
# 0:排队
JOB_WAITING = 0
# 1:远端正在计算
JOB_RUNNING = 1
# 2:远端计算成功 等待回传调用
JOB_CALLBACK = 2
# 3:计算成功
JOB_SUCCESS = 3
# -1:任务远端计算失败
JOB_FAILED = -1
# -2:任务回传调用计算失败
JOB_CALLBACK_FAILED = -2
# -3:需要删除的任务
JOB_TO_KILL = -3

# MACHINE 相关状态
# 1 表示 机器正常运行
MACHINE_OK = 1
# 0 表示暂停机器，机器进入黑名单，不会更新参数也拿不到任务
MACHINE_DENY = 0

# MACHINE_UPDATE_STATUS 相关状态
# 1 表示 机器的云端参数有更新
MACHINE_UPDATE_STATUS_YES = 1
# 0 表示 机器的云端参数不需要更新
MACHINE_UPDATE_STATUS_NO = 0
