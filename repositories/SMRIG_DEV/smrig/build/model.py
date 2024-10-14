import logging
import os

import maya.cmds as cmds
import maya.mel as mel
from smrig import env
from smrig.lib import attributeslib
from smrig.lib import nodepathlib
from smrig.lib import pathlib
from smrig.lib import selectionlib
from smrig.lib import utilslib
from smrig.lib.constantlib import RIG_GROUP, MODEL_GROUP, RIG_SET, CACHE_SET
from smrig.userprefs import *

try:
	import visional_pipeline_api1.element as velement
	import visional_pipeline_api1.asset as vasset
except:
	pass

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


def convert_lookdev_to_model():
	"""

	:return:
	"""

	lookdev_data = env.asset.get_models()[0]
	lookdev_filepath = lookdev_data["file_path"]
	lookdev_filename = lookdev_filepath.split("/")[-1]
	if "ModelOnly" in lookdev_filename:
		back_to_lookdev = lookdev_filename.replace("ModelOnly", "LookDev")
		env.asset.set_models(file_path=back_to_lookdev)
		lookdev_data = env.asset.get_models()[0]
		lookdev_filepath = lookdev_data["file_path"]
		lookdev_filename = lookdev_filepath.split("/")[-1]
	model_dir = lookdev_filepath.replace(lookdev_filename, "")
	model_filepath = pathlib.normpath(os.path.join(model_dir, "Rig"))
	model_filename = lookdev_filename.replace("LookDev", "ModelOnly")
	model_filepath = pathlib.normpath(os.path.join(model_filepath, model_filename))

	cmds.file(lookdev_filepath, i=True, loadReferenceDepth="none", type="mayaBinary")

	groups = ["high_model_GRP", "Xgen_GRP", "custom_blends_high_GRP", "Makeup_CTL"]
	export = []
	for group in groups:
		if cmds.objExists(group):
			export.append(group)
		else:
			print(group + "  does not exist in scene.....skipping for export")

	cmds.select(export)
	vray_set = cmds.ls("vrayDisplacement_*")

	cmds.select(export)
	for vray_node in vray_set:
		cmds.select(vray_node, add=True, ne=True)

	cmds.file(model_filepath, force=True, es=True, type="mayaBinary")
	env.asset.set_models(file_path=model_filepath)


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

		if result and cmds.objExists(RIG_GROUP) and cmds.objExists(MODEL_GROUP) and cmds.objExists(RIG_SET):
			if cmds.objExists("|{}|{}".format(RIG_GROUP, MODEL_GROUP)):
				model_parents = list(set([selectionlib.get_top_parent(n) for n in result]))
				cmds.parent(model_parents, "|{}|{}".format(RIG_GROUP, MODEL_GROUP))

			if not cmds.objExists(CACHE_SET):
				cmds.sets(cmds.sets(n=CACHE_SET, em=True), add=RIG_SET)

			if not cmds.objExists(RENDER_SET):
				cmds.sets(cmds.sets(n=RENDER_SET, em=True), add=RIG_SET)

			cmds.sets(result, add=CACHE_SET)
			cmds.sets(result, add=RENDER_SET)

		return result


def save_from_build_options(description="primary"):
	"""
	Save a model file according to variables set in asset info file.
	:return:
	"""
	models_data = env.asset.get_models()

	save_scene(description=description)


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

#
# def save_scene(asset=None, description="primary", version=None):
#     """
#     Save model maya file.
#
#     :param asset:
#     :param description:
#     :return:
#     """
#     asset = asset if asset else env.asset.get_asset()
#
#     if not asset:
#         log.error("Asset not set")
#         return
#
#     file_name = "{}_model_{}".format(asset, description)
#     directory = pathlib.normpath(os.path.join(os.path.dirname(env.asset.get_rigbuild_path()), "model"))
#     pathlib.make_dirs(directory)
#
#     version_object = pathlib.Version(directory, file_name, maya_file_extention)
#     file_path = version_object.get_save_version_path(version, new_version=False if version else True)
#
#     cmds.file(file_path, options="v=0;", type=maya_file_type, ea=True)
#     log.info("Saved model scene: {}".format(pathlib.normpath(file_path)))
#
#
# def load_scene(asset=None,
#                description="primary",
#                version=None,
#                unlock_normals=False,
#                soft_normals=False,
#                action="import",
#                namespace=None,
#                new_file=False,
#                file_path=""):
#     """
#     Load model file.
#
#     :param asset:
#     :param description:
#     :param version:
#     :param unlock_normals:
#     :param soft_normals:
#     :param action:
#     :param namespace:
#     :param new_file:
#     :param file_path:
#     :return:
#     """
#     asset = asset if asset else env.asset.get_asset()
#
#     if not asset:
#         log.error("Asset not set")
#         return
#
#     if USE_FACILITY_PIPELINE:
#         version = version if version else "latest"
#         file_path = get_pipeline_file_path(asset, description, version)
#
#     if not file_path:
#         file_name = "{}_model_{}".format(asset, description)
#         directory = pathlib.normpath(os.path.join(os.path.dirname(env.assets.get_rigbuild_path(asset)), "model"))
#         version_object = pathlib.Version(directory, file_name, maya_file_extention)
#         file_path = version_object.get_load_version_path(version)
#
#     result = utilslib.scene.load(file_path, action=action, rnn=True, namespace=namespace, new_file=new_file)
#     result = cmds.ls(result)
#
#     if result:
#         result = selectionlib.sort_by_hierarchy(result)
#         result = cmds.ls([selectionlib.get_transform(m, full_path=True) for m in result])
#
#         if unlock_normals or soft_normals:
#             meshes = [n for n in result if cmds.nodeType(n) == "mesh"]
#
#             if unlock_normals:
#                 cmds.select(meshes)
#                 mel.eval("UnlockNormals;")
#
#             if soft_normals:
#                 cmds.select(meshes)
#                 mel.eval("SoftPolyEdgeElements 1;")
#
#         return result
#
#
# def load_from_build_options(action="import", namespace=None, use_default=True):
#     """
#     Load model from build options.
#
#     :param action:
#     :param namespace:
#     :param use_default:
#     :return:
#     """
#     model_data = env.asset.get_models()
#     if not model_data and use_default:
#         log.warning("No model data found, using primary model.")
#         model_data = [{"description": "primary",
#                        "unlock_normals": False,
#                        "soft_normals": False,
#                        "version": None,
#                        "asset": env.asset.get_asset(),
#                        "file_path": None}]
#
#     elif not model_data:
#         log.warning("No model data found.")
#         return
#
#     for data in model_data:
#         result = load_scene(namespace=namespace,
#                             action=action,
#                             asset=data.get("asset"),
#                             description=data.get("description"),
#                             version=data.get("version"),
#                             file_path=data.get("file_path"))
#
#         if result and cmds.objExists(RIG_GROUP) and cmds.objExists(MODEL_GROUP) and cmds.objExists(RIG_SET):
#             if cmds.objExists("|{}|{}".format(RIG_GROUP, MODEL_GROUP)):
#                 model_parents = list(set([selectionlib.get_top_parent(n, full_path=True) for n in result]))
#                 cmds.parent(model_parents, "|{}|{}".format(RIG_GROUP, MODEL_GROUP))
#
#             if not cmds.objExists(CACHE_SET):
#                 cmds.sets(cmds.sets(n=CACHE_SET, em=True), add=RIG_SET)
#
#             if not cmds.objExists(ENGINE_SET):
#                 cmds.sets(cmds.sets(n=ENGINE_SET, em=True), add=RIG_SET)
#
#             cmds.sets(result, add=CACHE_SET)
#             cmds.sets(result, add=ENGINE_SET)
#
#         return result
#
#
# def clean(freeze_transforms=True,
#           zero_pivots=True,
#           unlock_normals=True,
#           soften_normals=True,
#           rename_shape_nodes=True,
#           delete_intermediate_objects=True,
#           delete_layers=True,
#           delete_namespaces=True,
#           delete_history=True,
#           fix_clashing_node_names=True,
#           remove_unknown_plugins=True,
#           unlock_transforms=True):
#     """
#     Clean up the model before saving or publishing.
#
#     :param bool freeze_transforms:
#     :param bool zero_pivots:
#     :param bool unlock_normals:
#     :param bool soften_normals:
#     :param bool rename_shape_nodes:
#     :param bool delete_intermediate_objects:
#     :param bool delete_layers:
#     :param bool delete_namespaces:
#     :param bool delete_history:
#     :param bool fix_clashing_node_names:
#     :param bool remove_unknown_plugins:
#     :param bool unlock_transforms:
#     :return:
#     """
#     if delete_intermediate_objects:
#         intermediates = [g for g in cmds.ls(type=["mesh", "nurbsSurface", "nurbsCurve"])
#                          if cmds.getAttr(g + ".intermediateObject")]
#
#         if intermediates:
#             cmds.delete(intermediates)
#
#     meshes = cmds.ls(type="mesh")
#     shapes = cmds.ls(type=["mesh", "nurbsSurface", "nurbsCurve"])
#     transforms = [n for n in cmds.ls(type="transform") if n not in ["front", "persp", "side", "top"]]
#
#     if unlock_transforms:
#         attributeslib.set_attributes(transforms, ["t", "r", "s", "v"], lock=False, keyable=True)
#
#     if freeze_transforms:
#         cmds.makeIdentity(transforms, apply=1, t=1, r=1, s=1, n=0, pn=1)
#
#     if zero_pivots:
#         cmds.xform(transforms, piv=[0, 0, 0])
#
#     if unlock_normals:
#         cmds.select(meshes)
#         mel.eval("UnlockNormals;")
#
#     if soften_normals:
#         cmds.select(meshes)
#         mel.eval("SoftPolyEdgeElements 1;")
#
#     if delete_layers:
#         layers = [l for l in cmds.ls(type="displayLayer") if l not in ["defaultLayer"]]
#         if layers:
#             cmds.delete(layers)
#
#     if delete_namespaces:
#         namespaces = [n for n in cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) if n not in ["UI", "shared"]]
#         for namespace in namespaces:
#             cmds.namespace(mergeNamespaceWithRoot=True, removeNamespace=namespace)
#
#     if rename_shape_nodes:
#         for shape in shapes:
#             name = "{}Shape".format(selectionlib.get_transform(shape)).split("|")[-1]
#             if shape != name:
#                 cmds.rename(shape, name)
#
#     if fix_clashing_node_names:
#         fix_clashing_names()
#
#     if remove_unknown_plugins:
#         utilslib.scene.remove_unknown_nodes_and_plugins()
#
#     if delete_history:
#         cmds.DeleteAllHistory()
#
#
# def get_pipeline_file_path(asset, name, version):
#     """
#     For pipeline specific environments
#
#     :param str asset:
#     :param str name:
#     :param str version:
#     :return:
#     """
#     path = PATH_TEMPLATE.split("{job}")[0] + env.get_job()
#     paths = [p for p in vasset.get_assets(path) if asset in p]
#     if not paths:
#         return []
#
#     e_paths = [p for p in velement.get_elements(paths[0]) if name == os.path.basename(p)]
#     if not e_paths:
#         return []
#
#     versions = velement.get_element_versions(e_paths[0])
#     versions.reverse()
#
#     if version == "latest":
#         version_path = versions[0]
#     else:
#         version_path = [p for p in versions if "/{}/".format(version)]
#
#     try:
#         file_path = velement.get_components(version_path, pattern="*.abc")[1][0]
#         return file_path
#     except:
#         log.warning("Cannot find published file for: " + version_path)
#
# def split_geo(geos=None):
#     """
#
#     :param str/list geos:
#     :return:
#     """
#     geos = utilslib.conversion.as_list(geos) if geos else cmds.ls(sl=1)
#     results = []
#     for geo in geos:
#         try:
#             result = cmds.polySeparate(geo, ch=0)
#             for r in result:
#                 results.append(cmds.rename(r, geo + "#"))
#         except:
#             print ("cannot split: " + geo)
#
#     return results
#
# def fix_clashing_names():
#     """
#     Renames all nodes with clashing geo names to long_name_node_name#
#     :return:
#     """
#     nodepathlib.print_clashing_nodes_names()
#     for i, s in enumerate(cmds.ls(sl=1)):
#         s = cmds.ls(sl=1)[i]
#         cmds.rename(s, "{}{}".format(s.split("|")[-1], i))
