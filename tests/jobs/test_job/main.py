#coding=utf-8
def work(data):
    result = "multi_job_test %s" % data
    return result

def count(data):
    return len(data)

if __name__ == "__main__":
    print(work(1))
