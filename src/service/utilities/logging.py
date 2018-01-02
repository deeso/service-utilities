from . import logging


class LoggingFactory(object):
    KEY = "LoggingFactory"
    FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    CLS_FMT = '[%(asctime)s - %(name)s] %(message)s'

    @classmethod
    def setup(cls, logger_name, log_type='console',
              log_level=logging.INFO, log_fmt=FMT,
              log_config=None, logging_json={}, host='0.0.0.0',
              port=514, facility='daemon', filename='/dev/log'):
        if log_type == 'config':
            cls.setup_config(logger_name, log_level, log_config, logging_json)
        elif log_type == 'remote_host':
            cls.setup_remote_host(logger_name, log_level, log_fmt, host,
                                  port, facility)
        elif log_type == 'local_syslog':
            cls.setup_local_syslog(logger_name, log_level, log_fmt,
                                   filename, facility)
        else:
            cls.setup_console(cls, logger_name, log_level, log_fmt)

    @classmethod
    def setup_config(cls, logger_name, log_level=logging.INFO,
                     log_config=None, logging_json={}):
        if log_config is not None:
            logging.config.fileConfig(log_config)
        elif len(log_config) > 0:
            logging.config.dictConfig(logging_json)
        else:
            logging.basicConfig(level=log_level)
        return logging.getLogger(logger_name)

    @classmethod
    def setup_console(cls, logger_name, log_level=logging.INFO, log_fmt=FMT):
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        formatter = logging.Formatter(log_fmt)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logging.getLogger(logger_name)

    @classmethod
    def setup_remote_host(cls, logger_name,
                          log_level=logging.INFO, log_fmt=FMT,
                          host='0.0.0.0', port=514, facility='daemon'):
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        ce = logging.handlers.SysLogHandler(address=(host, port),
                                            facility=facility)
        formatter = logging.Formatter(log_fmt)
        ce.setFormatter(formatter)
        logger.addHandler(ce)
        return logging.getLogger(logger_name)

    @classmethod
    def setup_local_syslog(cls, logger_name,
                           log_level=logging.INFO, log_fmt=FMT,
                           filename='/dev/log/', facility='daemon'):
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        ce = logging.handlers.SysLogHandler(address=filename,
                                            facility=facility)
        formatter = logging.Formatter(log_fmt)
        ce.setFormatter(formatter)
        logger.addHandler(ce)
        return logging.getLogger(logger_name)

    @classmethod
    def key(cls):
        return cls.KEY.lower()
