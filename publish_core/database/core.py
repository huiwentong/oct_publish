from shotgun_api3.shotgun import Shotgun
import inspect
import threading
import gc
import traceback
from publish_core.database.utils import get_databaseinfo



class ThreadSafeShotgun:
    def __init__(self, base_url=None, script_name=None, api_key=None, shotgun_ins=None,  **kwargs):
        self.lock = threading.Lock()
        print("Initializing Shotgun connection...")
        if shotgun_ins:
            self._sg = shotgun_ins
        elif base_url:
            self._sg = Shotgun(base_url, script_name, api_key, **kwargs)


    def find(self, entity_type, filters, fields, **kwargs):
        with self.lock:
            try:
                result = self._sg.find(entity_type, filters, fields, **kwargs)
                return result
            except Exception as e:
                raise
    
    def shotgun(self):
        return self._sg

    def create(self, *arges, **kwargs):
        with self.lock:
            return self._sg.create(*arges, **kwargs)

    def update(self, *arges, **kwargs):
        with self.lock:
            return self._sg.update(*arges, **kwargs)

    def delete(self, *arges, **kwargs):
        with self.lock:
            return self._sg.delete(*arges, **kwargs)

    def find_one(self, *arges, **kwargs):
        with self.lock:
            return self._sg.find_one(*arges, **kwargs)



class FastSg(object):
    _instance = None
    no_need_to_init = False
    add,key,pw = get_databaseinfo()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FastSg, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not FastSg.no_need_to_init:
            shotgun = self.get_shogun()
            if not shotgun:
                self.client = ThreadSafeShotgun(base_url=self.add, script_name=self.key, api_key=self.pw)
            else:
                self.client = ThreadSafeShotgun(shotgun_ins=shotgun)
        FastSg.no_need_to_init = True

    def get_shogun(self):
        objs = gc.get_objects()
        for o in objs:
            try:
                if isinstance(o, Shotgun):
                    print('find shotgun!')
                    return o
            except Exception as e:
                continue
        return None