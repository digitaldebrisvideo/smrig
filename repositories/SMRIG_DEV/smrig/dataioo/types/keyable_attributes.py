import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import nodepathlib
from smrig.lib import utilslib

deformer_type = "keyableAttributes"
file_type = "json"


def get_data(nodes=None, **kwargs):
	"""

	:param nodes:
	:param kwargs:
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


def set_data(data, **kwargs):
	"""

	:param data:
	:param kwargs:
	:return:
	"""
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
