import logging

import maya.cmds as cmds
from smrig.lib import iolib
from smrig.lib import spaceslib
from smrig.lib import utilslib

deformer_type = "spaces"
file_extension = "spc"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(nodes=None, **kwargs):
	"""
	Get deformation order from nodes

	:param nodes:
	:param kwargs:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes) if nodes else cmds.ls("*." + spaceslib.SPACE_TAG)
	return {n.split(".")[0]: eval(cmds.getAttr("{}.{}".format(n, spaceslib.SPACE_TAG))) for n in nodes}


def set_data(data, **kwargs):
	"""
	Set deformation order

	:param data:
	:param kwargs:
	:return:
	"""
	for node, data in data.items():
		space_obj = spaceslib.Space(node)
		space_obj.set_data(data)


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	nodes = []
	for node, values in data.items():
		nodes.append(node)

	return nodes


def remap_nodes(data, remap):
	"""

	:param data:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	new_data = {}
	for search, replace in remap:
		for node, values in data.items():
			r_node = node.replace(search, replace) if search in node else node
			new_data[r_node] = values

	return new_data


def save(nodes, file_path, *args, **kwargs):
	"""

	:param nodes:
	:param file_path:
	:return:
	"""
	iolib.json.write(file_path, get_data(nodes))
	log.info("Saved {} to: {}".format(nodes, file_path))


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	remap = kwargs.get("remap")
	data = iolib.json.read(file_path)
	set_data(remap_nodes(data, remap) if remap else data)
