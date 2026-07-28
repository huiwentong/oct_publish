import hou
import sys

print("************** hou: *****************")
scene = sys.argv[1]
hou.hipFile.load(scene,suppress_save_prompt=False,ignore_load_warnings=False)
node = hou.node('/obj/geo1/testgeometry_pighead1')
print(node.name())