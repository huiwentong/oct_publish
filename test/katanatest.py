from Katana import NodegraphAPI
from Katana import KatanaFile
import sys
print("************** ARGV: *****************")

scene = sys.argv[1]
KatanaFile.Load(scene)

for node in NodegraphAPI.GetAllNodes():
    print(
        node.getName(),
        node.getType()
    )