#coding=utf-8
import requests
import os
import json
def work(return_data):
    save_dir = open('dir').read().strip()
    for stock_id in return_data:
        tmp_dir = os.path.join(save_dir, stock_id)
        with open(tmp_dir, 'w') as w:
            w.write(json.dumps(return_data[stock_id], indent=2))

if __name__ == "__main__":
    return_data = {'sz000829': [{'date': '2021-06-21 15:00:00', 'open': 7.01, 'high': 7.03, 'low': 6.99, 'close': 7.02, 'volume': 2421500}]}
    work(return_data)
