import time
import os
import platform
from functools import wraps

# import torch
import inspect
import objgraph
import cProfile
from snakeviz.cli import main as snakeviz_main
import tracemalloc

from comfy.performance_utils.log import Logger
from comfy.performance_utils.config import Config


config = Config()
logger = Logger(__name__, Config()["log_level"])()


def open_file(file_path):
    file_path = os.path.normpath(os.path.abspath(file_path))
    if platform.system() == "Windows":
        os.system(f"start {file_path}")
    elif platform.system() == "Darwin":
        os.system(f"open {file_path}")
    else:
        os.system(f"xdg-open {file_path}")


def profile(func):
    def wrapper(*args, **kwargs):
        if not config["profiler"]["enabled"]:
            return func(*args, **kwargs)

        pr = cProfile.Profile()
        pr.enable()
        retval = func(*args, **kwargs)
        pr.disable()

        stats_filename = config["profiler"]["stats_filename"]
        pr.dump_stats(stats_filename)

        if config["profiler"]["print_stats"]:
            pr.print_stats()
        if config["profiler"]["auto_open_stats"]:
            open_file(stats_filename)
        if config["profiler"]["auto_open_visualization"]:
            snakeviz_main([stats_filename])

        return retval

    return wrapper


def tracemalloc_profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not config["tracemalloc"]["enabled"]:
            return func(*args, **kwargs)

        p = config["tracemalloc"]["print"]
        l = config["tracemalloc"]["log"]

        tracemalloc.start()
        result = func(*args, **kwargs)
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")
        # other_data = {
        #     "total_peak_size_MB": tracemalloc.get_traced_memory()[1] / 1024 / 1024,
        #     "total_peak_blocks_MB": tracemalloc.get_traced_memory()[0] / 1024 / 1024,
        # }

        results_num = int(config["tracemalloc"]["results_limit"])
        logger.debug(
            f"Tracemalloc results (top {results_num}):", to_console=p, to_file=l
        )
        res ="\n".join([str(stat) for stat in top_stats[:results_num]]) 
        logger.debug(res, to_console=p, to_file=l)
        # logger.debug(other_data)

        tracemalloc.stop()
        return result

    return wrapper


# def cuda_malloc_profile(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if not config["cuda_malloc"]["enabled"]:
#             return func(*args, **kwargs)

#         p = config["cuda_malloc"]["print"]
#         l = config["cuda_malloc"]["log"]

#         torch.cuda.reset_peak_memory_stats()
#         result = func(*args, **kwargs)
#         peak_memory = torch.cuda.max_memory_allocated()
#         logger.debug(
#             f"Peak memory allocated: {peak_memory / 1024 / 1024:.2f} MB",
#             to_console=p,
#             to_file=l,
#         )
#         return result

#     return wrapper


def objgraph_log(func):
    def wrapper(*args, **kwargs):
        if not config["objgraph"]["enabled"]:
            return func(*args, **kwargs)

        p = config["objgraph"]["print"]
        l = config["objgraph"]["log"]

        logger.debug(f"Objects before {func.__name__} call:", to_console=p, to_file=l)
        if p:
            objgraph.show_growth(limit=config["objgraph"]["items_limit"])
        if l:
            objgraph.show_growth(
                limit=config["objgraph"]["items_limit"], file=logger.log_file
            )
        result = func(*args, **kwargs)

        # other_data = {
        #     "leaking_objects": repr(objgraph.get_leaking_objects()),
        #     # "proper_modules": objgraph.is_proper_module(),
        #     "most_common_types": objgraph.most_common_types(limit=config["objgraph"]["items_limit"]),
        # }
        logger.debug(f"Objects after {func.__name__} call:", to_console=p, to_file=l)
        logger.debug(
            objgraph.show_growth(limit=config["objgraph"]["items_limit"]),
            to_console=p,
            to_file=l,
        )
        if p:
            objgraph.show_growth(limit=config["objgraph"]["items_limit"])
        if l:
            objgraph.show_growth(
                limit=config["objgraph"]["items_limit"], file=logger.log_file
            )

        # logger.debug(other_data, to_console=p, to_file=l)

        return result

    return wrapper


def report_time_taken(func):
    def wrapper(*args, **kwargs):
        if not config["time_reporting"]["enabled"]:
            return func(*args, **kwargs)

        p = config["time_reporting"]["print"]
        l = config["time_reporting"]["log"]

        time_start = time.time()
        if config["time_reporting"]["start_message"]:
            logger.info(f"Started {func.__name__}", to_console=p, to_file=l)

        result = func(*args, **kwargs)
        time_end = time.time()
        time_diff = time_end - time_start
        past_threshold = time_diff > float(config["time_reporting"]["threshold_to_log"])
        if config["time_reporting"]["end_message"] and past_threshold:
            logger.info(
                f"Finished {func.__name__} in {time_end - time_start:.2f} seconds.",
                to_console=p,
                to_file=l,
            )

        return result

    return wrapper


def print_func_frame_details(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not config["frame_details_reporting"]["enabled"]:
            return func(*args, **kwargs)

        p = config["frame_details_reporting"]["print"]
        l = config["frame_details_reporting"]["log"]

        messages = [f"Function {func.__name__} — "]
        if config["frame_details_reporting"]["args"]:
            messages.append(f"Args: {args}")
        if config["frame_details_reporting"]["kwargs"]:
            messages.append(f"Kwargs: {kwargs}")
        if config["frame_details_reporting"]["return"]:
            messages.append(f"Return: {func(*args, **kwargs)}")
        if config["frame_details_reporting"]["frame"]:
            frame = inspect.currentframe()
            messages.append(f"Frame: {frame}")
        if config["frame_details_reporting"]["code"]:
            code = inspect.getsource(func)
            messages.append(f"Code: {code}")
        if config["frame_details_reporting"]["locals"]:
            locals_ = func.__globals__
            messages.append(f"Locals: {locals_}")
        if config["frame_details_reporting"]["globals"]:
            globals_ = func.__globals__
            messages.append(f"Globals: {globals_}")

        logger.debug(", ".join(messages), to_console=p, to_file=l)
        return func(*args, **kwargs)

    return wrapper


def count_total_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not config["call_counter"]["enabled"]:
            return func(*args, **kwargs)

        p = config["call_counter"]["print"]
        l = config["call_counter"]["log"]

        wrapper.count += 1
        logger.debug(
            f"{func.__name__} has been called {wrapper.count} times",
            to_console=p,
            to_file=l,
        )
        return func(*args, **kwargs)

    wrapper.count = 0
    return wrapper
