from flask import Blueprint

#rc = rediscache.RedisClient(app, conf_key = "default", key_prefix="APIV10")
router = Blueprint('job_file', __name__, url_prefix='/job_file')
from .views import *
