import maya.standalone

maya.standalone.initialize(name="python")

import maya.cmds as cmds

cmds.file(
    'D:/HWT/repository/newpublish/test/mayatest.mb',
    open=True,
    force=True
)

objects = cmds.ls(dag=True, type="transform")

for obj in objects:
    print(obj)