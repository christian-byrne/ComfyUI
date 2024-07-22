import json
import functools


def handle_exceptions(logger=None):
    def decorator(func):
        @functools.wraps(func)  # Preserve function metadata
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.exception(f"Exception occurred in '{func.__name__}': {e}")
                else:
                    pass
                    # print(f"Exception occurred: {e}")

        return wrapper

    return decorator


class NodeScanner:
    BLACKLISTS = None
    MAX_ARG_PREVIEW = 80
    LOG_ALL_IMPORTS = False

    def __init__(self):
        self.all_imports = set()
        self.import_violations = set()
        self.arg_violoations = set()
        self.call_violations = set()

    def trace_calls(self, frame, event, arg):
      self.scan_args(arg, frame)
      if event == "call" or event == "return":
          self.scan_calls(frame)
          self.scan_builtin_import_calls(frame)
          self.scan_calc_package_calls(frame)
          self.scan_import_frame_stripping(frame)
          self.scan_import_fromlist(frame)

      return self.trace_calls

    @staticmethod
    def get_blacklists(category):
        if NodeScanner.BLACKLISTS is None:
            with open("node_scanner_blacklists.json", "r") as f:
                NodeScanner.BLACKLISTS = json.load(f)

        return NodeScanner.BLACKLISTS[category]

    def log_results(self):
        with open("scan_results.log", "w") as f:
            f.write("IMPORT VIOLATIONS:\n")
            for violation in self.import_violations:
                f.write(f"\t{violation}\n")
            f.write("\nARG VIOLATIONS:\n")
            for violation in self.arg_violoations:
                f.write(f"\t{violation}\n")
            f.write("\nCALL VIOLATIONS:\n")
            for violation in self.call_violations:
                f.write(f"\t{violation}\n")
            if NodeScanner.LOG_ALL_IMPORTS:
                f.write("\nALL IMPORTS:\n")
                for imp in self.all_imports:
                    f.write(f"\t{imp}\n")

    @handle_exceptions()
    def scan_args(self, arg, frame):
        for bl_arg in NodeScanner.get_blacklists("args"):
            if bl_arg in repr(arg):
                preview = repr(arg)[
                    max(0, repr(arg).index(bl_arg) - 5) : min(
                        len(repr(arg)),
                        repr(arg).index(bl_arg) + NodeScanner.MAX_ARG_PREVIEW,
                    )
                ]
                arg_length = len(repr(arg))
                context = f"Function '{frame.f_code.co_name}'\n\tCalled with arg containing '{bl_arg}'\n\tPreview: {preview}\n\t(full arg length: {arg_length})\n\tLocation: {frame.f_code.co_filename}:{frame.f_lineno}"
                self.arg_violoations.add(context)

    @handle_exceptions()
    def scan_calls(self, frame):
        code = frame.f_code
        for bl_func_name in NodeScanner.get_blacklists("calls"):
            if bl_func_name == code.co_name:
                self.import_violations.add(repr(code.co_name))

    @handle_exceptions()
    def scan_builtin_import_calls(self, frame):
        """https://github.com/python/cpython/blob/69f2dc5c06e62b4a9eb4da8f0cd456cc09b998ed/Lib/importlib/_bootstrap.py#L1454"""
        function_vars = frame.f_locals
        module_var = function_vars["module"]
        if module_var:
            self.all_imports.add(repr(module_var.__name__))
            for bl_import_name in NodeScanner.get_blacklists("imports"):
                if bl_import_name in module_var.__name__:
                    self.import_violations.add(repr(module_var))

    @handle_exceptions()
    def scan_calc_package_calls(self, frame):
        """https://github.com/python/cpython/blob/69f2dc5c06e62b4a9eb4da8f0cd456cc09b998ed/Lib/importlib/_bootstrap.py#L1427"""
        function_vars = frame.f_locals
        package_var = function_vars["package"]
        if package_var:
            self.all_imports.add(repr(package_var.__name__))
            for bl_import_name in NodeScanner.get_blacklists("imports"):
                if bl_import_name in package_var.__name__:
                    self.import_violations.add(repr(package_var))

    @handle_exceptions()
    def scan_import_frame_stripping(self, frame):
        """https://github.com/python/cpython/blob/69f2dc5c06e62b4a9eb4da8f0cd456cc09b998ed/Lib/importlib/_bootstrap.py#L480"""
        if frame.f_code.co_name == "_call_with_frames_removed":
            args_var = frame.f_locals["args"]
            f_var = frame.f_locals["f"]
            if f_var == __import__:
                for import_arg in args_var:
                    self.all_imports.add(repr(import_arg))
                    for bl_import_name in NodeScanner.get_blacklists("imports"):
                        if bl_import_name in repr(import_arg):
                            self.import_violations.add(repr(args_var))

    @handle_exceptions()
    def scan_import_fromlist(self, frame):
        """https://github.com/python/cpython/blob/69f2dc5c06e62b4a9eb4da8f0cd456cc09b998ed/Lib/importlib/_bootstrap.py#L1390"""
        if frame.f_code.co_name == "_handle_fromlist":
            module_arg = frame.f_locals["module"]
            if module_arg:
                self.all_imports.add(repr(module_arg))
                for bl_import_name in NodeScanner.get_blacklists("imports"):
                    if bl_import_name in repr(module_arg):
                        self.import_violations.add(repr(module_arg))

            fromlist_arg = frame.f_locals["fromlist"]
            if fromlist_arg:
                for fromlist_item in fromlist_arg:
                    self.all_imports.add(repr(fromlist_item))
                    for bl_import_name in NodeScanner.get_blacklists("imports"):
                        if bl_import_name in repr(fromlist_item):
                            self.import_violations.add(repr(fromlist_item))