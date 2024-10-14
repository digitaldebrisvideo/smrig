import logging

import maya.cmds as cmds
from smrig.dataioo import tools

deformer_type = "attributeValues"
file_type = "json"

log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(node, **kwargs):
	"""

	:param node:
	:param kwargs:
	:return:
	"""
	locked_atrs = cmds.listAttr(node, l=True) or []
	attrs = cmds.listAttr(node, k=True) or [] + cmds.listAttr(node, cb=True) or []
	attrs = [a for a in attrs if a not in locked_atrs]

	attrs_data = tools.get_attributes_data(node, attrs)

	data = {"name": node,
	        "nodes": [node],
	        "deformer_type": deformer_type,
	        "attributes": attrs_data}

	return data


def set_data(data, **kwargs):
	"""

	:param data:
	:param kwargs:
	:return:
	"""
	tools.set_attributes_data(data.get("nodes")[0], data.get("attributes"))
