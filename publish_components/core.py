from dataclasses import dataclass, fields
from typing import Any
from abc import ABC, abstractmethod
from publish_core.cli import PublishCli
from qtpy.QtWidgets import QWidget



class Component():
    pass



@dataclass
class InterFace():
    cli: PublishCli
    ui_parent: QWidget | None = None
    dcc_file: str | None = None
    is_gui: bool = False


    @abstractmethod
    def init_ui(self):
        pass

    
    @abstractmethod
    def pre_interface(self):
        pass

    
    @abstractmethod
    def post_interface(self):
        pass
    

    def __post_init__(self):
        self.pre_interface()
        if self.is_gui:
            self.init_ui()
        self.post_interface()

    
