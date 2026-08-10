import traceback
import hou

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查工程文件版本号是否和shogun版本一致
    """
    try:
        bname = hou.hipFile.basename()
        ver_num = bname.split(".")[-2]
        logger.info(f'+++++ 版本号为{process_data["version_num"]}')
        if ver_num != str(process_data["version_num"]):
            return f'{bname}工程版本号与待提交的shotgun版本号不一致， 请手动提升后再发布'
    except:
        return traceback.format_exc()


