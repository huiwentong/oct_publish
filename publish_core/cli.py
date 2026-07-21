from dataclasses import dataclass, field, asdict, is_dataclass, fields
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from publish_core.database import SGEntity


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
class PublishStack:
    process_files: list[Path]
    check_files: list[Path]
    status: PublishStatus = field(init=False, default=PublishStatus.WAITING)
    message: str = field(init=False, default='starting……')
    create_time: datetime = field(init=False, default_factory=datetime.now)



@dataclass(slots=True)
class PublishCli:

    user: str
    task_id: int

    publish_type: PublishType = PublishType.DAILY

    preview_paths: list[str | Path] | None = None
    comment: str | None = None
    publish_tag_id: int | None = None
    version_num: int | None = None
    dcc_file: str | None = None

    custom_data: dict[str, Any] = field(default_factory=dict)
    notify: list[str] = field(default_factory=list)
    
    task_entity: SGEntity | None = field(init=False, default=None)
    tag_entity: SGEntity | None = field(init=False, default=None)
    stack: PublishStack | None = field(init=False, default=None)

    

    def __post_init__(self):
        pass
        

    @property
    def task(self) -> SGEntity:
        if self.task_entity is None:
            self.task_entity = SGEntity(
                "Task",
                self.task_id
            )

        return self.task_entity
    

    



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