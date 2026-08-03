from publish_core.config import Config
import xml.etree.ElementTree as ET
from pathlib import Path




def unpack_xml(xml_file: Path, publish_type='Dailies') -> tuple[list[Path], list[Path]]:
    tree = ET.parse(xml_file)
    root = tree.getroot()

    dir_folder = Path(__file__).parent.parent / 'components'
    check_files = []
    process_files = []

    checkcontainer = root.find('checkcontainer')
    if checkcontainer is not None:
        for check_group in checkcontainer.findall('check_group'):
            group_name = check_group.get('name')
            if publish_type == "Dailies" and group_name != "Dailies": continue
            for check in check_group.findall('check'):
                check_type = check.get('type') or'gen'
                check_name = check.get('name') or ''
                fpath = dir_folder / check_type / 'check' / (check_name + '.py')
                if not fpath.exists():
                    raise FileNotFoundError(
                        f'file {fpath} not exists!'
                    )
                check_files.append(fpath)

    processcontainer = root.find('processcontainer')
    if processcontainer is not None:
        for process in processcontainer.findall('process'):
            proc_type = process.get('type') or'gen'
            proc_name = process.get('name') or ''
            mode = process.get('mode')
            if publish_type == "Dailies" and mode != "Dailies": continue
            fpath = dir_folder / proc_type / 'process' / (proc_name + '.py')
            if not fpath.exists():
                raise FileNotFoundError(
                    f'file {fpath} not exists!'
                )
            process_files.append(fpath)

    return check_files, process_files