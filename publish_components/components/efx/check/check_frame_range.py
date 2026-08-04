import traceback
from pprint import pprint
from publish_core.database.entity import SGEntity


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查工程帧范围 与shotgun上的帧范围作对比
    """
    try:
        import hou
        task = SGEntity('Task', process_data['task_id'])

        start = int(task.entity.sg_cut_in)
        end = int(task.entity.sg_cut_out)

        logger.info(hou.playbar.frameRange())
        if hou.playbar.frameRange()[0] != start or hou.playbar.frameRange()[1] != end:
            return "帧范围与shotgun上的帧范围不一致!"
    except:
        return traceback.format_exc()