from typing import Any
from publish_core.database.core import ThreadSafeShotgun, FastSg
import getpass
from pprint import pprint


class SGEntity:
    """
    Shotgun Entity Wrapper
    带有记忆系统
    当shotgun上有更新是需要flush一下Entity
    支持:
        entity.code
        entity.project.name
        entity.status.name
    """
    _sg: ThreadSafeShotgun | None = None


    @classmethod
    def connect_sg(cls):
        if cls._sg is None:
            cls._sg = FastSg().client

        return cls._sg


    def __init__(
        self,
        entity_type: str | Any,
        entity_id: int | Any,
        data: dict[str, Any] | Any | None = None,
        fields: list[str] | Any | None = None,
    ):
        self.connect_sg()
        self._entity_type = entity_type
        self._entity_id = entity_id

        if data is None:
            data = self._fetch(fields)

        self._data = data


    def _fetch(self, fields=None):

        if fields is None:
            fields = self._get_all_fields()
        if not self._sg:
            raise TypeError(
                "can not find sg"
            )
        entity = self._sg.find_one(
            self._entity_type,
            [
                ["id", "is", self._entity_id]
            ],
            fields
        )

        if entity is None:
            raise ValueError(
                f"{self._entity_type} with id {self._entity_id} not found"
            )
        else:
            return dict(entity)
        
    def flush(self, fields = None):
        keys = [
            k
            for k in self.__dict__
            if not k.startswith("_")
        ]

        for k in keys:
            self.__dict__.pop(k)

        self._data = self._fetch(fields)


    def _get_all_fields(self):

        """
        自动获取实体所有字段
        """
        if not self._sg:
            raise TypeError(
                "can not find sg"
            )
        
        schema = self._sg.shotgun().schema_field_read(
            self._entity_type
        )

        return list(schema.keys())


    def __getattr__(self, name):

        """
        属性访问核心
        """

        if name in self._data:

            value = self._data[name]

            return self._wrap(value, name)

        raise AttributeError(
            f"{self._entity_type} has no field '{name}'"
        )
    
    def __getitem__(self, key):
        if key in self._data:

            value = self._data[key]

            return self._wrap(value, key)

        raise AttributeError(
            f"{self._entity_type} has no field '{key}'"
        )


    def _wrap(self, value: Any, key:str | None = None) -> Any:

        """
        自动包装 entity
        """

        if isinstance(value, dict):
            if "type" in value and "id" in value:
                entity = SGEntity(
                    value["type"],
                    value["id"],
                )
                if key:
                    self.__dict__[key] = entity
                return entity


        elif isinstance(value, list):
            if isinstance(value[0], dict) and len(value) > 20:
                raise ValueError('this value contains too many entities, we do not suggests query shotgun entites with this method!')
            entity_list =  [
                self._wrap(item)
                for item in value
            ]
            if key:
                self.__dict__[key] = entity_list
            return entity_list

        return value


    def __repr__(self):
        return (
            f"<SGEntity "
            f"{self._entity_type} "
            f"id={self._entity_id}>"
        )


    @property
    def id(self):
        return self._entity_id


    @property
    def type(self):
        return self._entity_type


    def tiny_raw(self):
        tiny = {}
        for k, v in self._data.items():
            if k in ['id', 'type']:
                tiny[k] = v
        return tiny

    def raw(self):
        """
        获取原始shotgun dict
        """

        return self._data
    

def get_pros(user:SGEntity) -> list[SGEntity]:
    """Fetch all active projects from Shotgun."""
    sg = FastSg().client
    raw_list = sg.find(
        "Project",
        [["sg_status", "is", "Active"],
         ['users', 'is', user.tiny_raw()]
         ],
        ["id", "name", "code", "sg_status"],
    )
    return [
        SGEntity(r.get("type"), r.get("id"))
        for r in raw_list
    ]


def get_pro_entities(pro_entity: SGEntity) -> dict[str, list]:
    """Fetch Asset / Shot / Sequence belonging to a project, grouped by type."""
    sg = FastSg().client
    pro_filter = ["project", "is", pro_entity.tiny_raw()]
    fields = ["id", "code", "sg_status_list"]

    result: dict[str, list] = {}
    for etype in ("Asset", "Shot", "Sequence"):
        raw_list = sg.find(etype, [pro_filter], fields)
        result[etype] = raw_list
    return result


def get_entity_tasks(sg_entity: SGEntity) -> list:
    """Fetch all Tasks linked to a given entity."""
    sg = FastSg().client
    raw_list = sg.find(
        "Task",
        [["entity", "is", {"type": sg_entity.type, "id": sg_entity.id}]],
        ["id", "content", "sg_status_list", "task_assignees", "step", "sg_last_version", "entity"],
    )
    return raw_list


def get_my_tasks() -> list:
    """Fetch tasks assigned to the current user."""
    sg = FastSg().client
    user = get_user()
    raw_list = sg.find(
        "Task",
        [["task_assignees", "is", user.tiny_raw()]],
        ["id", "content", "sg_status_list", "task_assignees", "step", "sg_latestversion", "entity"],
    )
    return raw_list


def get_my_project_tasks(project: SGEntity) -> list:
    """Fetch tasks assigned to current user within a specific project."""
    sg = FastSg().client
    user = get_user()
    raw_list = sg.find(
        "Task",
        [
            ["task_assignees", "is", user.tiny_raw()],
            ["project", "is", project.tiny_raw()],
        ],
        ["id", "content", "sg_status_list", "task_assignees", "step", "sg_last_version", "entity"],
    )
    return raw_list

def get_history_version(task: SGEntity) -> list:
    sg = FastSg().client
    raw_list = sg.find(
        "Version",
        [
            ["sg_task", "is", task.tiny_raw()],
            ["sg_status_list", "is_not", 'omt'],
        ],
        ["sg_version_type", "code", "user", "created_at", "description"],
    )
    return raw_list

def get_user(user_name=None) -> SGEntity:
    """Fetch user to a given entity."""
    sg = FastSg().client
    if not user_name:
        user_name = getpass.getuser()
    user = sg.find_one(
        'HumanUser',
        [['login', 'is', user_name]],
        ['id']
    )
    if not user:
        raise ValueError(f'can not find user {user_name} in shotgun')
    return SGEntity('HumanUser', user.get('id'))
    
def get_all_pp() -> list:
    sg = FastSg().client
    users = sg.find(
        'HumanUser',
        [['sg_status_list', 'is_not', 'dis'], ['sg_dingtalk_id', 'is_not', None]],
        ['name', 'login', 'id', 'sg_dingtalk_id']
    )
    if not users:
        raise RuntimeError('can not find any pp')
    return users

if __name__ == "__main__":
    from pprint import pprint
    # entity = SGEntity("Task", 120705)
    # print(entity.content)
    # print(entity.project.asd)
    project = SGEntity('Project', 142)
    print(len(get_my_project_tasks(project)))