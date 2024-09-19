import logging

import maya.cmds as cmds

from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.attributeslib.common")

__all__ = [
	"add_spacer_attribute",
	"get_selected_attributes",
	"get_locked_attributes",
	"set_attributes",
	"reset_attributes",
	"reset_attributes_wildcard",
	"create_float3_attribute"
]

TRANSLATE_CHANNELS = ["translateX", "translateY", "translateZ"]
ROTATE_CHANNELS = ["rotateX", "rotateY", "rotateZ"]
SCALE_CHANNELS = ["scaleX", "scaleY", "scaleZ"]
VISIBILITY_CHANNEL = "visibility"
LOCK_CHANNEL = "lockChannels"


# ----------------------------------------------------------------------------


def add_spacer_attribute(node, attribute_name="CONTROLS"):
	"""
	Add an empty enum attribute to the given node for adding a space between
	attribute groups in the channelbox. The attribute is non-keyable and
	locked. The attribute name defaults to "CONTROLS". Spacer attributes are
	always to be upper case. Any attribute name provided will be upper cased
	to ensure consistency.

	Example:
		.. code-block:: python

			add_spacer_attribute(node='L_hand_001_CTL', attribute_name='handPoses')
			>> Hand Poses: ------------

	:param str node:
	:param str attribute_name:
	"""
	attribute_name = attribute_name.upper()
	if cmds.objExists("{}.{}".format(node, attribute_name)):
		return
	cmds.addAttr(node, longName=attribute_name, nn="_" * 15, attributeType="enum", enumName=" ", k=True)


# cmds.setAttr("{}.{}".format(node, attribute_name), edit=True, lock=True, channelBox=True, keyable=False)


# ----------------------------------------------------------------------------


def get_selected_attributes(node_path=False, full_path=False):
	"""
	Get the selected attributes in the channel box. It is possible to have the
	selected node paths prepended to attributes.

	:param bool node_path:
	:param bool full_path:
	:return: Selected attributes
	:rtype: list[str]
	"""
	# validate paths
	if full_path and not node_path:
		log.warning("Full path attributes cannot be returned "
		            "as the node name is to be ignored.")

	# variables
	attributes = []

	# get channel box
	channel_box = utilslib.mel.get_mel_global_variable("$gChannelBoxName")
	channel_box_options = [
		("mainObjectList", "selectedMainAttributes"),
		("shapeObjectList", "selectedShapeAttributes"),
		("historyObjectList", "selectedHistoryAttributes"),
		("outputObjectList", "selectedOutputAttributes"),
	]

	# get selected attributes
	for obj_arg, attr_arg in channel_box_options:
		attrs = cmds.channelBox(channel_box, query=True, **{attr_arg: True}) or []
		if not node_path:
			attributes.extend(attrs)
			continue

		nodes = cmds.channelBox(channel_box, query=True, **{obj_arg: True}) or []
		attributes.extend(
			[
				"{}.{}".format(node, attr)
				for node in nodes
				for attr in attrs
				if cmds.attributeQuery(attr, node=node, exists=True)
			]

		)

	# get full path
	if node_path and full_path:
		attributes = cmds.ls(attributes, l=True)

	return attributes


def get_locked_attributes(node, attribute_name):
	"""
	Loop the attribute and potential children and see if any of the attributes
	are locked. Locked attributes will be returned.

	:param node:
	:param attribute_name:
	:return: Locked attributes
	:rtype: list
	"""
	attribute_path = "{}.{}".format(node, attribute_name)
	children = cmds.attributeQuery(attribute_name, node=node, listChildren=True)
	if not children and cmds.getAttr(attribute_path, lock=True):
		return [attribute_path]

	if children and cmds.getAttr(attribute_path, lock=True):
		return [c for c in children]
	elif children:
		return [
			child
			for child in children
			if cmds.getAttr("{}.{}".format(node, child), lock=True)
		]

	return []


# ----------------------------------------------------------------------------


def set_attributes(nodes, attributes, user_defined=False, lock=None, keyable=None, channel_box=None):
	"""
	Set the locked, keyable and channel box state of a list of attributes. It
	is possible to pick standard from commonly used attribute that will be
	appended to the attributes list.

	:param str/list nodes:
	:param str/list attributes:
	:param bool user_defined:
	:param bool lock:
	:param bool keyable:
	:param bool channel_box:
	"""

	def process_attribute(node, attribute):
		# get path
		node_attribute_path = "{}.{}".format(node, attribute)

		# get arguments
		arguments = {}
		arguments.update({"keyable": keyable} if keyable is not None else {})
		arguments.update({"lock": lock} if lock is not None else {})

		# set arguments
		if arguments:
			cmds.setAttr(node_attribute_path, **arguments)

		# set channel box
		if channel_box is not None:
			cmds.setAttr(node_attribute_path, channelBox=channel_box)

	# convert to list
	nodes = utilslib.conversion.as_list(nodes)
	attributes = utilslib.conversion.as_list(attributes)

	# handle nodes
	for node in nodes:
		# add user defined attributes
		node_attributes = attributes[:]
		if user_defined:
			node_attributes.extend(cmds.listAttr(node, userDefined=True) or [])

		# loop attributes
		for attribute in node_attributes:
			# validate attribute
			if not cmds.attributeQuery(attribute, node=node, exists=True):
				log.debug("Unable to process attribute '{}.{}', it doesn't exist.".format(node, attribute))
				continue

			# get children attributes
			component_attributes = cmds.attributeQuery(attribute, node=node, listChildren=True) or []
			component_attributes.append(attribute) if not component_attributes else None

			# set attributes
			for component_attribute in component_attributes:
				process_attribute(node, component_attribute)


# ----------------------------------------------------------------------------


def reset_attributes(nodes, user_defined=False, ignore_types=None):
	"""
	Resets the keyable attributes on the provided nodes. The set attributes
	are run in a catch and warning messages will be printed when the attribute
	cannot be set.

	The user defined flag can be used to only reset user defined attributes
	and the ignore types list can be used to ignore resetting certain
	attributes of a specific type.

	:param str/list nodes:
	:param bool user_defined:
	:param str/list/None ignore_types:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	ignore_types = utilslib.conversion.as_list(ignore_types)

	for node in nodes:
		attributes = cmds.listAttr(node, keyable=True, settable=True, unlocked=True, userDefined=user_defined) or []
		attributes.reverse()

		for attribute in attributes:
			attribute_path = "{}.{}".format(node, attribute)
			attribute_type = cmds.getAttr(attribute_path, type=True)

			if ignore_types and attribute_type in ignore_types:
				log.debug("Ignored attribute '{}' on node '{}' as it is of "
				          "type '{}'.".format(attribute, node, attribute_type))

				continue

			default_value = cmds.attributeQuery(attribute, node=node, listDefault=True)[0]

			try:
				cmds.setAttr("{}.{}".format(node, attribute), default_value)
			except Exception as e:
				log.warning(e.message)


def reset_attributes_wildcard(search, user_defined=False, ignore_types=None):
	"""
	Resets the keyable channels on the nodes defined in the wildcard "search"
	argument. Only transforms will be processed.

	Example:
		Like, "*_CTL" ot "Nezha_01_NS:*_CTL" that defines the controls
		(or any nodes) that you want to reset too their creation value.

		.. code-block:: python

			# reset keyable attributes on all controls
			reset_attributes_wildcard("*_CTL")

	:param str search:
	:param bool user_defined:
	:param str/list/None ignore_types:
	"""
	nodes = cmds.ls(search, transforms=True)
	reset_attributes(nodes, user_defined, ignore_types)


def create_float3_attribute(node, attribute_name):
	"""
	Create a 3 float attribute XYZ
	:param node:
	:param attribute_name:
	:return:
	"""
	cmds.addAttr(node, ln=attribute_name, at="float3", k=1)
	cmds.addAttr(node, ln="{}X".format(attribute_name), k=1, at="float", parent=attribute_name)
	cmds.addAttr(node, ln="{}Y".format(attribute_name), k=1, at="float", parent=attribute_name)
	cmds.addAttr(node, ln="{}Z".format(attribute_name), k=1, at="float", parent=attribute_name)
