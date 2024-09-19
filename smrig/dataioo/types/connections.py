import logging

import maya.cmds as cmds
from smrig.dataioo import utils

deformer_type = "connections"
file_type = "json"

log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(node, **kwargs):
	"""

	:param node:
	:param kwargs:
	:return:
	"""
	data = {"name": node,
	        "connections": utils.get_connections(node),
	        "deformer_type": deformer_type}

	return data


def set_data(data, **kwargs):
	"""
	Create connections

	:param data:
	:param kwargs:
	:return:
	"""
	for src_conneciton, dst_connection in data.get("connections"):
		try:
			cmds.connectAttr(src_conneciton, dst_connection, f=True)
		except:
			log.warning(
				"Could not connect {} to {}. This may already be connected.".format(src_conneciton, dst_connection))
