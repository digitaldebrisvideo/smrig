import logging
import os

import maya.cmds as cmds
import maya.mel as mel
from smrig import env
from smrig.lib import attributeslib, nodepathlib, pathlib, selectionlib, utilslib
from smrig.lib.constantlib import ENGINE_SET, LIBRARY_GROUP, RIG_GROUP, RIG_SET

log = logging.getLogger("smrig.build.model")

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"


def save_scene(asset=None, description="primary", version=None):
	"""
	Save model maya file.

	:param asset:
	:param description:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	file_name = "{}_model_{}".format(asset, description)
	directory = pathlib.normpath(os.path.join(os.path.dirname(env.asset.get_rigbuild_path()), "model"))
	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	cmds.file(file_path, options="v=0;", type=maya_file_type, ea=True)
	log.info("Saved model scene: {}".format(pathlib.normpath(file_path)))


def load_scene(asset=None,
               description="primary",
               version=None,
               unlock_normals=False,
               soft_normals=False,
               action="import",
               namespace=None,
               new_file=False,
               file_path=""):
	"""
	Load model file.

	:param asset:
	:param description:
	:param version:
	:param unlock_normals:
	:param soft_normals:
	:param action:
	:param namespace:
	:param new_file:
	:param file_path:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not file_path:
		file_name = "{}_model_{}".format(asset, description)
		directory = pathlib.normpath(os.path.join(os.path.dirname(env.assets.get_rigbuild_path(asset)), "model"))
		version_object = pathlib.Version(directory, file_name, maya_file_extention)
		file_path = version_object.get_load_version_path(version)

	result = utilslib.scene.load(file_path, action=action, rnn=True, namespace=namespace, new_file=new_file)

	if result:
		result = cmds.ls([selectionlib.get_transform(m) for m in selectionlib.sort_by_hierarchy(result)])

		if unlock_normals or soft_normals:
			meshes = [n for n in result if cmds.nodeType(n) == "mesh"]

			if unlock_normals:
				cmds.select(meshes)
				mel.eval("UnlockNormals;")

			if soft_normals:
				cmds.select(meshes)
				mel.eval("SoftPolyEdgeElements 1;")

		return result


def load_from_build_options(action="import", namespace=None):
	"""
	Load model from build options.

	:param action:
	:param set_shapes:
	:param set_colors:
	:param stash:
	:param namespace:
	:return:
	"""
	model_data = env.asset.get_models()
	if not model_data:
		log.warning("No model dataio found.")
		return

	for data in model_data:
		result = load_scene(namespace=namespace,
		                    action=action,
		                    asset=data.get("asset"),
		                    description=data.get("description"),
		                    version=data.get("version"),
		                    file_path=data.get("file_path"))

		if result and cmds.objExists(RIG_GROUP) and cmds.objExists(LIBRARY_GROUP) and cmds.objExists(RIG_SET):
			if cmds.objExists("|{}|{}".format(RIG_GROUP, LIBRARY_GROUP)):
				cmds.parent(result, "|{}|{}".format(RIG_GROUP, LIBRARY_GROUP))

			if not cmds.objExists(LIBRARY_CACHE_SET):
				cmds.sets(cmds.sets(n=LIBRARY_CACHE_SET, em=True), add=RIG_SET)

			if not cmds.objExists(ENGINE_SET):
				cmds.sets(cmds.sets(n=ENGINE_SET, em=True), add=RIG_SET)

			cmds.sets(result, add=LIBRARY_CACHE_SET)
			cmds.sets(result, add=ENGINE_SET)

		return result


def clean(freeze_transforms=True,
          zero_pivots=True,
          unlock_normals=True,
          soften_normals=True,
          rename_shape_nodes=True,
          delete_intermediate_objects=True,
          delete_layers=True,
          delete_namespaces=True,
          delete_history=True,
          check_clashing_node_names=True,
          remove_unknown_plugins=True,
          unlock_transforms=True):
	"""

	:param freeze_transforms:
	:param zero_pivots:
	:param unlock_normals:
	:param soften_normals:
	:param rename_shape_nodes:
	:param delete_intermediate_objects:
	:param delete_layers:
	:param delete_namespaces:
	:param delete_history:
	:param check_clashing_node_names:
	:param remove_unknown_plugins:
	:param unlock_transforms:
	:return:
	"""
	if delete_intermediate_objects:
		intermediates = [g for g in cmds.ls(type=["mesh", "nurbsSurface", "nurbsCurve"])
		                 if cmds.getAttr(g + ".intermediateObject")]

		if intermediates:
			cmds.delete(intermediates)

	meshes = cmds.ls(type="mesh")
	shapes = cmds.ls(type=["mesh", "nurbsSurface", "nurbsCurve"])
	transforms = [n for n in cmds.ls(type="transform") if n not in ["front", "persp", "side", "top"]]

	if unlock_transforms:
		attributeslib.set_attributes(transforms, ["t", "r", "s", "v"], lock=False, keyable=True)

	if freeze_transforms:
		cmds.makeIdentity(transforms, apply=1, t=1, r=1, s=1, n=0, pn=1)

	if zero_pivots:
		cmds.xform(transforms, piv=[0, 0, 0])

	if unlock_normals:
		cmds.select(meshes)
		mel.eval("UnlockNormals;")

	if soften_normals:
		cmds.select(meshes)
		mel.eval("SoftPolyEdgeElements 1;")

	if delete_layers:
		layers = [l for l in cmds.ls(type="displayLayer") if l not in ["defaultLayer"]]
		if layers:
			cmds.delete(layers)

	if delete_namespaces:
		namespaces = [n for n in cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) if n not in ["UI", "shared"]]
		for namespace in namespaces:
			cmds.namespace(mergeNamespaceWithRoot=True, removeNamespace=namespace)

	if rename_shape_nodes:
		for shape in shapes:
			name = "{}Shape".format(selectionlib.get_transform(shape)).split("|")[-1]
			if shape != name:
				cmds.rename(shape, name)

	if check_clashing_node_names:
		nodepathlib.print_clashing_nodes_names()

	if remove_unknown_plugins:
		utilslib.scene.remove_unknown_nodes_and_plugins()

	if delete_history:
		cmds.DeleteAllHistory()


def save_from_build_options(description="primary"):
	"""
	Save a model file according to variables set in asset info file.
	:return:
	"""
	guides_data = env.asset.get_models()

	if guides_data[0].get("inherited"):
		save_data(description="inherited")

	else:
		save_scene(description=description)
