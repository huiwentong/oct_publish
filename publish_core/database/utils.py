from publish_core.config import Config

def get_databaseinfo():
    cfg = Config()
    key = cfg.get('db.db_key')
    pw = cfg.get('db.db_password')
    addr = cfg.get('db.db_addr')
    return addr, key, pw

