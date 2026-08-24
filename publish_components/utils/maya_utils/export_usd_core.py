import sys
import json
import traceback
import subprocess
import tempfile
from pathlib import Path
from publish_components.utils import maya_utils
from publish_components.utils.gen_func import get_utils_env

def batch_export_usd(maya_file, out_usd, **ars):
    arg_json = tempfile.mktemp(suffix=".json")
    with open(arg_json, "w") as f:
        json.dump(ars, f)

    script_path = Path(maya_utils.__file__).resolve().parent / "scripts/batch_export_usd.py"
    cmd = f'rez-env maya-2024 oct_maya -c "mayapy.exe {script_path} {maya_file} {out_usd} {arg_json}"'
    print("输出资产usd的cmd为: \n{}".format(cmd))
    try:
        py3 = sys.version_info[0] >= 3
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, env=get_utils_env())
        output_lines = []

        for line in iter(process.stdout.readline, b''):
            if py3:
                line_decoded = line.decode('utf-8', errors='replace')
            else:
                line_decoded = line  # Python 2 默认是 str
            sys.stdout.write(line_decoded)
            sys.stdout.flush()
            output_lines.append(line_decoded)

        process.stdout.close()
        process.wait()
        print(output_lines)

    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        msg = "Batch export usd failed!!! \nBecause:{}".format(traceback.print_exc())
        print(msg)

