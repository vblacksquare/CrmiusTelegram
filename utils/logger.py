
import os.path
from loguru import logger
import sys


def setup_logger(logs_path, log_level):
    log_path = os.path.join(logs_path, "debug.log")

    fmt = "<g>{time}</> | <lvl>{level}</> | <c>{extra[classname]}:{function}:{line}</> - {message}"

    logger.remove()
    logger.configure(extra={"classname": "None"})
    logger.add(log_path, backtrace=True, diagnose=True, level="DEBUG", format=fmt, rotation="1 day")
    logger.add(sys.stdout, backtrace=True, diagnose=True, level=log_level, format=fmt)
    logger.info("Started logging successfully")
