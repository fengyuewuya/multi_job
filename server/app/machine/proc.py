from app import db
from app import app
from app.models import Machine
#@cache.cached(timeout=3)
# limit_time 为检测多久时间间隔内的机器 ， offline_time 表示超过offline_time 时间，判断为失联
def get_machine_info(limit_time=30, offline_time=5):
    begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - limit_time * 60))
    res = db.session.execute("select *  from machine where update_time > '%s' " % begin_time)
    data = convert_rowproxy_to_dict(res.fetchall())
    for line in data:
        # -1 表示机器关机了
        if line['status'] == -1:
            continue
        tmp_update_time = time.mktime(time.strptime(line['update_time'], "%Y-%m-%d %H:%M:%S"))
        if (time.time() - offline_time * 60) > tmp_update_time:
            line['status'] = -2
        #if (time.time() - 10 * 60) > tmp_update_time:
        #    line['status'] = -2
    return data
