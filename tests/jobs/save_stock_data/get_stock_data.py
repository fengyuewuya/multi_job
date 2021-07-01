import requests
import random
import time
# 爬取一条数据，并返回给数据库
# 如何用 python 获取实时的股票数据？ - sheen的回答 - 知乎
# https://www.zhihu.com/question/438404653/answer/1717279374

def get_stock_data(id, scale, data_len):
    symsol = '股票代码'
    scale = scale
    data_len = data_len
    url = 'http://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={0}&scale={1}&datalen={2}'.format(id, scale, data_len)
    res = requests.get(url)
    data = res.json()
    bar_list = []
    data.reverse()
    for tmp_dict in data:
        bar = {}
        bar['date'] = tmp_dict['day']
        bar['open'] = float(tmp_dict['open'])
        bar['high'] = float(tmp_dict['high'])
        bar['low'] = float(tmp_dict['low'])
        bar['close'] = float(tmp_dict['close'])
        bar['volume'] = int(tmp_dict['volume'])
        bar_list.append(bar)
    return bar_list

if __name__ == "__main__":
    get_stock_data('sz000829', 30, 1)
