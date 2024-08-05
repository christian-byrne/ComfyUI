from comfy.performance_utils.config import Config
from comfy.performance_utils.log import Logger
from comfy.performance_utils.peformance_logging import *

config = Config()
logger = Logger(__name__, config["log_level"])()