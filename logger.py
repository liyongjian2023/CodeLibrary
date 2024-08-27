"""
 Function: General log lib for Python
 Usage: from logger import *
        log_debug("Debug message.")
"""
import sys
import time
import os
import inspect

DEBUG, INFO, WARN, ERROR, FATAL = range(5)

COLOR_RESET = "\033[0m"
COLOR_DEBUG = "\033[37m"
COLOR_INFO = "\033[34m"
COLOR_WARN = "\033[33m"
COLOR_ERROR = "\033[31m"
COLOR_FATAL = "\033[41;37m"

def get_current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class LogStream:
    def __init__(self, level, file, line, func):
        self._level = level
        self._file = file
        self._line = line
        self._func = func
        self._stream = sys.stderr

        # 构建日志信息
        log_message = f"{get_current_time()} {os.path.basename(file)}:{func}():{line} "
        log_message += f"{self.log_level_to_string(level)} "
        log_message += f"{self.log_level_color(level)}| "

        self._message = log_message

    def write(self, message):
        self._stream.write(self._message + message + COLOR_RESET + "\n")

    def log_level_to_string(self, level):
        return {
            DEBUG: "DEBUG",
            INFO: "INFO",
            WARN: "WARN",
            ERROR: "ERROR",
            FATAL: "FATAL"
        }.get(level, "UNKNOWN")

    def log_level_color(self, level):
        return {
            DEBUG: COLOR_DEBUG,
            INFO: COLOR_INFO,
            WARN: COLOR_WARN,
            ERROR: COLOR_ERROR,
            FATAL: COLOR_FATAL
        }.get(level, COLOR_RESET)

def LOG(level):
    frame = inspect.stack()[1]
    file = frame.filename
    line = frame.lineno
    func = frame.function
    return LogStream(level, file, line, func)

def log_debug(message):
    frame = inspect.stack()[1]
    LogStream(DEBUG, frame.filename, frame.lineno, frame.function).write(message)

def log_info(message):
    frame = inspect.stack()[1]
    LogStream(INFO, frame.filename, frame.lineno, frame.function).write(message)

def log_warning(message):
    frame = inspect.stack()[1]
    LogStream(WARN, frame.filename, frame.lineno, frame.function).write(message)

def log_error(message):
    frame = inspect.stack()[1]
    LogStream(ERROR, frame.filename, frame.lineno, frame.function).write(message)

def log_fatal(message):
    frame = inspect.stack()[1]
    LogStream(FATAL, frame.filename, frame.lineno, frame.function).write(message)
