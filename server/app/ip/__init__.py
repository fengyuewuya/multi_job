from flask import Blueprint
#rc = rediscache.RedisClient(app, conf_key = "default", key_prefix="APIV10")
router = Blueprint('ip', __name__, url_prefix='/ip')

from .views import *
