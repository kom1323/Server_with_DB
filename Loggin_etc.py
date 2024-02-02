import logging
from datetime import datetime


class LogFormatter:
    """
    formats the log for easy use
    """
    def __init__(self):
        self.request_number = 1

    def get_format(self, log_level, log_message, request_number):
        current_time = datetime.now()
        format_time = current_time.strftime("%d-%m-%Y %H:%M:%S.%f")[:-3]

        result = f"{format_time} {log_level}: {log_message} | request #{request_number} "
        return result



class RequestLogger:
    def __init__(self, formatter):
        self.request_logger = logging.getLogger("request_logger")
        self.request_logger.setLevel(logging.INFO)
        self.request_logger.addHandler(logging.FileHandler("requests.log"))
        self.request_logger.addHandler(logging.StreamHandler())

        self.formatter = formatter

    def request_info(self, log_level, http_verb, resource_name, request_number):
        self.request_logger.info(self.formatter.get_format(log_level, f"Incoming request | #{request_number} | resource: {resource_name} | HTTP Verb {http_verb}", request_number))

    def request_debug(self, log_level, duration, request_number):
        self.request_logger.debug(self.formatter.get_format(log_level, f"request #{request_number} duration: {duration}ms", request_number))

    def get_level(self):
        return self.request_logger.getEffectiveLevel()

    def set_level(self, level):
        if level == "ERROR":
            self.request_logger.setLevel(logging.ERROR)
        elif level == "INFO":
            self.request_logger.setLevel(logging.INFO)
        elif level == "DBUG":
            self.request_logger.setLevel(logging.DEBUG)


class TodoLogger:
    def __init__(self, formatter):
        self.todo_logger = logging.getLogger("todo_logger")
        self.todo_logger.setLevel(logging.INFO)
        self.todo_logger.addHandler(logging.FileHandler("todos.log"))

        self.formatter = formatter


    def todo_info(self, message, request_number):
        self.todo_logger.info(self.formatter.get_format("INFO", message, request_number))

    def todo_debug(self, message, request_number):
        self.todo_logger.debug(self.formatter.get_format("DEBUG", message, request_number))

    def todo_error(self, message, request_number):
        self.todo_logger.error(self.formatter.get_format("ERROR", f" {message}", request_number))

    def get_level(self):
        return self.todo_logger.getEffectiveLevel()

    def set_level(self, level):
        if level == "ERROR":
            self.todo_logger.setLevel(logging.ERROR)
        elif level == "INFO":
            self.todo_logger.setLevel(logging.INFO)
        elif level == "DEBUG":
            self.todo_logger.setLevel(logging.DEBUG)