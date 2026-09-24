# coding=utf-8

from functools import lru_cache

from oct.pipeline.shotgun.models import Task
from publish_core.database.entity import FastSg


def check_is_internal_rig(task_id):
    sg = FastSg().client
    artist_list = []
    task_e = sg.find('Task', [['id', 'is', task_id]], ['task_assignees'])
    if task_e:
        for e in task_e[0]['task_assignees']:
            if e['type'] == 'Group':
                grp_e = sg.find_one('Group', [['id', 'is', e['id']]], ['name', 'sg_login'])
                artist_list.append(grp_e['sg_login'])
            else:
                person_e = sg.find_one('HumanUser', [['id', 'is', e['id']]], ['name', 'login'])
                artist_list.append(person_e['login'])

    print(artist_list)
    if 'kekedou' in artist_list:
        return False
    else:
        return True

# SG 上标记资产类别的 Tag id，资产没有这两个标签就是默认资产
MAYA_SCENE_TAG_ID = 1139
UE_SCENE_TAG_ID = 1140

MAYA_SCENE_TAG = 'maya_scene'
UE_SCENE_TAG = 'ue_scene'
DEFAULT_ASSET_TAG = 'default'

# get_asset_kind 的返回值反查 Tag id，给需要把标签写回 SG 的组件用
SCENE_TAG_IDS = {
    MAYA_SCENE_TAG: MAYA_SCENE_TAG_ID,
    UE_SCENE_TAG: UE_SCENE_TAG_ID,
}


@lru_cache(maxsize=None)
def get_asset_kind(task_id):
    """读取任务所属资产的标签，判断它属于哪一类资产。

    一次发布里几十个 check / process 都会调它，结果按 task_id 缓存。
    在 SG 上改完标签要让新值生效，调 get_asset_kind.cache_clear() 或重开发布器。

    Args:
        task_id: 任务 id，check / process 里从 process_data['task_id'] 取。

    Returns:
        str: MAYA_SCENE_TAG（传统 Maya 场景）、UE_SCENE_TAG（UE 场景，
            ASB 资产没打标签时也归这类）、DEFAULT_ASSET_TAG（普通单体资产，
            任务挂在镜头等非资产实体下时同样返回它）。
    """
    entity = Task.get(id=int(task_id)).entity
    if getattr(entity, 'entity_type', None) != 'Asset':
        return DEFAULT_ASSET_TAG

    # tags 是 multi_entity，Tag 没有对应 Model，懒加载回来可能是原始 dict 也可能是实例
    tag_ids = set()
    for tag in entity.tags or []:
        tag_ids.add(tag['id'] if isinstance(tag, dict) else getattr(tag, 'id', None))

    if MAYA_SCENE_TAG_ID in tag_ids:
        return MAYA_SCENE_TAG
    if UE_SCENE_TAG_ID in tag_ids:
        return UE_SCENE_TAG
    # ASB 是组装出来的场景，不该按单体资产的规范检查。没打标签时默认当 UE 场景，
    # 这样共用组件只判断 UE_SCENE_TAG 就够了：mod 环节的无标签资产仍是 DEFAULT_ASSET_TAG 照常全查
    # asb_split 环节的无标签 ASB 自动走轻量流程
    if entity.sg_asset_type == 'ASB':
        return UE_SCENE_TAG
    return DEFAULT_ASSET_TAG
