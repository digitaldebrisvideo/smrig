import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import iolib
from smrig.lib import utilslib

deformer_type = "connections"
file_extension = "cnn"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))

excluded_types = ["animCurve", "blendWeighted", "Constraint"]


def get_data(nodes=None):
	"""
	get connection info

	:param nodes:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)

	connections = {}
	for node in nodes:
		node_connections = utils.get_connections(node)
		for connection in node_connections:
			connections[connection[1]] = connection[0]

	return connections


def set_data(data):
	"""
	Create connections

	:param data:
	:return:
	"""
	for dst_connection, src_conneciton in data.items():
		if utils.check_missing_nodes("connections", [dst_connection.split(".")[0], src_conneciton.split(".")[0]]):
			continue

		try:
			cmds.connectAttr(src_conneciton, dst_connection, f=True)

		except:
			log.warning("Could not connect {} to {}. This may already be connected.".format(src_conneciton,
			                                                                                dst_connection))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	nodes = []
	data = iolib.json.read(file_path)
	for dst_connection, src_conneciton in data.items():
		nodes.extend([dst_connection.split(".")[0], src_conneciton.split(".")[0]])

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
		for destination, source in data.items():
			r_destination = destination.replace(search, replace) if search in destination else destination
			r_source = source.replace(search, replace) if search in source else source
			new_data[r_destination] = r_source

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
