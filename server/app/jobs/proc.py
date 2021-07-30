import json
import time
import sqlalchemy
from copy import deepcopy
from multiprocessing import Process, Queue
from sqlalchemy import and_, or_, UniqueConstraint
from app import app, db
from app.models import Jobs, JobFile
from app.env import JOB_WAITING, JOB_RUNNING, JOB_TO_KILL, JOBS_DIR, CWD_DIR, logging
import app.utils as utils
# 插入任务
def insert_job(data):
    # 插入一条新的任务
    tmp_job = Jobs()
    # 确定 job_type
    job_type = data.get('job_type')
    tmp_job.job_type = job_type
    # 确定 input_data
    input_data = json.dumps(data.get('input_data', ''))
    tmp_job.input_data = input_data
    # 任务相关机器标签
    tag = data.get('tag', job_type)
    tmp_job.tag = tag
    # 重跑次数
    limit_count = data.get('limit_count')
    if limit_count:
        tmp_job.limit_count = limit_count
    # 任务批次
    batch = data.get('batch')
    if batch:
        tmp_job.batch = batch
    # 任务优先级 越大越优先
    priority = data.get('priority', 0)
    tmp_job.priority = priority
    #new_job = Jobs(job_type, input_data, limit_count, status=status, tag=tag, batch=batch, priority=priority)
    db.session.add(tmp_job)
    db.session.flush()
    job_id = tmp_job.id
    db.session.add(tmp_job)
    db.session.commit()
    logging.info("insert a job of %s" % job_type)
    return job_id

# 更新任务状态，并且对回传数据进行处理
def update_job_status(data):
    job_id = data.get('id')
    status = data.get('status')
    #result = str({'result':result})
    spend_time = data.get('spend_time', -1)
    return_data = data.get('return_data')
    return_count = data.get('count', 0 if status < 0 else 1)
    result = json.dumps(data.get('result', ''))
    error = json.dumps(data.get("error", ""))
    tmp_job = Jobs.get_by_job_id(job_id=job_id)
    if not tmp_job:
        return 0
    # 判断是否进行回调操作
    if status == 2:
        # return_data为None的话，则不需要回传
        if return_data == None:
            status = 3
    """
        else:
            try:
                return_data = json.loads(return_data)
                data['return_data'] = return_data
            except:
                pass
            p = Process(target=operate_return_data, args=(data, ))
            p.dameon = False
            p.start()
    """
    if status in [-1, -2]:
        logging.error(result)
    # 任务失败的话 如果limit_count > 0 说明有重跑的机会, 进行重跑
    # 没有重跑机会 就更新数据库相关结果
    if int(status) < 0 and tmp_job.limit_count > 0:
        tmp_job.status = 0
        tmp_job.clear = 0
        tmp_job.limit_count -= 1
    else:
        tmp_job.status = status
        tmp_job.return_count = return_count
        tmp_job.result = result
        tmp_job.spend_time = spend_time
        if int(status) < 0:
            tmp_job.error = error
    db.session.add(tmp_job)
    db.session.commit()
    logging.info("update job status of %s" % (job_id))
    return 1

# 获取 可以筛选的信息, limit_time(默认 30分钟内)以内的
def get_distinct_select(limit_time=30):
    status = [''] + [-2, -1, 0, 1, 2, 3]
    res = db.session.execute("select distinct job_type from jobs")
    job_type = [''] + [x['job_type'] for x in utils.convert_rowproxy_to_dict(res.fetchall())]
    job_type = list(filter(None, job_type))
    res = db.session.execute("select distinct batch from jobs")
    batch = [''] + [x['batch'] for x in utils.convert_rowproxy_to_dict(res.fetchall())][::-1]
    batch = list(filter(None, batch))
    begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 30 * 60))
    res = db.session.execute("select distinct machine_id  from machine where update_time > '%s' " % begin_time)
    machine_id = [''] + [x['machine_id'] for x in utils.convert_rowproxy_to_dict(res.fetchall())][::-1]
    machine_id = list(filter(None, machine_id))
    result = {}
    result['job_type'] = job_type
    result['batch'] = job_type
    result['machine_id'] = machine_id
    result['status'] = ['-2', '-1', '0', '1', '2', '3']
    return result

# 返回所有任务类型
def get_all_job_type():
    data = {}
    for line in JobFile.query.all():
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
        line['job_file'] = ''
        data[line['job_type']] = line
    return data

# 根据 job_type tag 获取相关的任务
def get_job(job_type, tag, machine_id):
    tag = tag.replace(" ", "")
    tag_list = tag.split(",")
    query_0 = Jobs.query
    query_0 = query_0.filter(Jobs.status==JOB_WAITING)
    query_0 = query_0.filter(or_(Jobs.tag == '', Jobs.tag.in_(tag_list)))
    # 如果存在特定的job_type，就筛选特定的job_type
    if job_type:
        query_0 = query_0.filter(job_type=job_type)
    # 获取最新的任务
    data = query_0.order_by(Jobs.priority.desc(), Jobs.create_time).first()
    if data:
        data = data.to_json()
        tmp_job_type = data['job_type']
        tmp_job_file = JobFile.get_by_job_type(job_type=tmp_job_type)
        version = tmp_job_file.version
        data['input_data'] = utils.parse_data_to_json(data['input_data'])
        # 对该id的任务便更新状态为1
        Jobs.query.filter_by(id=data['id']).update({'status':JOB_RUNNING, 'machine_id':machine_id, "version":version})
        db.session.commit()
    else:
        data = {}
    data = [data]
    return data

# 根据 machine_id 获取需要操作的任务
def get_job_operation(machine_id):
    operation_id = []
    for tmp_job in Jobs.query.filter_by(status=JOB_TO_KILL).filter_by(machine_id=machine_id).all():
        operation_id.append(tmp_job.id)
    return operation_id

# 重跑任务
def rerun_job(job_id, job_type, batch, machine_id):
    # 参数中 需要至少存在1个
    if not (machine_id or job_id or job_type or batch):
        return 0
    tmp_query = Jobs.query
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
    tmp_query.filter(Jobs.status!=JOB_WAITING).filter(Jobs.status!=JOB_RUNNING).update({'status':0, 'machine_id':''}, synchronize_session=False)
    db.session.commit()
    return 1

# 重跑任务
def delete_job(job_id, job_type, batch, machine_id):
    # 参数中 需要至少存在1个
    if not (machine_id or job_id or job_type or batch):
        return 0
    tmp_query = Jobs.query
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
    tmp_query.filter(Jobs.status!=JOB_RUNNING).delete(synchronize_session=False)
    db.session.commit()
    return 1

# 强制关闭任务
def kill_job(job_id, job_type, batch, machine_id):
    # 参数中 需要至少存在1个
    if not (machine_id or job_id or job_type or batch):
        return 0
    tmp_query = Jobs.query
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
    tmp_query.filter(Jobs.status.in_([JOB_WAITING, JOB_RUNNING])).update({'status':JOB_TO_KILL}, synchronize_session=False)
    db.session.commit()
    return 1

# 复制任务
def copy_job(job_id, job_type, batch, machine_id):
    # 参数中 需要至少存在1个
    if not (machine_id or job_id or job_type or batch):
        return 0
    tmp_query = Jobs.query
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
        new_job = Jobs()
        new_job.job_type = line.job_type
        new_job.input_data = line.input_data
        new_job.limit_count = line.limit_count
        new_job.status = JOB_WAITING
        new_job.tag = line.tag
        new_job.batch = line.batch
        new_job.priority = line.priority
        db.session.add(new_job)
    db.session.commit()
    return 1

# 获取job的列表页信息
def get_job_list(job_type, batch, machine_id, status, offset_num=0, limit_num=10, clear=None):
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
    if clear:
        query_0 = query_0.filter_by(clear=clear)
    # 计算数据量
    count = db.session.query(sqlalchemy.func.count(1)).select_from(query_0.subquery()).one()[0]
    data = query_0.order_by(Jobs.id.desc()).limit(limit_num).offset(offset_num).all()
    if data:
        data = utils.convert_rowproxy_to_dict(data)
        for line in data:
            line['spend_time'] = round(line['spend_time'], 4) if line['spend_time'] else 0
            line["result"] = ""
    else:
        data = []
    result = {}
    result['data'] = data
    result['count'] = count
    return result

# 获取 job 的统计描述信息
def get_job_summary(job_type, batch):
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
    result = utils.convert_rowproxy_to_dict(tmp)
    for line in result:
        line['spend_time'] = round(line['spend_time'], 4) if line['spend_time'] else 0
    return result

# 获取历史时间段的任务运行信息
# TODO 注意加缓存
def get_history_job(limit_time=24):
    # 取最近 24 小时的数据
    time_0 = time.strftime("%Y-%m-%d %H:00:00", time.localtime(time.time() - limit_time * 3600))
    mysql_0 = "select group_concat(distinct a.job_type) as job_type, sum(a.return_count * (case when a.status = 3 then 1 else 0 end)) as count, count(1) as task_num, sum(a.spend_time) / sum(case when a.status = 3 then 1 else 0 end) as spend_time, sum(case when a.status = 0 then 1 else 0 end) as waiting_task, sum(case when a.status = 1 then 1 else 0 end) as working_task, sum(case when a.status = 3 then 1 else 0 end) as finished_task, sum(case when a.status = -1 then 1 else 0 end) as failed_task, min(a.create_time) "
    # 注意 sqlite3 和 mysql 的时间处理的语法有差异
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        mysql_0 += " as begin_time, strftime('%Y-%m-%d %H:00:00', max(a.update_time)) as update_time from jobs a where update_time > " + "'%s'" % time_0 + " group by strftime('%Y-%m-%d %H:00:00', `update_time`)"
    else:
        mysql_0 += " as begin_time, DATE_FORMAT(max(a.update_time),'%Y-%m-%d %H:00:00') as update_time from jobs a where update_time > " + "'%s'" % time_0 + " group by DATE_FORMAT(`update_time`,'%Y-%m-%d %H:00:00')"
    res = db.session.execute(mysql_0)
    data = utils.convert_rowproxy_to_dict(res.fetchall())
    # 数据再处理
    series = []
    tmp_data = {}
    for i in range(limit_time):
        time_1 = time.strftime("%Y-%m-%d %H:00:00", time.localtime(time.time() - (limit_time - i - 1) * 3600))
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
    # 对数据进行重新赋值处理
    for tmp_key in key_list:
        tmp_dic_0 = deepcopy(tmp_dic)
        tmp_dic_0["name"] = tmp_key
        for tmp_series in series:
            tmp_dic_0['data'].append(data[tmp_series][tmp_key])
            if tmp_key in summary_data:
                summary_data[tmp_key] += data[tmp_series][tmp_key]
        front_end_data[tmp_key] = tmp_dic_0
    result = {}
    result['data'] = data
    result['front_end_data'] = front_end_data
    result['series'] = series
    result['title'] = key_list
    result['summary_data'] = summary_data
    return result

# 清洗任务
def clear_job(job_id):
    # 参数中 需要至少存在1个
    #if not (machine_id or job_id or job_type or batch):
    #    return 0
    if type(job_id) is not list:
        job_id = [job_id]
    tmp_query = Jobs.query
    tmp_query = tmp_query.filter(Jobs.id.in_(job_id))
    data = tmp_query.all()
    for line in data:
        line.result = ""
        line.clear = 1
        db.session.add(line)
    db.session.commit()
    return 1
