#coding=utf-8
import requests
import pymysql
def work(data):
    conn = pymysql.connect(host='localhost', user='root', password='', db='')
    cursor = conn.cursor()
    # 更新下表
    search_word = data['result']
    count = data['count']
    if not count:
        count = 0
    cursor.execute("update tmp_word set count=count+%s where word = %s", (count, search_word))
    count_1 = 0
    for line in data['return_data'].keys():
        if 'http' not in line:
            continue
        shop_id = line.strip().split('/')[2]
        try:
            cursor.execute("insert into tmp_id values(%s, '', 1, 0, default, default ) on duplicate key update count=count+1, status=1", (shop_id))
        except:
            pass
        count_1 += 1
        if count_1 % 100 == 0:
            conn.commit()
    conn.commit()
    conn.close()
