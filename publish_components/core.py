from dataclasses import dataclass, fields, field
from typing import Any
import ast
from abc import ABC, abstractmethod
from qtpy.QtWidgets import QWidget
import traceback
import inspect
import importlib
from importlib import util
import sys
from pprint import pprint
import os
import tempfile
from pathlib import Path
import subprocess
from publish_core.database.entity import SGEntity
from publish_components.utils.register import unpack_xml
from publish_components.utils.runlist_db import RunListDB

DCC_COMMANDS = {
    
    'cmd':
        'rez-env oct_publish -- python {script} {scene}',

    '.hip':
        'rez-env oct_houdini houdini-20.5 -- hython {script} {scene}',

    '.ma':
        'rez-env maya-2024 oct_maya -- mayapy {script} {scene}',

    '.mb':
        'rez-env maya-2024 oct_maya -- mayapy {script} {scene}',

    '.nk':
        'rez-env nuke-14.1v8 oct_nuke nuke_plugins -- nukex -t {script} {scene}',

    '.katana':
        'rez-env katana-7.5v2 ktoa-4.3.7.1 oct_katana -- katanaBin --script {script} {scene}',
}

DCC_OPENSCEN = {
    'cmd': ['', ''],
    '.hip': ['', '    scene = sys.argv[1]\n    hou.hipFile.load(scene,suppress_save_prompt=False,ignore_load_warnings=False)'],
    '.mb': ['import maya.standalone\nmaya.standalone.initialize(name="python")', '    scene = sys.argv[1]\n    cmds.file(scene,open=True,force=True)'],
    '.ma': ['import maya.standalone\nmaya.standalone.initialize(name="python")', '    scene = sys.argv[1]\n    cmds.file(scene,open=True,force=True)'],
    '.nk': ['', '    scene = sys.argv[1]\n    nuke.scriptOpen(scene)'],
    '.katana': ['', '    scene = sys.argv[1]\n    KatanaFile.Load(scene)'],
}

class Signal:
    def __init__(self, signal_data_type, logger):
        self.data_type = signal_data_type
        self.logger = logger
        self.data=None
        self.callbacks = []
    
    def set_loop(self, loop):
        self._loop = loop


    def emit(self, signal_data):
        
        if not isinstance(signal_data, self.data_type):
            raise ValueError('Wrong type!')
        for func in self.callbacks:
            func(signal_data)


    def connect(self, func):
        self.callbacks.append(func)

    def disconnect(self, func):
        self.callbacks.remove(func)






class Component():
    def __init__(self, parent, script_path, gui: bool, log, ctype="Dailies"):
        self.parent = parent
        self.type = ctype
        self.script_path = Path(script_path)
        self.name = self.script_path.stem
        self.import_module = set()
        self.main_script = None
        self.status = 'waiting'
        self.log = log
        self.check_script()
        if gui:
            self.gui_register()


    def run(self):
        self.status = self.gui_main(self.parent.submit_form, self.parent.process_data, self.parent.ui_parent, self.log)


    def gui_main(self, submit_data:dict, process_data:dict, parent_widget=None, logger=None):
        pass



    def get_function_doc(self, node: ast.FunctionDef):
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            return node.body[0].value.value

        return None


    def check_script(self):
        try:
            if not self.script_path.exists():
                raise FileNotFoundError(self.script_path)
            source = self.script_path.read_text(encoding="utf-8")
            tree = ast.parse(source,filename=str(self.script_path))
            main_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        code = "import " + alias.name
                        if alias.asname:
                            code += f" as {alias.asname}"
                        self.import_module.add(code)
                if isinstance(node, ast.ImportFrom):
                    names = []
                    for alias in node.names:
                        name = alias.name
                        if alias.asname:
                            name += f" as {alias.asname}"
                        names.append(name)
                    code = f"from {node.module} import {', '.join(names)}"
                    self.import_module.add(code)

                if isinstance(node, ast.FunctionDef):
                    if node.name == "main":
                        main_node = node
                        lines = source.splitlines()
                        start = node.body[0].lineno - 1
                        end = node.end_lineno
                        self.main_script = "\n".join(lines[start:end])

            if not main_node:
                raise RuntimeError(
                    f"component file error {self.script_path}, script missing main() function"
                )

            expected_args = [
                "submit_data",
                "process_data",
                "parent_widget",
                "logger",
            ]

            param_names = [
                arg.arg
                for arg in main_node.args.args
            ]

            if param_names != expected_args:
                raise RuntimeError(
                    f"component file error {self.script_path}.\n"
                    f"main() signature mismatch.\n"
                    f"Expected: {expected_args}\n"
                    f"Got: {param_names}"
                )

            doc = self.get_function_doc(main_node)

            if not doc:
                raise RuntimeError(f"component file error {self.script_path}, main() should have docstring")
            
            has_return = False
            for node in ast.walk(main_node):
                if isinstance(node, ast.Import):
                    raise RuntimeError(
                        f"component file error {self.script_path}, main() should not contain import"
                    )
                if isinstance(node, ast.ImportFrom):
                    raise RuntimeError(
                        f"component file error {self.script_path}, main() should not contain import from"
                    )
                if isinstance(node, ast.Return):
                    has_return = True
            if not has_return:
                raise RuntimeError(f"component file error {self.script_path} main() should has return")
            return ""
        except Exception:
            traceback.print_exc()
            return traceback.format_exc()


    def gui_register(self):
        try:
            spec = util.spec_from_file_location(
                "component_script",
                self.script_path
            )
            if spec is None:
                raise RuntimeError(
                    f"component file error {self.script_path}, Cannot load module: {self.script_path}"
                )
            module = util.module_from_spec(spec)
            if spec.loader is None:
                raise RuntimeError(
                    f"component file error {self.script_path}, Missing loader: {self.script_path}"
                )
            spec.loader.exec_module(module)
            self.gui_module = module
            self.gui_main = module.main
            return ""
        except Exception:
            traceback.print_exc()
            return traceback.format_exc()
    
    def gui_reload(self):
        try:
            spec = util.spec_from_file_location(
                "component_script",
                self.script_path
            )
            if spec is None:
                raise RuntimeError(
                    f"Cannot load module: {self.script_path}"
                )
            module = util.module_from_spec(spec)
            if spec.loader is None:
                raise RuntimeError(
                    f"Missing loader: {self.script_path}"
                )
            spec.loader.exec_module(module)
            self.gui_module = module
            self.gui_main = module.main
            return ""

        except Exception:
            traceback.print_exc()
            return traceback.format_exc()



@dataclass
class InterFace():
    # Data to be read from user input
    log: Any
    task_entity: SGEntity
    submit_type: str | None = None
    # Data from cli data
    process_data:dict | None = None

    ui_parent: QWidget | None = None
    is_gui: bool = False
    dcc_file: str | None = None
    dcc: str | None = None
    runlist: str | None = None
    all_complete: bool = False
    input_form: dict = field(default_factory=dict)


    process_files: list[Path] = field(init=False, default_factory=list)
    check_files: list[Path] = field(init=False, default_factory=list)

    check_stat:int = field(init=False, default=0)
    proc_stat:int = field(init=False, default=0)

    process_comps:list = field(default_factory=list)
    check_comps:list = field(default_factory=list)


    def init_process_data(self):
        if not self.process_data:
            raise ValueError('process_data is None')
        task = SGEntity('Task', self.process_data['task_id'])
        self.process_data['task_name'] = task.content
        self.process_data['step_name'] = task.step.short_name
        self.process_data['step_id'] = task.step.id
        self.process_data['entity_name'] = task.entity.code
        self.process_data['entity_id'] = task.entity.id
        self.process_data['entity_status'] = task.entity.sg_status_list
        self.process_data['project_name'] = task.project.code
        self.process_data['project_id'] = task.project.id



    def get_all_check_process(self):
        if not self.submit_type:
            raise ValueError('submit_type is None')
        module_name = self.__class__.__module__
        module = sys.modules.get(module_name)
        module_file = module.__file__ if module and module.__file__ else __file__

        if self.runlist:
            runlist = Path(self.runlist)
        else:
            runlist = Path(module_file).parent / 'runlist.xml'
            
        if not runlist.exists():
            raise FileNotFoundError(f"can not find file {runlist}")
        
        db = RunListDB(runlist_file=runlist, file_first=True if self.runlist else False, publish_type=self.submit_type, step=Path(module_file).parent.stem)
        self.check_files = db.check_files
        self.process_files = db.process_files
        self.process_data = {'filetypes': db.file_types}


    def fill_submit_form(self):
        if not hasattr(self, 'submit_form'):
            raise ValueError('can not found submit form')
        
        if (not self.is_gui) and (not self.input_form):
            raise ValueError('need property input_form')
        
        if not self.input_form:
            return
        
        for k,v in getattr(self, 'submit_form').items():
            if not self.input_form.get(k):
                raise ValueError(f'lack for submitproperty {k}')
            getattr(self, 'submit_form')[k] = self.input_form[k]


    def generate_publish_script(self, scene_name):
        if scene_name != 'cmd':
            suffix = Path(scene_name).suffix.lower()
        else:
            suffix = 'cmd'
        head, body = DCC_OPENSCEN[suffix]
        

        all_imports = set()
        all_funcs = []
        funcs_template = """
import sys
from publish_core.log.core import PublishLog
{import_module}
{maya_standalone}


logger = PublishLog(name="TEMP_PYTHON")
def main():
    {load_file}
    parent_widget=None
    submit_data = {submit_data}
    process_data = {process_data}
    
{all_funcs}
if __name__ == "__main__":
    res = main()
    logger.error(res)
    if res:
        raise RuntimeError(res)
    
        """
        for check in self.check_files:
            c = Component(self, str(check), False, self.log)
            all_imports.update(c.import_module)
            all_funcs.append(c.main_script)
        
        for proc in self.process_files:
            c = Component(self, str(proc), False, self.log)
            all_imports.update(c.import_module)
            all_funcs.append(c.main_script)

        return funcs_template.format(
            maya_standalone = head,
            import_module='\n'.join(sorted(all_imports)),
            submit_data = getattr(self, 'submit_form'),
            process_data = self.process_data,
            all_funcs = '\n'.join(all_funcs),
            load_file=body
        )


    def run_in_cli(self):
        
        if not self.dcc_file:
            raise RuntimeError(f'In no-gui mode, the dcc argument is required.')
        if self.dcc_file != 'cmd':
            suffix = Path(self.dcc_file).suffix.lower()
        else:
            suffix = 'cmd'
        if suffix not in DCC_COMMANDS:
            raise RuntimeError(f'Unsupported dcc file: {suffix}')
        fd, python_script = tempfile.mkstemp(
            suffix='.py',
            prefix='publish_'
        )
        try:
            os.close(fd)
            with open(python_script, 'w', encoding='utf-8') as f:
                f.write(self.generate_publish_script(self.dcc_file))
            
            cmd = DCC_COMMANDS[suffix].format(
                script=str(Path(python_script).resolve()),
                scene='' if suffix=='cmd' else self.dcc_file
            )

            self.log.info(cmd)
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    self.log.info(f"stdout: {result.stdout}")
                self.all_complete = True
            except subprocess.CalledProcessError as e:
                self.log.error(f"stdout: {e.stdout}")
                self.log.error(f"stderror: {e.stderr}")
                
            
        except Exception:
            self.log.error(traceback.format_exc())
        finally:
            if os.path.exists(python_script):
                os.unlink(python_script)


    def check_submit_form(self):
        for k,v in getattr(self, 'submit_form').items():
            if not v:
                raise ValueError(f'has no property: {k}`s value ')
    

    def gui_build_check(self):
        self.check_comps.clear()
        if not self.process_data: return
        self.check_submit_form()
        for index, check in enumerate(self.check_files):
            if self.check_stat <= index:
                c = Component(self, str(check), True, self.log, self.process_data['filetypes'][0][index])
                self.check_comps.append(c)
                

    def gui_build_process(self):
        self.process_comps.clear()
        if not self.process_data: return
        self.check_submit_form()
        for index, process in enumerate(self.process_files):
            if self.proc_stat <= index:
                c = Component(self, str(process), True, self.log, self.process_data['filetypes'][1][index])
                self.process_comps.append(c)
                


    @abstractmethod
    def init_ui(self, parent):
        pass

    
    @abstractmethod
    def gui_pre_interface(self):
        pass

    
    @abstractmethod
    def gui_post_interface(self):
        pass
    
    def gui_init(self):
        self.gui_pre_interface()
        self.init_ui(self.ui_parent)
        self.gui_post_interface()

    def __post_init__(self):
        self.get_all_check_process()
        if not self.is_gui:
            self.init_process_data()
            self.fill_submit_form()
            self.check_submit_form()

    
if __name__ == "__main__":
    pass
    # c = Component('D:/HWT/repository/newpublish/publish_components/components/mod/check/check_dcc_rv.py', True)
    # c.gui_main({}, {})