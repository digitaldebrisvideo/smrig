import logging

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import sys

if sys.version_info[0] < 3:
    string_types = (str, unicode)
else:
    string_types = (str,)

from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.attributeslib.tag")
keyable_attributes_tag = "smrigKeyableAttributes"


def add_lock_attributes_tag(nodes, attributes, keyable=False, locked=True, channel_box=False):
	"""

	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	attributes = utilslib.conversion.as_list(attributes)
	values = {"keyable": keyable, "locked": locked, "channel_box": channel_box}
	data = {k: values for k in attributes}

	for node in nodes:
		if not cmds.objExists("{}.{}".format(node, keyable_attributes_tag)):
			cmds.addAttr(node, ln=keyable_attributes_tag, dt="string")
		cmds.setAttr("{}.{}".format(node, keyable_attributes_tag), str(data), type="string")


def add_tag_attribute(node, attribute_name, value=None):
	"""
	Create a non-keyable attribute that is not visible in out channel box.
	It can be used to tag a node with a certain value that can later be
	retrieved. The tag attribute will be locked so it cannot be changed
	un-intentionally.

	:param str node:
	:param str attribute_name:
	:param str/int/float value:
	"""
	# add attribute
	path = "{}.{}".format(node, attribute_name)
	if not cmds.objExists(path):
		if value is None:
			cmds.addAttr(node, longName=attribute_name, attributeType="message")
		elif isinstance(value, string_types):
			cmds.addAttr(node, longName=attribute_name, dataType="string")
		elif isinstance(value, int):
			cmds.addAttr(node, longName=attribute_name, attributeType="long", defaultValue=value)
		elif isinstance(value, float):
			cmds.addAttr(node, longName=attribute_name, attributeType="double", defaultValue=value)
		else:
			error_message = "Value type '{}' is not supported".format(type(value))
			log.error(error_message)
			raise ValueError(error_message)

	# set attribute
	if value is not None:
		arguments = {"type": "string"} if isinstance(value, string_types) else {}
		cmds.setAttr(path, value, **arguments)


def get_tagged_nodes(attribute_name, value=None, full_path=True):
	"""
	Get the tagged node from an attribute name and value. All nodes will be
	checked to see if they contain the attribute name. If they do and it
	matches the value if any is specified the node will be returned. It is
	possible to return full names or partial names.

	:param str attribute_name:
	:param str/int/float value:
	:param bool full_path:
	:return: Tagged nodes
	:rtype: list
	"""
	# variables
	matches = set()
	plug_func = None
	sel = OpenMaya.MSelectionList()

	# get plug func
	if value is not None:
		if isinstance(value, string_types):
			plug_func = "asString"
		elif isinstance(value, int):
			plug_func = "asInt"
		elif isinstance(value, float):
			plug_func = "asFloat"
		else:
			error_message = "Value type '{}' is not supported".format(type(value))
			log.error(error_message)
			raise ValueError(error_message)

	# populate selection, when no nodes with the attribute exists it will
	# raise a runtime error. An empty list is returned
	try:
		sel.add("*.{}".format(attribute_name), searchChildNamespaces=True)
	except RuntimeError:
		return []

	# loop selection
	for i in range(sel.length()):
		plug = sel.getPlug(i)
		if value is not None:
			try:
				plug_value = getattr(plug, plug_func)()
				if value != plug_value:
					continue

			except RuntimeError:
				continue

		node = plug.node()
		if node.hasFn(OpenMaya.MFn.kDagNode):
			for dag in OpenMaya.MDagPath.getAllPathsTo(node):
				if full_path:
					matches.add(dag.fullPathName())
				else:
					matches.add(dag.partialPathName())
		else:
			dep = OpenMaya.MFnDependencyNode(node)
			matches.add(dep.name())

	return list(matches)
