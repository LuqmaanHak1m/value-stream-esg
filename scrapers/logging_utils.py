import datetime


class LoggerMixin:
    def log(self, message):
        if getattr(self, "verbose", False):
            now = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] {message}")