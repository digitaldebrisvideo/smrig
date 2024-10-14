import logging
import os

import maya.cmds as cmds

# Compatibility for string types in both Python 2 and Python 3
import sys

if sys.version_info[0] < 3:
	string_types = (str, unicode)
else:
	string_types = (str,)

from smrig import env
from smrig import partslib
from smrig.lib import iolib
from smrig.lib import pathlib
from smrig.lib import utilslib
from smrig.lib.constantlib import GUIDE_GRP
from smrig.partslib.common import manager
from smrig.partslib.common import utils

log = logging.getLogger ("smrig.build.guide")

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"


def save_scene(asset=None, description="primary", version=None):
	"""
	Save guides maya file.

	:param str/None asset:
	:param str description:
	:param int version:
	:return:
	"""

	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not cmds.objExists(GUIDE_GRP):
		log.error("{} not in scene".format(GUIDE_GRP))

	file_name = "{}_guides_{}".format(asset, description)
	directory = pathlib.normpath(os.path.join(env.asset.get_rigbuild_path(), "guides"))
	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	cmds.select(GUIDE_GRP)
	cmds.file(file_path, options="v=0;", type=maya_file_type, es=True)
	log.info("Saved guide scene: {}".format(pathlib.normpath(file_path)))


def save_data(asset=None, description="primary", version=None):
	"""
	Save guides into a dataexporter file.

	:param str/None asset:
	:param str description:
	:param int version:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not cmds.objExists(GUIDE_GRP):
		log.error("{} not in scene".format(GUIDE_GRP))

	file_name = "{}_guides_{}".format(asset, description)
	directory = pathlib.normpath(os.path.join(env.asset.get_rigbuild_path(), "guides"))
	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, manager.template_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	data = manager.get_template_data()
	iolib.json.write(file_path, data)

	log.info("Saved guide dataexporter: {}".format(pathlib.normpath(file_path)))


def load_scene(asset=None,
               description="primary",
               version=None,
               action="import",
               namespace=None,
               rnn=False,
               new_file=True,
               force=False):
	"""
	Load guide maya file.

	:param str/None asset:
	:param str description:
	:param int version:
	:param str action: Options are import open, reference
	:param str namespace:
	:param bool new_file: Start new file
	:param bool force: Forse without showing unsaved changes promopt
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	file_name = "{}_guides_{}".format(asset, description)
	directory = pathlib.normpath(os.path.join(env.assets.get_rigbuild_path(asset), "guides"))

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_load_version_path(version)
	return utilslib.scene.load(file_path, action=action, rnn=rnn, namespace=namespace, new_file=new_file, force=force)


def load_data(asset=None,
              description="primary",
              version=None,
              build=True,
              set_shapes=True,
              set_colors=True,
              namespace=None):
	"""
	Load guide from json file. This is used for templates

	:param str/ None asset:
	:param str description:
	:param int version:
	:param bool build: Build the guide part if it doesnt exist.
	:param bool set_shapes:
	:param bool set_colors:
	:param str namespace:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	file_name = "{}_guides_{}".format(asset, description)
	directory = pathlib.normpath(os.path.join(env.asset.get_rigbuild_path(), "guides"))

	if not os.path.isdir(directory):
		log.debug("Guide dataexporter file not found: " + directory)
		return

	version_object = pathlib.Version(directory, file_name, manager.template_extention)
	file_path = version_object.get_load_version_path(version)

	if not os.path.isfile(file_path):
		log.debug("Guide dataexporter file not found: " + file_path)
		return

	template_data = iolib.json.read(file_path)

	for item in template_data.get("template", {}):
		part_type = item.get("part_type")
		part_data = item.get("part_data")
		options = {o: v.get("value") for o, v in item.get("options").items()}

		if build:
			partslib.build_guide(part_type, **options)
			namespace = None

		if namespace:
			part_data["shapes"] = {"{}:{}".format(namespace, k): v for k, v in part_data.get("shapes").items()}
			part_data["transforms"] = {"{}:{}".format(namespace, k): v
			                           for k, v in part_data.get("transforms").items()}
			part_data["nodes"] = [
				"{}:{}".format(namespace, t) if isinstance(t, string_types) else ["{}:{}".format(namespace, x) for x in
				                                                                  t]
				for t in part_data.get("nodes")]

		utils.set_guide_data(part_data, set_shapes=set_shapes, set_colors=set_colors)


def load_from_build_options(action="import",
                            set_shapes=True,
                            set_colors=True,
                            stash=False,
                            namespace=None,
                            force=False,
                            new_file=True):
	"""
	Load guides from build options.

	:param str action: Options are import open, reference
	:param bool set_shapes:
	:param bool set_colors:
	:param bool stash: Put into temp namespce
	:param str namespace:
	:param bool force: :param bool force: Forse without showing unsaved changes prompt
	:param bool new_file:
	:return:
	"""
	guides_data = env.asset.get_guides()
	namespace = utilslib.scene.STASH_NAMESPACE if stash else namespace

	if not guides_data:
		log.warning("No guide dataexporter found.")
		return

	for data in guides_data:
		load_scene(namespace=namespace,
		           action=action,
		           asset=data.get("asset"),
		           description=data.get("description"),
		           version=data.get("version"),
		           new_file=new_file,
		           force=force)

		if data.get("inherited"):
			load_data(description="inherited", set_shapes=set_shapes, set_colors=set_colors, namespace=namespace,
			          build=False)


def save_from_build_options(description="primary"):
	"""
	Save a guides file according to variables set in asset info file.
	If the guideis meant ot be inherited, then only the offset dataexporter will be saved.

	:param str description:
	:return:
	"""
	guides_data = env.asset.get_guides()

	if guides_data[0].get("inherited"):
		save_data(description="inherited")

	else:
		save_scene(description=description)
