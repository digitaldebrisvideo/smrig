import logging
import os

import maya.cmds as cmds
from smrig import env
from smrig.lib import pathlib, utilslib

log = logging.getLogger("smrig.build.guide")

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"


def save_scene(asset=None, description=None, version=None):
	"""
	Save guides maya file.

	:param str/None asset:
	:param str description:
	:param int version:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()
	description = description if description else env.asset.get_variant()

	if not asset:
		log.error("Asset not set")
		return

	file_name = "{}_work_{}".format(asset, description)
	directory = pathlib.normpath(os.path.join(os.path.dirname(env.asset.get_rigbuild_path()), "scenes"))
	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	cmds.file(rename=file_path)
	cmds.file(save=True, type=maya_file_type)

	log.info("Saved work scene: {}".format(pathlib.normpath(file_path)))


def load_scene(asset=None,
               description="primary",
               version=None,
               action="open",
               file_path=""):
	"""
	Load model file.

	:param str asset:
	:param str description:
	:param int version:
	:param action: Options are import, open, reference
	:param str file_path: Optionaly load specified file path
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not file_path:
		file_name = "{}_work_{}".format(asset, description)
		directory = pathlib.normpath(os.path.join(os.path.dirname(env.assets.get_rigbuild_path(asset)), "scenes"))
		version_object = pathlib.Version(directory, file_name, maya_file_extention)
		file_path = version_object.get_load_version_path(version)

	return utilslib.scene.load(file_path, action=action, rnn=True)
