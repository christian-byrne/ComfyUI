import logging
import os
from rich.logging import RichHandler
from comfy.performance_utils.config import Config


class Logger:
    def __init__(self, logger_name: str, level: str):
        self.logger_base = logging.getLogger(logger_name)
        self.last_message = None
        self.config = Config()
        global thread_locked_file
        self.log_file = self.config["log_file"]
        cur_index = 1
        while os.path.exists(f"{self.log_file}_{cur_index}.log"):
            cur_index += 1
            if not self.config["logfile_policy"]["unlimited_logs"]:
                if cur_index > self.config["logfile_policy"]["max_logs"]:
                    existing_logs = [
                        f
                        for f in os.listdir()
                        if f.startswith(self.log_file) and f.endswith(".log")
                    ]
                    sorted_mtime = sorted(
                        [(os.path.getmtime(f), f) for f in existing_logs],
                        key=lambda x: x[0],
                    )
                    oldest_index = sorted_mtime[0][1].split("_")[-1].split(".")[0]
                    os.remove(f"{self.log_file}_{oldest_index}.log")
                    cur_index = 1

        self.log_file = f"{self.log_file}_{cur_index}.log"

        # Base formatters (no handlers added yet)
        self.console_formatter = logging.Formatter("%(message)s")
        self.file_formatter = logging.Formatter(
            "%(asctime)s - %(message)s", datefmt="%H:%M:%S"
        )

        match level:
            case "ERROR":
                self.level = logging.ERROR
            case "WARNING":
                self.level = logging.WARNING
            case "INFO":
                self.level = logging.INFO
            case "DEBUG":
                self.level = logging.DEBUG
            case _:
                self.level = logging.INFO

        self.logger_base.setLevel(self.level)
        self.logger_base.propagate = False

    def __call__(self):
        return self

    def _log(self, level, msg, *args, to_console=True, to_file=False, **kwargs):
        if msg != self.last_message:
            # Dynamically add handlers based on arguments
            if to_console:
                console_handler = RichHandler(
                    rich_tracebacks=True, tracebacks_show_locals=True, markup=True
                )
                console_handler.setFormatter(self.console_formatter)
                self.logger_base.addHandler(console_handler)

            if to_file:
                file_handler = logging.FileHandler(self.log_file)
                file_handler.setFormatter(self.file_formatter)
                self.logger_base.addHandler(file_handler)

            self.logger_base._log(level, msg, args, kwargs)
            self.last_message = msg

            # Remove handlers to avoid duplicates on next call
            for handler in self.logger_base.handlers[:]:
                self.logger_base.removeHandler(handler)

    # Logging methods with duplicate message check
    def debug(self, msg, *args, to_console=True, to_file=False, **kwargs):
        if self.level <= logging.DEBUG:
            self._log(
                logging.DEBUG,
                msg,
                *args,
                to_console=to_console,
                to_file=to_file,
                **kwargs,
            )

    def info(self, msg, *args, to_console=True, to_file=False, **kwargs):
        if self.level <= logging.INFO:
            self._log(
                logging.INFO,
                msg,
                *args,
                to_console=to_console,
                to_file=to_file,
                **kwargs,
            )

    def warning(self, msg, *args, to_console=True, to_file=False, **kwargs):
        if self.level <= logging.WARNING:
            self._log(
                logging.WARNING,
                msg,
                *args,
                to_console=to_console,
                to_file=to_file,
                **kwargs,
            )

    def warn(self, msg, *args, to_console=True, to_file=False, **kwargs):
        if self.level <= logging.WARNING:
            self._log(
                logging.WARNING,
                msg,
                *args,
                to_console=to_console,
                to_file=to_file,
                **kwargs,
            )

    def error(self, msg, *args, to_console=True, to_file=False, **kwargs):
        if self.level <= logging.ERROR:
            self._log(
                logging.ERROR,
                msg,
                *args,
                to_console=to_console,
                to_file=to_file,
                **kwargs,
            )


    def critical(self, msg, *args, to_console=True, to_file=False, **kwargs):
        if self.level <= logging.CRITICAL:
            self._log(
                logging.CRITICAL,
                msg,
                *args,
                to_console=to_console,
                to_file=to_file,
                **kwargs,
            )

    def exception(self, msg, *args, to_console=True, to_file=False, **kwargs):
        self._log(
            logging.ERROR,
            msg,
            *args,
            to_console=to_console,
            to_file=to_file,
            exc_info=True,
            **kwargs,
        )

    def note(self, msg, *args, to_console=True, to_file=False, **kwargs):
        if self.level == logging.INFO:
            self._log(
                logging.INFO,
                f"[bold blue]{msg}[/bold blue]",
                *args,
                to_console=to_console,
                to_file=to_file,
                **kwargs,
            )

    def set_level(self, level):
        self.logger_base.setLevel(level)
