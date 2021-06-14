from flask import Blueprint

#rc = rediscache.RedisClient(app, conf_key = "default", key_prefix="APIV10")
router = Blueprint('jobs', __name__, url_prefix='/jobs')
from .views import *
