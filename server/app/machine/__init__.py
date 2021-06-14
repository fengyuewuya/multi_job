from flask import Blueprint
#rc = rediscache.RedisClient(app, conf_key = "default", key_prefix="APIV10")
router = Blueprint('machine', __name__, url_prefix='/machine')

from .views import *
