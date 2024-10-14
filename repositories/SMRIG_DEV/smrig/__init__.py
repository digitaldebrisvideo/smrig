import os
import maya.cmds as cmds
import smrig.mel

base_path = os.path.normpath(os.path.dirname(__file__)).replace('\\', '/')

# source mel code
smrig.mel.source()

# load required maya plugins
required_plugins = [
	"quatNodes",
	"matrixNodes",
	"poseInterpolator"
]

for plugin in required_plugins:
	if not cmds.pluginInfo(plugin, q=True, l=True):
		cmds.loadPlugin(plugin)

# handle icon paths
ico_path = os.path.join(os.path.dirname(__file__), "gui", "icons/")

exec("""
try:
    from importlib import reload
except:
    pass
""")
