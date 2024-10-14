import os

import maya.cmds as cmds
from smrig import dataio
from smrig import env
from smrig.lib import pathlib, attributeslib


# def unreal_export_prep_scene(model_grp="mocap_model_GRP", skel_grp="mocap_skel_offset_GRP", fbx_grp="optitrack_skel_offset_GRP"):

def unreal_export_prep_scene():
	"""

	:param model_grp:
	:param skel_grp:
	:param opti_skel_grp:
	:return:
	"""

	if cmds.objExists("joints_GRP"):
		cmds.select("joints_GRP", hi=True)
		nodes = cmds.ls(sl=1)
		attrs = ["translate", "rotate", "scale"]
		attributeslib.connection.break_connections(nodes=nodes, attributes=attrs, user_defined=True)

	if cmds.objExists("noxform_GRP"):
		cmds.delete("noxform_GRP")

	if cmds.objExists("none"):
		cmds.delete("none")

	if cmds.objExists("mocap_model_GRP"):
		cmds.delete("mocap_model_GRP")

	if cmds.objExists("mocap_GRP"):
		cmds.delete("mocap_GRP")

	if cmds.objExists("parts_GRP"):
		cmds.delete("parts_GRP")
	#
	# if cmds.objExists(fbx_grp):
	#     cmds.delete (fbx_grp)
	#
	# if cmds.objExists(model_grp):
	#     cmds.parent(model_grp, world=True)
	#     cmds.rename(model_grp, "mocap_lib_GRP")
	#
	# if cmds.objExists (skel_grp):
	#     cmds.parent(skel_grp, world=True)
	#     cmds.rename(skel_grp, "skel_export_grp")

	# blend_poses="blend_poses_GRP"
	# if cmds.objExists (blend_poses):
	#     cmds.parent (blend_poses, world=True)

	# if cmds.objExists("rig_GRP"):
	#     cmds.delete("rig_GRP")
	#
	# command = 'searchReplaceNames "Mocap_Maya_" "Maya_" "all"'
	# mm.eval(command)
	#
	# command = 'searchReplaceNames "Blends_MC" "Blends" "all"'
	# mm.eval(command)
	#
	# cmds.setAttr("mocap_lib_GRP.visibility", 1)

	print("Prep For Export Done")


def bind_clothing_lib_grps(asset=None):
	"""

	:return:
	"""
	if not asset:
		asset = env.asset.get_asset()
		if not asset:
			return ("asset not set")
	asset_path = env.asset.get_data_path()
	library_path = pathlib.normpath(os.path.join(asset_path.replace(asset, "LIBRARIES"), "mocap", "skinCluster"))
	if os.path.isdir(library_path):
		# print() (library_path)
		lib_files = pathlib.get_files(library_path)
		print(lib_files)
		if lib_files:
			for lib_file in lib_files:
				dataio.load(lib_file)
