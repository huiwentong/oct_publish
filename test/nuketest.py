import nuke
import sys

print("************** nuke: *****************")
scene = sys.argv[1]
nuke.scriptOpen(scene)
for node in nuke.allNodes():
    print(node.name())