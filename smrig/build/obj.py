import logging
import os

import maya.cmds as cmds
from smrig import env
from smrig.lib import pathlib

log = logging.getLogger("smrig.build.obj")

maya_file_extention = "obj"
maya_file_type = "OBJexport"


def export_objs(nodes=None, asset=None, description=""):
	"""
	Save obj maya file.

	:param asset:
	:param description:
	:return:

	"""

	nodes = nodes if nodes else cmds.ls(sl=1)

	if not nodes:
		log.error("Nothing Selected")

	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	directory = pathlib.normpath(os.path.join(os.path.dirname(env.asset.get_rigbuild_path()), "objs"))
	print
	directory
	pathlib.make_dirs(directory)

	for node in nodes:

		if description:
			description = "_" + description
		file_name = "{}{}_obj.OBJ".format(node, description)
		file_path = pathlib.normpath(os.path.join(directory, file_name))
		cmds.file(file_path, type="OBJExport", es=True)

		log.info("Saved obj scene {}".format(pathlib.normpath(file_path)))


def load_objs(objs=None,
              asset=None,
              action="import"):
	"""
	Load obj file.
	:param asset:
	:param asset:
	:param description:

	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	directory = pathlib.normpath(os.path.join(os.path.dirname(env.assets.get_rigbuild_path(asset)), "objs"))

	for obj in objs:
		file_name = "{}.obj".format(obj)
		file_path = pathlib.normpath(os.path.join(directory, file_name))
		print(file_path)
		cmds.file(file_path, i=1, type='OBJ')

# directory = r"X:\Character\Blend_Shapes\SHAPES_MASTER\Shapes_Mouth"
# obj_paths = pathlib.get_files(directory, search="*.obj")
# for obj in obj_paths:
# 	print obj
# 	file_name = obj.split(r"/")[-1]
# 	obj_name = file_name.replace ("_sd3.obj", "")
# 	nn = cmds.file(obj, i=1, type='OBJ', returnNewNodes=True)
# 	node =  [n for n in nn if "Shape" not in n]
# 	new_name=cmds.rename (node, obj_name)
