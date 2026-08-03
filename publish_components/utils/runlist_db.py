from psycopg2.pool import SimpleConnectionPool
from publish_core.config import Config
from publish_components.utils.register import unpack_xml


class RunListDB():
    runlist_pool = None

    def __init__(self, runlist_file, file_first=False, publish_type='Dailies' ,step='mod') -> None:
        self.check_files = self.process_files = []
        if file_first:
            self.check_files, self.process_files = unpack_xml(runlist_file, publish_type)
        else:
            RunListDB.connect_db(Config())
            if self.runlist_pool:
                self.check_files, self.process_files = self.find_file_from_db(step, publish_type)
            else:
                self.check_files, self.process_files = unpack_xml(runlist_file, publish_type)
                
        if not self.check_files or not self.process_files:
            raise RuntimeError('failed to find runlist data!')


    def find_file_from_db(self, step, publish_type):
        if not self.runlist_pool:
            raise RuntimeError('can not find pool!')
        conn = self.runlist_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM runlist
                """
            )
            rows = cursor.fetchall()
        finally:
            self.runlist_pool.putconn(conn)

        return [], []


    @classmethod
    def connect_db(cls, config):
        try:
            if not cls.runlist_pool:
                pool = SimpleConnectionPool(
                    1,
                    3,
                    host=config.data['runlist_db']['db_addr'],
                    port=config.data['runlist_db']['db_port'],
                    user=config.data['runlist_db']['db_user'],
                    password=config.data['runlist_db']['db_password'],
                    database=config.data['runlist_db']['db_name'],
                    connect_timeout=2
                )
                cls.runlist_pool = pool
        except Exception as e:
            cls.runlist_pool = None