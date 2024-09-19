import logging
import os
import sys

import maya.cmds as cmds
import smrig
from smrig import dataio, env
from smrig.lib import nodepathlib, pathlib, selectionlib, utilslib
from smrig.lib.attributeslib import tag

base_path = os.path.normpath(os.path.dirname(__file__)).replace('\\', '/')

p = smrig.base_path.split("/smrig")[0]

pose_tool_path = pathlib.normpath(os.path.join(p, "studiolibrary", "src"))
if pose_tool_path not in sys.path:
	sys.path.insert(0, pose_tool_path)
from studiolibrarymaya import poseitem
from studiolibrarymaya import setsitem

log = logging.getLogger("smrig.build.library")

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"


def list_library_elements():
	asset = env.asset.get_asset()
	# print asset
	if not asset:
		return ['asset not set']

	directory = pathlib.normpath(os.path.join(os.path.dirname(env.assets.get_rigbuild_path(asset)), "model"))
	# print directory
	files = pathlib.get_files(directory, search="*.mb")
	if not files:
		print('no models found....clearing')
		return
	models = []
	for file in files:
		lib_file_x = file.split('/')[-1]
		lib_file = lib_file_x.replace('.mb', '')
		if lib_file.endswith('.mb'):
			lib_file = lib_file.replace('.mb', '')
		print(lib_file)
		models.append(lib_file)

	return models


def replace_rig_reference(current_reference_node=None, new_path=None):
	"""

	:param current:
	:param new:
	:return:
	"""
	get_current_references(type="Rig")
	if not rig_refs:
		logging.info('no references of any rig found')
		return

	cmds.file(new_path, loadReference=current_reference_node, lrd='all')


def save_library_scene(asset=None, type=None, category=None, description=None, version=None, meshes=None):
	"""
	Save library item maya file.

	:param asset:
	:param description:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not type or not category or not description:
		log.error("library type cateogory or description not set")
		return

	if type.endswith("_lib"):
		type = type.replace("_lib", "")

	nodes = []

	if not meshes:
		meshes = cmds.ls(type="mesh")
		if not meshes:
			log.error("No meshes in scene")
			return

		for mesh in meshes:
			node = selectionlib.get_transform(mesh)
			if selectionlib.get_parent(node):
				cmds.parent(node, world=True)
			nodes.append(node)

		if not nodes:
			log.error("no meshes or something went wrong in scene")
	else:
		for mesh in meshes:
			if cmds.objExists(mesh):
				log.warning("{} does not exist....skipping".format(mesh))
			shapes = selectionlib.get_shapes(mesh)
			if not shapes:
				log.warning("{} is not a mesh....skipping".format(mesh))
				continue
			else:
				if "mesh" in cmds.nodeType(shapes[0]):
					nodes.append(mesh)
					if selectionlib.get_parent(mesh):
						cmds.parent(mesh, world=True)
				else:
					log.warning("{} not a mesh....skipping".format(mesh))
					continue

	lib_grp = description + "_lib_GRP"
	if not cmds.objExists(lib_grp):
		lib_grp = cmds.createNode("transform", name=lib_grp)
	# print (nodes)
	cmds.parent(nodes, lib_grp)

	tag_value = type.replace("_lib", "") + "_" + category + "_" + description
	tag.add_tag_attribute(lib_grp, attribute_name="libItem", value=tag_value)

	file_name = "{}_{}_{}.{}".format(type, category, description)

	directory = pathlib.normpath(
		os.path.join(os.path.join(env.asset.get_rigbuild_path().replace("rigbuild", "libraries")), type, category))
	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	cmds.file(file_path, options="v=0;", type=maya_file_type, ea=True)
	log.info("Saved library model element: {}".format(pathlib.normpath(file_path)))

	log.info("Exported library item to: {}".format(pathlib.normpath(file_path)))


def reference_library_element(asset=None,
                              type=None,
                              category=None,
                              element=None,
                              action="reference",
                              namespace=None,
                              rnn=True,
                              version=True):
	"""

	:param asset:
	:param type:
	:param category:
	:param element:
	:param item:
	:param action:
	:param namespace:
	:param rnn:
	:return:
	"""

	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not type or not category or not element:
		log.error("no library, category or element  set")
		return
	name = type + "_" + element + "_" + version + ".mb"
	directory_file = pathlib.normpath(os.path.join(env.asset.get_rigbuild_path()), "dataio", "libraries", type,
	                                  category)
	if os.path.isfile(directory_file):
		if action == "reference":
			if not namespace:
				namespace = ":"
			results = utilslib.scene.load(directory_file, action="reference", rnn=True, namespace=namespace,
			                              new_file=False)
			if rnn is True:
				return results
			else:
				log.info("referenced {} into scene").formate(directory_file)


def load_element(asset=None,
                 type=None,
                 category=None,
                 element=None,
                 item=None,
                 action=None,
                 namespace=None,
                 rnn=True,
                 apply_data=False):
	"""
	Load library maya file.

	:param asset:
	:param type:
	:param category:
	:param action:
	:param namespace:
	:param new_file:
	:param new names:
	:param apply_deformers:

	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not type or not category or not element:
		log.error("no library, category or element  set")

	type = type + "_lib"

	if ".mb" in element:
		file = pathlib.normpath(
			os.path.join(env.assets.get_rigbuild_path(asset).replace("rigbuild", "libraries"), type, category, element))
		if os.path.isfile(file):
			new_nodes = cmds.file(file_path, i=1, type='OBJ', rnn=True, namespace=namespace)
			custom_path = pathlib.normpath(
				os.path.join(env.assets.get_rigbuild_path(asset).replace("rigbuild", "libraries"), "dataio"))
			if os.path.isdir(custom_path):
				dataio.load(custom_path=custom_path)


def get_current_references():
	"""

	return:   namespaces
	"""

	namespaces = []
	reference_nodes = cmds.ls(type="reference")
	if "sharedReferenceNode" in reference_nodes:
		rns.remove("sharedReferenceNode")
	for reference_node in reference_nodes:
		top_node = cmds.referenceQuery(reference_node, rfn=True, topReference=True)
		if "rig_GRP" in top_node:
			namespace = cmds.referenceQuery(reference_node, rfn=True, namespace=True)
			if namespace:
				namespaces.append(namespace)

	return namespaces


def save_pose_element(asset, type, category, name):
	"""
	return: pose name

	"""
	if not "pose" in type:
		log.error("not from pose library")
	objects = cmds.ls(selection=True) or []
	if not objects:
		cmds.confirmDialog(message="Nothing Selected")
	directory = pathlib.normpath(
		os.path.join(env.asset.get_rigbuild_path().replace("rigbuild", "libraries"), "pose_lib", category))
	pose_file = pathlib.normpath(os.path.join(directory, name + '.pose'))
	if not os.path.isdir(pose_file):
		pathlib.make_dirs(pose_file)
	poseitem.save(pose_file, objects=objects)
	return pose_file


def save_set_element(asset, type, category, name):
	"""
	return: pose name

	"""
	if "set" in type:
		log.error("not set to sets library")
	objects = cmds.ls(selection=True) or []
	if not objects:
		cmds.confirmDialog(m="Nothing Selected")
	namespaces = nodepathlib.get_namespace(objects[0])
	directory = pathlib.normpath(
		os.path.join(env.asset.get_rigbuild_path().replace("rigbuild", "libraries"), "sets_lib", category, name))
	# sets_file = pathlib.normpath(os.path.join(directory, name+'.set'))
	objects = cmds.ls(selection=True) or []
	item = setsitem.SetsItem(sets_file)
	item.save(objects)
	return directory


def load_pose_element(asset, type, category, name):
	"""
	return: pose name

	"""
	if not "pose" in type:
		log.error("not from pose library")
	namespaces = get_current_references()
	if namespaces and len(namespaces) > 1:
		cmds.confirmDialog(message="More than one reference of rig in scene\nWill to first namespace found")
	directory_x = pathlib.normpath(
		os.path.join(env.asset.get_rigbuild_path().replace("rigbuild", "libraries"), "pose_lib", category, name))
	directory = pathlib.normpath(os.path.join(directory_x, name + '.pose'))
	namespace = ""
	if namespaces:
		namespace = namespaces[0]
	if os.path.isdir(directory):
		poseitem.load(directory, namespaces=namespace)
	return directory


def load_set_element(asset, type, category, name):
	"""
	return: pose name

	"""
	if not "sets" in type:
		log.error("not set to sets library")

	namespaces = get_current_references() or []
	namespace = ""
	if namespaces and len(namespaces) > 1:
		cmds.confirmDialog(message="Warning:\nScene contains more than one reference of rig\nWill apply to first found")
		namespace = namespaces[0]
	if namespaces:
		namespace = namespaces[0]
	directory = pathlib.normpath(
		os.path.join(env.asset.get_rigbuild_path().replace("rigbuild", "libraries"), "sets_lib", category, name))
	if os.path.isdir(directory):
		item = setsitem.SetsItem(directory)
		item.load(namespaces=namespace)
	return directory


def save_from_build_options(description="primary"):
	"""
	Save a model file according to variables set in asset info file.

	:return:
	"""
	models_data = env.asset.libraries()

	if models_data[0].get("inherited"):
		save_data(description="inherited")

	else:
		save_scene(description=description)
