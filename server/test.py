#coding=utf-8
from app import app
from app.env import APP_CONFIG

if __name__ == "__main__":
    host = APP_CONFIG["host"]
    port = APP_CONFIG["port"]
    debug = APP_CONFIG["debug"]
    app.run(host=host, port=port, debug=debug, threaded=True)
