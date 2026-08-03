import requests
from datetime import datetime
import json
from publish_core.database.core import FastSg



sg = FastSg().client



def get_person_dingid(id):
    pp = sg.find_one('HumanUser', [['id', 'is', id]], ['sg_dingtalk_id'])
    if not pp:
        raise ValueError('找不到这个人员')
    return pp['sg_dingtalk_id']



def send_simple_message(msg, title, user):
    uid = user['sg_dingtalk_id']
    url = 'http://192.168.20.217:8080/ding/msg/simple'

    mk_message = """
# 🚀 来自发布工具的通知!
___
* ***通知信息:***  {message}
***
| 任务信息 | 查询结果 |
| :--- | :---: | 
| 版本类型 | {type} | 
| 版本名称 | {vname} |
| 任务名称 | {tname} |
| 实体名称 | {ename} |
***
`发送时间： {datetime_now}`
""".format(
           message=msg['message'],
           type=msg['type'],
           vname=msg['vname'],
           tname=msg['tname'],
           ename=msg['ename'],
           datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    post_data = {
        'title': title ,
        'text': mk_message
    }
    ret = requests.post(
        url=url,
        params={'user_id': uid},
        data=json.dumps(post_data)
    )

    ret.raise_for_status()
    return ret.json()