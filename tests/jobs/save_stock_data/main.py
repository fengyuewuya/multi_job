#coding=utf-8
import requests
from get_stock_data import get_stock_data
def work(stock_id, time_sep, time_length):
    result = get_stock_data(stock_id, time_sep, time_length)
    count = len(result)
    result = {stock_id:result}
    return {'count':count, 'result':result, 'return_data':result}

if __name__ == "__main__":
    print(work('sz000829', 30, 1))
