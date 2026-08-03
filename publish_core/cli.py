from dataclasses import dataclass, field, asdict, is_dataclass, fields, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from pprint import pprint
import inspect
import importlib
from importlib import util
from publish_core.database.entity import SGEntity, get_user, get_all_pp
from publish_components.core import InterFace
from publish_core.log.core import PublishLog


class PublishType(Enum):
    DAILY = "Dailies"
    SUBMIT = "Submit"
    PUBLISH = "Publish"


class PublishStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


        



@dataclass(slots=True)
class PublishCli:

    # core inputs
    user: SGEntity
    task_id: int
    gui:bool

    # core properties
    publish_type: PublishType = PublishType.DAILY

    # read from user inputs
    comment: str | None = None
    publish_tag_id: int | None = None
    version_num: int | None = None
    dcc_file: str | None = None
    runlist: str | None = None
    widget: Any | None = None
    log: PublishLog | None = None
    preview_paths: list[str | Path] = field(default_factory=list)
    notify: list[str] = field(default_factory=list)
    all_active_pp: list[dict] = field(default_factory=list)


    # User inputs derived from stack template, which vary depending on the template.
    input_form: dict[str, Any] = field(default_factory=dict)
    
    # auto build after initial
    task_entity: SGEntity | None = field(init=False, default=None)
    tag_entity: SGEntity | None = field(init=False, default=None)
    interface: InterFace | None = field(init=False, default=None)

    

    def __post_init__(self):
        self.task_entity = SGEntity('Task', self.task_id)


        # build interface based on the step of the task
        stepname = str(self.task_entity.step.short_name).lower()
        module_path = f'publish_components.components.{stepname}.interface'
        try:
            module = importlib.import_module(module_path)

        except ModuleNotFoundError as e:
            raise RuntimeError(
                f"Cannot load component interface: {module_path}"
            ) from e
        
        importlib.reload(module)
        
        if not hasattr(module, "CompInterface"):
            raise RuntimeError(
                f"{module_path} missing CompInterface"
            )
        
        
        if not self.gui:
            self.log = PublishLog()
            self.log.info('publish cli initial!!')
            if not self.dcc_file or not self.publish_tag_id or not self.comment or not self.preview_paths:
                raise RuntimeError(f'In no-gui mode, the dcc_file, publish_tag_id, comment, and preview_paths arguments are required.')
            self.tag_entity = SGEntity('Tag', self.publish_tag_id)
            self.interface = module.CompInterface(
                log=self.log,
                submit_type=self.publish_type.value,
                input_form=self.input_form,
                process_data=self.to_dict(),
                dcc_file=self.dcc_file,
            )
        else:
            self.all_active_pp = get_all_pp()
            self.interface = module.CompInterface(log=self.log, submit_type=self.publish_type.value, is_gui=True, ui_parent=self.widget, runlist=self.runlist)
        
        
    def init_interface_parent(self, widget):
        if not self.interface:
            raise RuntimeError('can not found interface!')
        self.interface.ui_parent = self.widget = widget
        self.interface.gui_init()


    def form_init(self, publish_tag_id, comment, preview_paths, notify, version_num):
         if not self.interface:
             raise RuntimeError('can not found interface!')
         self.publish_tag_id = publish_tag_id
         self.tag_entity = SGEntity('Tag', self.publish_tag_id)
         self.comment = comment
         self.notify = notify
         self.version_num = version_num
         self.preview_paths = preview_paths
         self.interface.process_data = self.to_dict()
         self.interface.fill_submit_form()


    def to_dict(self):
        process_data = {}
        for field in fields(self):
            k = field.name
            v = getattr(self, k)
            if k == 'all_active_pp':
                continue
            if isinstance(v, SGEntity):
                continue
            elif is_dataclass(v):
                continue
            elif is_dataclass(v):
                continue
            else:
                process_data[k] = v
        return process_data

    @property
    def task(self) -> SGEntity:
        if self.task_entity is None:
            self.task_entity = SGEntity(
                "Task",
                self.task_id
            )

        return self.task_entity
    

    def notify_pp(self):
        pass



def entity_asdict(obj):
    if isinstance(obj, SGEntity):
        return {
            k: entity_asdict(v)
            for k, v in obj._data.items()
        }
    
    if is_dataclass(obj):
        return {
            f.name: entity_asdict(
                getattr(obj, f.name)
            )
            for f in fields(obj)
        }
    if isinstance(obj, dict):
        return {
            k: entity_asdict(v)
            for k,v in obj.items()
        }
    if isinstance(obj, list):
        return [
            entity_asdict(v)
            for v in obj
        ]
    return obj


if __name__ == "__main__":

    pcli = PublishCli(
        user=get_user(), 
        task_id=143051, 
        input_form={'dcc_file': 'sss', 'test': 'dd'},
        gui=False,
        comment='asdasdasd', 
        publish_tag_id=282, 
        dcc_file='cmd', 
        preview_paths=['C:/Users/huiwentong/Pictures/873558788-86207417.png'])
    
    pprint(entity_asdict(pcli))