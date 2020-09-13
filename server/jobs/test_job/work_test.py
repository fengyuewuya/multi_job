import requests
import random
import time
def work(data):
    seed = data['seed']
    time.sleep(seed)
    random.seed(seed)
    tmp = random.random()
    return {"seed":seed, "random":tmp}

if __name__ == "__main__":
    print(work({"seed":1}))

