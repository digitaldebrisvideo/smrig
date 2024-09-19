import os

import maya.cmds as cmds

USE_FACILITY_PIPELINE = False
PATH_TEMPLATE = os.path.join(cmds.internalVar(userWorkspaceDir=True), "{job}", "{asset}", "rigbuild")
p = r"C:\Users\briol\Documents\General"
PATH_TEMPLATE = os.path.join(p, "{job}", "{asset}", "rigbuild")

# Set your default text editor. Make sure it works with: os.system("{} {}".format(prefs.get_editor(), file_path))
DEFAULT_EDITOR = "pycharm"

# Set default maya file type for saving maya scenes.
DEFAULT_FILE_TYPE = "mb"
