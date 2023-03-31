###############################################
#  collection of logger and better handling of module logger with
#  * root setup
#  * colorized logger
#
# see:
#    https://stackoverflow.com/questions/15727420/using-logging-in-multiple-modules
#    https://github.com/microsoft/vscode-python/issues/6324

import logging


class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result


# see https://github.com/microsoft/vscode-python/issues/6324
class LogColorerFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        logging.Formatter.__init__(self, fmt, datefmt, style)

    def format(self, record):
        # Still apply the default formatter
        uncolored = logging.Formatter.format(self, record)

        reset = "\x1b[0m"

        color = "\x1b[37m"  # White (default, for DEBUG level)
        if (record.levelno >= logging.CRITICAL):
            color = "\x1b[41m\x1b[37m"  # Red bg, white text
        elif (record.levelno >= logging.ERROR):
            color = "\x1b[31m"  # Red text
        elif (record.levelno >= logging.WARNING):
            color = "\x1b[33m"  # Yellow text
        elif (record.levelno >= logging.INFO):
            color = "\x1b[36m"  # Cyan text

        # If the logged string is already colored in places, allow that to override this
        colored = color + uncolored.replace(reset, reset + color) + reset
        return colored


def logger_init():
    print("print in logger.logger_init()")
    print("print logger.py __name__: " + __name__)

    # get logger
    # logger = logging.getLogger(__name__) ## this was my mistake, to init a module logger here
    logger = logging.getLogger()  # root logger
    logger.setLevel(logging.DEBUG)

    # File handler
    # logfilename = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{filename}"
    # file = logging.handlers.TimedRotatingFileHandler(f"{path}{logfilename}", when="midnight", interval=1)
    # fileformat = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    # fileformat = logging.Formatter("%(asctime)s [%(levelname)s]: %(name)s: %(message)s")
    # file.setLevel(logging.INFO)
    # file.setFormatter(fileformat)

    # Stream handler
    stream = logging.StreamHandler()
    # streamformat = logging.Formatter("%(asctime)s [%(levelname)s:%(module)s] %(message)s")
    # streamformat = LogColorerFormatter(logging.BASIC_FORMAT)
    streamformat = LogColorerFormatter("%(asctime)s [%(levelname)s:%(module)s] %(message)s")
    stream.setLevel(logging.DEBUG)
    stream.setFormatter(streamformat)

    # Adding all handlers to the logs
    # logger.addHandler(file)
    logger.addHandler(stream)
    print_info(logger)


def logger_cleanUp():
    logging.getLogger().removeHandler(logging.StreamHandler())


def print_info(log: logging.Logger):
    log.critical("This is a critical problem.")
    log.error("This is an error.")
    log.warning("This is a warning.")
    log.info("This is information.")
    log.debug("This is a debug message.")
    log.info("# set up test for br")
