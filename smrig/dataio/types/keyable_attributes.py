import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import attributeslib
from smrig.lib import iolib
from smrig.lib import nodepathlib
from smrig.lib import utilslib

deformer_type = "keyableAttributes"
file_extension = "katt"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(nodes):
	"""

	:param nodes:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	data = {}

	for node in nodes:
		data[nodepathlib.remove_namespace(node)] = {
			"keyable": cmds.listAttr(node, k=True) or [],
			"nonkeyable": cmds.listAttr(node, cb=True) or [],
			"locked": cmds.listAttr(node, l=True) or []
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

		keyable = node_data.get("keyable") or []
		nonkeyable = node_data.get("nonkeyable") or []
		locked = node_data.get("locked") or []

		try:
			attributeslib.set_attributes(node,
			                             ["t", "r", "s", "v", "ro", "jo", "shear", "radius"],
			                             lock=True,
			                             keyable=False,
			                             user_defined=True)

			attributeslib.set_attributes(node, keyable, keyable=True, lock=False)
			attributeslib.set_attributes(node, locked, lock=True, channel_box=False)
			attributeslib.set_attributes(node, nonkeyable, lock=False, keyable=False, channel_box=True)

		except:
			pass


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	return [n for n in data.keys()]


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


def save(dummy, file_path=None, nodes=None, *args, **kwargs):
	"""

	:param nodes:
	:param file_path:
	:return:
	"""
	nodes = nodes if nodes else utils.get_controls()
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
	data = remap_nodes(data, remap) if remap else data

	nodes = data.keys()
	if utils.check_missing_nodes(file_path, nodes):
		pass

	set_data(data)
