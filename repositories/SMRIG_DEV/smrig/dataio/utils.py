import logging
import os

import maya.cmds as cmds
from smrig import env
from smrig.env import prefs
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import utilslib

default_extension = "json"
default_filter = "Weights Data (*.json)"
log = logging.getLogger("smrig.dataexporter")

remap_file = os.path.join(env.asset.get_data_path(), "remap.json")


def get_deformers(node_shape, deformer_types, as_string=False):
	"""
	Get deformers from node

	:param str node_shape:
	:param str/list deformer_types:
	:param bool as_string: Used for enum, returns enum option names instead of index
	:return: Deformers
	:rtype: list
	"""
	deformers = []
	deformer_types = utilslib.conversion.as_list(deformer_types)

	for node in cmds.listHistory(node_shape) or []:
		inherited = cmds.nodeType(node, inherited=True)
		for inherit in deformer_types:
			if inherit in inherited:
				deformers.append(node)
				break

	for inherit in deformer_types:
		if inherit == "constraint":
			deformers.extend(constraintslib.get_constraints_from_target(node_shape))

		if inherit == "matrixConstraint":
			deformers.extend(constraintslib.get_matrix_constraints_from_target(node_shape))

		if inherit == "millSimpleConstraint":
			deformers.extend(constraintslib.get_mill_simple_constraints_from_target(node_shape))

		if inherit == "millVertexConstraint":
			deformers.extend(constraintslib.get_mill_simple_constraints_from_target(node_shape))

		if inherit == "connections":
			cnn = get_connections(node_shape, as_string=as_string)

			if cnn:
				cnn_str = "\n    ".join(cnn)
				deformers.append("{}:\n    {}".format(node_shape, cnn_str))

		if inherit == "userDefinedAttributes":
			attrs = cmds.listAttr(node_shape, ud=1) or []

			if attrs:
				attr_str = "\n    ".join(attrs)
				deformers.append("{}:\n    {}".format(node_shape, attr_str))

		if inherit == "setDrivenKeyframe":
			sdk = get_sdk(node_shape)

			if sdk:
				sdk_str = "\n    ".join(sdk)
				deformers.append("{}:\n    {}".format(node_shape, sdk_str))

	return deformers


def get_sdk(node):
	"""
	Get setdriven keyframes from node

	:param str node:
	:return:
	"""
	crvs = cmds.listConnections(node, s=1, d=0, type="animCurve", scn=1) or []
	sdks = [c for c in crvs if cmds.listConnections(c + ".input", s=1, d=0, p=1, scn=1)]

	return sdks


def get_connections(node, as_string=False):
	"""
	get connection info

	:param str nodes:
	:return:
	"""
	connections = []
	excluded_types = ["animCurve", "blendWeighted", "Constraint"]

	attrs = [a for a in cmds.listAttr(node, k=1) or [] if "." not in a] + ["t", "r", "s", "scale[0]"]
	if cmds.nodeType(node) == "blendShape":
		attrs.extend(["weight[{0}]".format(i) for i in range(cmds.blendShape(node, q=1, wc=1))])

	for attr in attrs:
		if cmds.objExists(node + "." + attr):
			source_connecitons = cmds.listConnections(node + "." + attr, s=1, d=0, p=1, scn=1) or []

			if source_connecitons:
				for src_conneciton in source_connecitons:

					passed_check = True
					for exluded in excluded_types:
						if exluded in cmds.nodeType(src_conneciton):
							passed_check = False

					if cmds.objExists(src_conneciton.split(".")[0] + ".smrigMatrixConstraint"):
						passed_check = False

					if passed_check:
						if as_string:
							connections.append("{}, {}".format(src_conneciton, "{}.{}".format(node, attr)))
						else:
							connections.append([src_conneciton, "{}.{}".format(node, attr)])

	return connections


def get_extension(node_type):
	"""
	Get file extension from deformer type.

	:param str node_type: deformer type
	:return: str
	"""

	return prefs.get_suffix(node_type).lower() or default_extension.lower()


def browser(action="import", extension=None, dir=None):
	"""

	:param action: Options are import, export
	:param str/None extension: file filter by file extension
	:param str dir: starting directory
	:return:
	"""
	if action == "import":
		file_mode = 1
		button = "Import"

	elif action == "import multiple":
		file_mode = 4
		button = "Import Multiple"

	elif action == "export multiple":
		file_mode = 3
		button = "Export"

	else:
		file_mode = 0
		button = "Export"

	file_filter = "Weights Data (*.{})".format(extension) if extension else default_filter
	if dir:
		file_path = cmds.fileDialog2(fileFilter=file_filter, dir=dir, dialogStyle=2, okc=button, fm=file_mode)
	else:
		file_path = cmds.fileDialog2(fileFilter=file_filter, dialogStyle=2, okc=button, fm=file_mode)

	if file_path and file_mode in [0, 1]:
		return file_path[0]

	else:
		return file_path


def check_missing_nodes(name, nodes):
	"""
	Check for requireed nodes before importing deformer

	:param str name: deformer name (This is used only for logging purposes)
	:param list nodes:
	:return:
	"""
	missing_nodes = [n for n in list(nodes) if not cmds.objExists(n)]
	if missing_nodes:
		log.warning("{} is missing nodes. Needs remapping...\n\t{}".format(name, "\n\t".join(list(missing_nodes))))

	return missing_nodes


def get_controls():
	"""

	:return:
	"""
	ctrls = [controlslib.Control(c.split(".")[0]) for c in cmds.ls("*.{}".format(controlslib.common.TAG))]

	nodes = []
	for ctrl in ctrls:
		nodes.extend(ctrl.all_controls)

	nodes.extend(cmds.ls("*_CTRL"))
	print(nodes)

	return list(set(nodes))
