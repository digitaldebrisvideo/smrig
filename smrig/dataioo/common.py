import logging
import os

import maya.cmds as cmds
from smrig import env
from smrig.dataioo import io
from smrig.dataioo import types
from smrig.dataioo import utils

log = logging.getLogger("deformerIO")


@utils.timer
@utils.preserve_selection
def export_deformer(deformer_node=None, deformer_type=None, file_path=None, versioned=False, sub_dir=False,
                    dir_path=None, **kwargs):
	"""
	Export deformer to file on disk
	TODO: add versioning functionality

	:param deformer_node:
	:param deformer_type: optionally force what type of exporter to use - this is needed for some ie. connections
	:param file_path:
	:param versioned:
	:param sub_dir:
	:param dir_path:
	:param kwargs:
	:return:
	"""
	mod, deformer_type = get_module_from_deformer_type(deformer_node, deformer_type)

	file_path = build_export_path(file_path, deformer_node, deformer_type, mod.file_type, sub_dir, versioned,
	                              dir_path=dir_path)
	if not file_path:
		return

	data = mod.get_data(deformer_node, file_path=file_path, **kwargs)

	if mod.file_type in ["json", "pickle"]:
		io.write_file(file_path, data)

	elif mod.file_type in ["mayaBinary"]:
		io.save_maya_file(file_path, data)

	utils.delete_export_data_nodes()
	deformer_node = deformer_node if deformer_node else "all"
	log.info("Exported {} '{}' to: {}".format(deformer_type, deformer_node, file_path))

	return file_path


def export_deformers(deformer_nodes=None, deformer_type=None, dir_path=None, versioned=False, sub_dir=False, **kwargs):
	"""
	Wrapper for exporting multiple deformers into individual files.

	USAGE:
		from armature.rig import deformerIO
		reload_hierarchy(deformerIO)

		file_path = deformerIO.export_deformers("cluster1")

	:param deformer_nodes:
	:param deformer_type: Required only when exporting connections, defomration orders and other attribute based types
	:param dir_path:
	:param versioned:
	:param sub_dir:
	:param kwargs:
	:return:
	"""
	results = []
	deformer_nodes = deformer_nodes if deformer_nodes else [None]

	dir_path = get_dir_path(dir_path)
	if not dir_path:
		return

	for deformer_node in utils.as_list(deformer_nodes):
		file_path = export_deformer(deformer_node, deformer_type, None, versioned, sub_dir, dir_path, **kwargs)
		results.append(file_path)

	return results


def save_to_asset(deformer, node=None, dtype=None, *args, **kwargs):
	"""
	Save deformers to asset data folder

	:param str/list deformer: export these deformer types
	:param str/list node: Export deformers for these nodes
	:param args:
	:param kwargs:
	:return:
	"""

	data_path = env.asset.get_data_path()
	save(deformer, node=node, directory=data_path, sub_directory=True, *args, **kwargs)
	# export_deformer(deformer_node=deformer, deformer_type=dty[e],  versioned=True, sub_dir=False, dir_path=data_path)
	export_deformers(deformer_nodes=deformer, deformer_type=dtype, dir_path=data_path, versioned=False, sub_dir=False)


def import_deformers(file_path=None, method="auto", remap=None, rebuild=True, data=None, **kwargs):
	"""
	Import deformers from files

	:param str file_path: file path
	:param str method: auto, vertex, uv, closest (auto will default vertex first then closest if vert count is off)
	:param dict remap: dict for remaping node names- {"orig_node": "new_node"}
	:param bool rebuild: recreate the deformer (if it exists in scene it deletes it and recreates it)
	:param dict data: optional for when remaping or checking missing nodes
	:param kwargs:
	:return:

	USAGE:
		from armature.rig import deformerIO
		reload_hierarchy(deformerIO)

		file_path = '/Users/ss/Desktop/cluster1.pickle'
		deformerIO.import_deformer(file_path)

	"""
	if not data:
		file_path = file_path if file_path else io.browser(action="import")
		if file_path:
			import_deformer(file_path, method, remap, rebuild, data, **kwargs)


@utils.timer
def import_deformer(file_path=None, method="auto", remap=None, rebuild=True, data=None, **kwargs):
	"""

	:return:
	"""
	utils.delete_export_data_nodes()
	data = data if data else io.read_file(file_path)
	if file_path.endswith(".pose"):
		data = {"deformer_type": "poseInterpolator", "name": "all", "nodes": []}

	data = remap_data(data, remap) if remap else data
	mod, deformer_type = get_module_from_deformer_type(deformer_type=data.get("deformer_type"))

	if not mod:
		log.warning("No exporter found for type: {}".format(deformer_type))
		return

	if not check_required_nodes(file_path, data):
		return

	# delete the deformer if it exists
	if data.get("name") and rebuild and cmds.objExists(data.get("name")):
		cmds.delete(data.get("name"))

	result = mod.set_data(data, file_path=file_path, method=method, **kwargs)
	log.info("Loaded {}: '{}' from: {}".format(deformer_type, data.get("name"), file_path))
	utils.delete_export_data_nodes()

	return result


def load_type(deformer_types, *args, **kwargs):
	"""
	Load deformer from asset build data folder

	:param str/List deformer_types:
	:param args:
	:param kwargs:
	:return:
	"""
	deformer_types = utilslib.conversion.as_list(deformer_types)

	for node_type in deformer_types:
		module = types.modules.get(node_type)

		if not module:
			log.warning("{} is not a valid data type".format(node_type))
			continue

		extension = types.modules.get(node_type).file_extension
		data_path = pathlib.join(env.asset.get_data_path(), node_type)

		files = pathlib.get_files(data_path, search="*.{}".format(extension))
		if files:
			load(files, *args, **kwargs)


# Helper functions --------------------------------------------------------------------


def remap_data(data, remap):
	"""
	Remap nodes in data for import

	:param dict data: import data
	:param remap: list of sets: [('search', 'replace'), ('search', 'replace')]
	:return dict : data
	"""
	new_data = dict(data)
	geometry = new_data.get("geometry")
	transforms = new_data.get("transforms")
	joints = new_data.get("joints")
	nodes = new_data.get("nodes")
	drivers = new_data.get("drivers")
	driven = new_data.get("driven")
	wuo = new_data.get("wuo")
	connections = new_data.get("connections")
	assignments = new_data.get("assignments")
	curves = new_data.get("curves")

	if geometry:
		new_data["geometry"] = utils.remap_dict(geometry, remap)
	if transforms:
		new_data["transforms"] = utils.remap_dict(transforms, remap)
	if curves:
		new_data["curves"] = utils.remap_dict(curves, remap, key="sdk_driver")
	if joints:
		new_data["joints"] = utils.remap_list(joints, remap)
	if nodes:
		new_data["nodes"] = utils.remap_list(nodes, remap)
	if drivers:
		new_data["drivers"] = utils.remap_list(drivers, remap)
	if driven:
		new_data["driven"] = utils.remap_list(driven, remap)
	if wuo:
		new_data["wuo"] = utils.remap_list(wuo, remap)
	if connections:
		new_data["connections"] = utils.remap_nested_list(connections, remap)
	if assignments:
		new_data["assignments"] = utils.remap_nested_list(assignments, remap)

	return new_data


def check_required_nodes(file_path, data):
	required = utils.get_required_nodes(data)
	missing = utils.get_missing_nodes(required)

	if missing:
		msg = "Missing required nodes for deformer: {} {}\n   ".format(data.get("name"), file_path)
		msg += "\n   ".join(missing)
		log.warning(msg)
		return

	return True


def get_module_from_deformer_type(deformer=None, deformer_type=None):
	"""
	Get export/import module based on node type.

	:param str deformer:
	:param str deformer_type:
	:return: py module
	"""
	deformer_type = deformer_type if deformer_type else cmds.nodeType(deformer)

	# Cases for non node type based exporters (ie constraints, matrix constraints, connections, etc)
	deformer_type = "mayaConstraint" if deformer_type and deformer_type in types.mayaconstraint.constraint_types.keys() else deformer_type
	deformer_type = "matrixConstraint" if deformer and cmds.objExists(deformer + ".armMtxConstraint") else deformer_type

	return types.modules.get(deformer_type), deformer_type


def get_dir_path(file_path=None):
	"""

	:param file_path:
	:return:
	"""
	if not file_path:
		file_path = io.browser(action="export multiple")
		if file_path:
			return file_path[0]


def build_export_path(file_path, deformer, deformer_type, file_extension, sub_dir, versioned, dir_path=None):
	"""
	Build export file path

	:param file_path:
	:param deformer:
	:param deformer_type:
	:param file_extension:
	:param sub_dir:
	:param versioned:
	:param dir_path:
	:return:
	"""
	file_extension = "mb" if file_extension in ["mayaBinary"] else file_extension

	if not dir_path:
		if not file_path:
			file_path = io.browser(action="export multiple", extension=file_extension)
			dir_path = file_path[0]

		elif os.path.splitext(file_path)[-1]:
			dir_path = os.path.dirname(file_path)

		else:
			dir_path = file_path

		if not file_path:
			return

	file_name = deformer if deformer else deformer_type
	base_name = "{}.{}".format(file_name, file_extension)
	dir_path = os.path.join(dir_path, deformer_type) if sub_dir else dir_path
	io.make_dirs(dir_path)

	return os.path.join(dir_path, base_name)
