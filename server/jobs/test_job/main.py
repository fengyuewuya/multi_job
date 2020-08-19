#coding=utf-8
import requests
import work_test
def work(data):
    result = work_test.work(data["input_data"])
    count = len(result.keys())
    return {'count':count, 'result':result['seed'], 'return_data':result}

if __name__ == "__main__":
    print(work({"input_data":{"seed":1}}))
