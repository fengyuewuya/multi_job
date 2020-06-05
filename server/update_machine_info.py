#coding=utf-8
import psutil
import os
import time
import requests
tmp_pop = os.popen("uname -n")
instance_id = tmp_pop.read().strip()
# 内存 cpu运行 硬盘 cpu数量
def get_info(interval=180):
    data = {}
    cpu_used = 0
    cpu_info = psutil.cpu_percent(interval=interval, percpu=True)
    for tmp_cpu in cpu_info:
        if tmp_cpu > 20:
            cpu_used += 1
    cpu_count = psutil.cpu_count()
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    # 获取 运行信息
    tmp_instance_id = instance_id[:1] + '-' + instance_id[2:]
    data['from'] = 'my'
    data['instance_id'] = tmp_instance_id
    data['CPUUtilization'] = int(sum(cpu_info) / len(cpu_info))
    data['cpu_core'] = len(cpu_info)
    data['cpu_used'] = cpu_used
    data['memory_usedspace'] = int(memory_info.used / 1000000) # 单位 M
    data['memory_freespace'] = int(memory_info.free / 1000000) # 单位 M
    data['diskusage_free'] = int(disk_info.free / 1000000) # 单位 M
    data['last_log'] = ''
    data['create_time'] = int(time.time())
    last_log = ''
    # 获取 kit train 日志
    tmp_pop = os.popen("ls -t dpgen_work/*/00*/lcurve.out")
    for tmp_file in tmp_pop.read().strip().split():
        last_log = os.popen("tail -n 1 %s" % tmp_file)
        last_log = last_log.read()
        break

    # vasp fp.log
    if last_log == '':
        tmp_pop = os.popen("ls -t dpgen_work/*/task.*/fp.log")
        for tmp_file in tmp_pop.read().strip().split():
            last_log = os.popen("tail -n 1 %s" % tmp_file)
            last_log = last_log.read()
            break

    # lammps model_devi.log
    if last_log == '':
        tmp_pop = os.popen("ls -t dpgen_work/*/task.*/model_devi.out")
        for tmp_file in tmp_pop.read().strip().split():
            last_log = os.popen("tail -n 1 %s" % tmp_file)
            last_log = last_log.read()
            break
    data['last_log'] = last_log
    return data
while True:
    time.sleep(1)
    data = {}
    try:
        data = get_info()
    except Exception as e:
        print('error', e)
        continue
    headers = {"Content-Type": "application/json;charset=utf-8"}
    proxies = {"http":"http://192.168.34.135:6666", "https":"https://192.168.34.135:6666"}
    url_0 = "http://39.98.150.188:5005/post_machine_info"
    if len(data.keys()) == 0:
        continue
    for i in range(3):
        try:
            res = requests.post(url_0, json=data, headers=headers, proxies=proxies, timeout=3)
            print(res.text)
            break
        except Exception as e:
            print('error', e)
