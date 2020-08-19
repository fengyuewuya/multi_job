import requests
import random
def work(data):
    seed = data['seed']
    random.seed(seed)
    tmp = random.random()
    return {"seed":seed, "random":tmp}

if __name__ == "__main__":
    print(work({"seed":1}))

