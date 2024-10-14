import logging

import maya.cmds as cmds
from smrig.lib import iolib
from smrig.lib import utilslib

deformer_type = "deformationOrder"
file_extension = "order"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(nodes):
	"""
	Get deformation order from nodes

	:param nodes:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)

	data = {}
	for shape in nodes:
		stack = cmds.listHistory(shape, il=1, pdo=1) or []
		data[shape] = stack

	return data


def set_data(data):
	"""
	Set deformation order

	:param data:
	:return:
	"""
	for shape, order in data.items():

		if not cmds.objExists(shape):
			log.warning("Node does not exist: {}. Cannot set deformation order...".format(shape))
			continue

		for i in range(len(order) - 1):
			try:
				cmds.reorderDeformers(order[i], order[i + 1], shape)
				log.info("Reordered deformation order: " + shape)

			except:
				pass


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	return data.keys()


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
		for shape, order in data.items():
			r_shape = shape.replace(search, replace) if search in shape else shape
			new_data[r_shape] = order

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
