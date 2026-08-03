import logging
import os
from logging.handlers import RotatingFileHandler
import getpass
from publish_core.config import Config
from psycopg2.pool import SimpleConnectionPool


class LogDB:
    def __init__(self, pool:SimpleConnectionPool) -> None:
        self.pool = pool

    def insert_log(self, data):
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO publish_log
                (
                    level,
                    user_name,
                    message,
                    logger,
                    file,
                    line
                )
                VALUES
                (%s,%s,%s,%s,%s,%s)
                """,
                (
                    data["level"],
                    data["user"],
                    data["message"],
                    data["logger"],
                    data["file"],
                    data["line"],
                )
            )
            conn.commit()
        finally:
            self.pool.putconn(conn)




class DatabaseHandler(logging.Handler):

    def __init__(self, db:LogDB):
        super().__init__()
        self.db = db


    def emit(self, record):
        try:
            msg = self.format(record)
            log_data = {
                "level": record.levelname,
                "message": msg,
                "logger": record.name,
                "file": record.filename,
                "line": record.lineno,
                "user": getattr(record, "user", "")
            }

            self.db.insert_log(log_data)
        except Exception:
            self.handleError(record)


class WidgetHandler(logging.Handler):
    def __init__(self, logwidget):
            super().__init__()
            self.widget = logwidget

    def emit(self, record):
            try:
                log_data = {
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "logger": record.name,
                    "file": record.filename,
                    "line": record.lineno,
                    "user": getattr(record, "user", "")
                }
                msg = self.format(record)
                self.widget.append_log(msg)

            except Exception:
                self.handleError(record)



class PublishLog:
    _initialized = False
    logDB = None

    @classmethod
    def setup(
        cls,
        name="PUBLISHER",
        log_widget=None,
        level=logging.DEBUG
    ):
        if cls._initialized:
            return


        logger = logging.getLogger(name)
        logger.setLevel(level)

        SUCCESS = logging.INFO + 1
        logging.addLevelName(SUCCESS, "SUCCESS")

        if logger.handlers:
            return


        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s "
                "[%(levelname)s] "
                "user:%(user)s "
                "%(name)s:%(lineno)d - "
                "%(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)

        cls.connect_db(Config())
        if cls.logDB:
            db_handler = DatabaseHandler(
                cls.logDB
            )
            db_handler.setFormatter(formatter)
            logger.addHandler(db_handler)

        if log_widget:
            wd_handler = WidgetHandler(log_widget)
            wd_handler.setFormatter(formatter)
            logger.addHandler(wd_handler)

        logger.addHandler(console)
        cls._initialized = True


    def __init__(self, log_widget=None, name="PUBLISHER") -> None:
        self._logger = None
        if not PublishLog._initialized:
            PublishLog.setup(log_widget=log_widget, name=name)
        self._logger = logging.getLogger(name)
        self._user = getpass.getuser()
        if not self.logDB:
            self.info('没有连接日志数据库！')

    @classmethod
    def connect_db(cls, config):
        try:
            if not cls.logDB:
                pool = SimpleConnectionPool(
                    1,
                    3,
                    host=config.data['log_db']['db_addr'],
                    port=config.data['log_db']['db_port'],
                    user=config.data['log_db']['db_user'],
                    password=config.data['log_db']['db_password'],
                    database=config.data['log_db']['db_name'],
                    connect_timeout=2
                )
                cls.logDB = LogDB(pool=pool)
        except Exception as e:
            cls.logDB = None

        


    def warning(self, msg):
        if not self._logger:
            raise RuntimeError('can not find logger!')
        self._logger.warning(
            msg,
            extra={
                'user': self._user
            }
        )


    def info(self, msg):
        if not self._logger:
                raise RuntimeError('can not find logger!')
        self._logger.info(
            msg,
            extra={
                'user': self._user
            }
        )


    def error(self, msg):
        if not self._logger:
                raise RuntimeError('can not find logger!')
        self._logger.error(
            msg,
            extra={
                'user': self._user
            }
        )


    def debug(self, msg):
        if not self._logger:
            raise RuntimeError('can not find logger!')
        self._logger.debug(
            msg,
            extra={
                'user': self._user
            }
        )


    def critical(self, msg):
        if not self._logger:
            raise RuntimeError('can not find logger!')
        self._logger.critical(
            msg,
            extra={
                'user': self._user
            }
        )


    def success(self, msg):
        if not self._logger:
            raise RuntimeError('can not find logger!')
        self._logger.log(
            logging.INFO + 1,
            msg,
            extra={
                'user': self._user
            }
        )