import logging
import os
from logging.handlers import RotatingFileHandler
import getpass
from publish_core.config import Config
from psycopg2.pool import SimpleConnectionPool
import weakref

from qtpy.QtCore import QObject, Signal, Slot, QThread, Qt
from qtpy.QtWidgets import QApplication

# oct_publish 根目录，日志 file 字段记录相对它的路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _rel_path(path):
    try:
        path = os.path.relpath(path, _PROJECT_ROOT)
    except ValueError:
        # Windows 下跨盘符算不出相对路径，保留绝对路径
        pass
    return path.replace('\\', '/')

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
                    line,
                    project,
                    entity,
                    step
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    data["level"],
                    data["user"],
                    data["message"],
                    data["logger"],
                    data["file"],
                    data["line"],
                    data["project"],
                    data["entity"],
                    data["step"],
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
            # 时间、级别、用户、行号都有单独的列，message 只存原始内容
            msg = record.getMessage()
            log_data = {
                "level": record.levelname,
                "message": msg,
                "logger": record.name,
                "file": _rel_path(record.pathname),
                "line": record.lineno,
                "user": getattr(record, "user", ""),
                "project": PublishLog.project,
                "entity": PublishLog.entity,
                "step": PublishLog.step,
            }

            self.db.insert_log(log_data)
        except Exception:
            self.handleError(record)


class _WidgetLogBridge(QObject):
    """把任意线程的日志转发到主线程。"""

    log_requested = Signal(str)

    def __init__(self, handler):
        super().__init__()
        self._handler_ref = weakref.ref(handler)

    @Slot(str)
    def _append_on_main_thread(self, msg):
        handler = self._handler_ref()
        if handler is None:
            return

        widget = handler.widget
        if widget is None:
            return

        try:
            # 这里已经运行在 GUI 主线程
            widget.append_log(msg)
        except RuntimeError:
            # 窗口可能已经被 Qt 销毁
            pass


class WidgetHandler(logging.Handler):
    def __init__(self, logwidget):
        super().__init__()
        self.widget = logwidget

        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication is not initialized")

        self._bridge = _WidgetLogBridge(self)

        # 信号接收对象必须属于主线程。
        # 即使 Handler 是在工作线程创建的，也将桥接对象移过去。
        if self._bridge.thread() != app.thread():
            self._bridge.moveToThread(app.thread())

        self._bridge.log_requested.connect(
            self._bridge._append_on_main_thread,
            Qt.QueuedConnection
        )

    def emit(self, record):
        try:
            msg = self.format(record)
            # 从任何工作线程调用都只会排队发送消息。
            self._bridge.log_requested.emit(msg)

        except Exception:
            self.handleError(record)



class PublishLog:
    _initialized = False
    logDB = None
    # 当前发布任务的上下文，由 PublishCli 在确定任务后写入，写数据库日志时带上
    project = ''
    entity = ''
    step = ''

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
        else:
            self._logger = logging.getLogger(name)
            if log_widget:
                for handler in self._logger.handlers:
                    if isinstance(handler, WidgetHandler):
                        handler.widget = log_widget
                        break

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
            },
            # 跳过本封装方法，file/line 记录真正打日志的位置
            stacklevel=2
        )


    def info(self, msg):
        if not self._logger:
                raise RuntimeError('can not find logger!')
        self._logger.info(
            msg,
            extra={
                'user': self._user
            },
            # 跳过本封装方法，file/line 记录真正打日志的位置
            stacklevel=2
        )


    def error(self, msg):
        if not self._logger:
                raise RuntimeError('can not find logger!')
        self._logger.error(
            msg,
            extra={
                'user': self._user
            },
            # 跳过本封装方法，file/line 记录真正打日志的位置
            stacklevel=2
        )


    def debug(self, msg):
        if not self._logger:
            raise RuntimeError('can not find logger!')
        self._logger.debug(
            msg,
            extra={
                'user': self._user
            },
            # 跳过本封装方法，file/line 记录真正打日志的位置
            stacklevel=2
        )


    def critical(self, msg):
        if not self._logger:
            raise RuntimeError('can not find logger!')
        self._logger.critical(
            msg,
            extra={
                'user': self._user
            },
            # 跳过本封装方法，file/line 记录真正打日志的位置
            stacklevel=2
        )


    def success(self, msg):
        if not self._logger:
            raise RuntimeError('can not find logger!')
        self._logger.log(
            logging.INFO + 1,
            msg,
            extra={
                'user': self._user
            },
            # 跳过本封装方法，file/line 记录真正打日志的位置
            stacklevel=2
        )