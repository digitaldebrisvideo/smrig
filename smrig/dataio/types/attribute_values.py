import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import iolib
from smrig.lib import nodepathlib
from smrig.lib import utilslib

deformer_type = "attributeValues"
file_extension = "attv"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(nodes, precision=None):
	"""

	:param nodes:
	:param int precision: round value decimal places
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	data = {}

	for node in nodes:
		locked_atrs = cmds.listAttr(node, l=True) or []
		attrs = cmds.listAttr(node, k=True) or [] + cmds.listAttr(node, cb=True) or []
		attrs = [a for a in attrs if a not in locked_atrs]

		for attr in attrs:
			value = cmds.getAttr("{}.{}".format(node, attr))
			value = round(value, precision) if isinstance(precision, int) else value

			if not cmds.listConnections("{}.{}".format(node, attr), d=False, s=True):
				if isinstance(value, int) or isinstance(value, float):
					data["{}.{}".format(nodepathlib.remove_namespace(node), attr)] = {
						"value": value
					}

	return data


def set_data(data):
	"""
	:param data:
	:param create_attrs:
	:return:
	"""
	if not data:
		return

	for node, node_data in data.items():
		if not node_data:
			continue

		if not cmds.objExists(node):
			continue

		try:
			cmds.setAttr(node, node_data.get("value"))
		except Exception as e:
			log.error(e)


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
		for shape, value in data.items():
			r_shape = shape.replace(search, replace) if search in shape else shape
			new_data[r_shape] = value

	return new_data


def save(dummy, file_path=None, nodes=None, precision=None, *args, **kwargs):
	"""

	:param nodes:
	:param int precision: round value decimal places
	:param file_path:
	:return:
	"""
	nodes = nodes if nodes else utils.get_controls()
	iolib.json.write(file_path, get_data(nodes, precision=precision))
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
	data = remap_nodes(data, remap) if remap else data

	nodes = data.keys()
	if utils.check_missing_nodes(file_path, nodes):
		pass

	set_data(data)
