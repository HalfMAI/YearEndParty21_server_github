import logging

def _init_formatter_logger(logger_name, file_path):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(file_path, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(threadName)s] %(message)s '))
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(threadName)s] %(message)s '))

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def log_info(text):
    if g_infoLog == None:
        reset_logger(g_default_logger, g_dfeault_logger_path)
    g_infoLog.info(text)
    # print(text)

def log_warnning(text):
    if g_infoLog == None:
        reset_logger(g_default_logger, g_dfeault_logger_path)
    g_infoLog.warning(text)

def log_err(text, is_raise_Exception=True, exception_func=Exception, exception=None):
    if g_infoLog == None:
        reset_logger(g_default_logger, g_dfeault_logger_path)
    g_infoLog.error(text)
    if exception:
        g_infoLog.exception(exception)

    if is_raise_Exception:
        raise exception_func(text)

g_infoLog = None
g_default_logger = 'infoLog'
g_dfeault_logger_path = 'infoLog.log'
def reset_logger(logger_name, file_path):
    global g_infoLog
    global g_default_logger
    global g_dfeault_logger_path
    g_default_logger = logger_name
    g_dfeault_logger_path = file_path
    if g_infoLog != None:
        for handler in g_infoLog.handlers[:]:
            g_infoLog.removeHandler(handler)
    g_infoLog = _init_formatter_logger(logger_name, file_path)

reset_logger(g_default_logger, g_dfeault_logger_path)