#coding=utf-8
from app import app
from app import db
from app.env import APP_CONFIG
from flask_script import Shell
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
def make_shell_context():
    return dict(app=app, db=db)

manager = Manager(app)
migrate = Migrate(app, db, render_as_batch=True, compare_type=True)
manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))

@manager.command
def test():
    print("test")

if __name__ == "__main__":
    #host = all_config["host"]
    #port = all_config["port"]
    #debug = all_config["debug"]
    #app.run(host=host, port=port, debug=debug, threaded=True)
    manager.run()
