import logging
from collections import OrderedDict

import maya.cmds as cmds

from smrig.lib import attributeslib
from smrig.lib import selectionlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.nodeslib.display")

# ----------------------------------------------------------------------------


DISPLAY_TYPES = OrderedDict(
	[
		("normal", 0),
		("template", 1),
		("reference", 2)
	]
)

ENABLE_ATTRIBUTE = {"displayLayer": "enabled"}
TYPE_ATTRIBUTE = {"displayLayer": "displayType"}
color_ATTRIBUTE = {"displayLayer": "color"}


# ----------------------------------------------------------------------------


def get_enable_path(node):
	"""
	:param str node:
	:return: Enable attribute path
	:rtype: str
	"""
	return "{}.{}".format(node, ENABLE_ATTRIBUTE.get(cmds.nodeType(node), "overrideEnabled"))


def get_type_path(node):
	"""
	:param str node:
	:return: Type attribute path
	:rtype: str
	"""
	return "{}.{}".format(node, TYPE_ATTRIBUTE.get(cmds.nodeType(node), "overrideDisplayType"))


def get_color_path(node):
	"""
	:param str node:
	:return: Type attribute path
	:rtype: str
	"""
	return "{}.{}".format(node, color_ATTRIBUTE.get(cmds.nodeType(node), "overrideColor"))


# ----------------------------------------------------------------------------


def set_display_override(nodes, value):
	"""
	:param str/list nodes:
	:param bool value:
	"""
	# get list
	nodes = utilslib.conversion.as_list(nodes)

	# loop nodes
	for node in nodes:
		enable_path = get_enable_path(node)
		enable_state = cmds.getAttr(enable_path)

		# only set value if it doesn"t match currently set value.
		if enable_state != value:
			cmds.setAttr(enable_path, value)


# ----------------------------------------------------------------------------


def set_display_color(nodes, color_index, shapes_only=False):
	"""
	Enables the overrideEnabled attribute on the given nodes and sets them to
	the color specified in the "color_index" flag.

	:param str/list nodes:
	:param int color_index:
	:param bool shapes_only:
		Extend the nodes with its shapes and not connect transforms.
	"""
	nodes = utilslib.conversion.as_list(nodes)

	# remove non-shape objects from the list
	if shapes_only:
		nodes = selectionlib.extend_with_shapes(nodes)
		nodes = selectionlib.exclude_type(nodes, "transform")

	# enable override
	set_display_override(nodes, True)

	# loop nodes
	for node in nodes:
		# get attributes
		display_path = get_color_path(node)

		try:
			cmds.setAttr(display_path, color_index)
		except Exception as e:
			log.warning(e.message)


def get_display_color(nodes):
	"""
	Get the color index from the nodes, the nodes will be extended with the
	shapes and see if an override is enabled if it is the first color index
	will be returned.

	:param str/list nodes:
	:return: color index
	:rtype: int/None
	"""
	nodes = utilslib.conversion.as_list(nodes)
	nodes = selectionlib.extend_with_shapes(nodes)

	for node in nodes:
		enable_path = get_enable_path(node)
		if cmds.getAttr(enable_path):
			display_path = get_color_path(node)
			return cmds.getAttr(display_path)


# ----------------------------------------------------------------------------


def set_historical_importance(nodes, value=0):
	"""
	Helper function to set the historical importance of the provided nodes to
	the provided value. Any of the setting of the attributes is captures in
	case any fail a warning message will be printed.

	:param str/list nodes:
	:param int value: 0, 1 or 2
	"""
	for node in utilslib.conversion.as_list(nodes):
		node_attribute_path = "{}.isHistoricallyInteresting".format(node)
		if not cmds.objExists(node):
			log.warning(
				"Attribute '{}' doesn't exist and cannot have its value "
				"set.".format(node_attribute_path)
			)
			continue

		try:
			cmds.setAttr(node_attribute_path, value)
		except Exception as e:
			log.warning(e.message)


def get_historical_importance(nodes):
	"""
	Get the historical importance of the provided nodes. The length of the
	list returned corresponds to the number of nodes provided.

	:param str/list nodes:
	:return: Historical importance
	:rtype: list
	"""
	historical_importance = []

	for node in utilslib.conversion.as_list(nodes):
		node_attribute_path = "{}.isHistoricallyInteresting".format(node)
		if not cmds.objExists(node_attribute_path):
			log.warning(
				"Attribute '{}' doesn't exist and cannot have its value "
				"read.".format(node_attribute_path)
			)
			continue

		value = cmds.getAttr(node_attribute_path)
		historical_importance.append(value)

	return historical_importance


# ----------------------------------------------------------------------------


def set_display_type(nodes, display_type="reference", shapes_only=False):
	"""
	Enables the overrideEnabled attribute on the given nodes and sets them to
	the type specified in the "display_type" flag.

	Example:
		Will set everything with the extension "_PLY" to reference mode making
		them un-selectable:

		.. code-block:: python

			set_display_override(nodes=cmds.ls(sl="*_PLY"), display_override="reference")

	:param str/list nodes:
	:param str display_type:
	:param bool shapes_only:
		Extend the nodes with its shapes and not connect transforms.
	"""
	display_index = DISPLAY_TYPES.get(display_type)
	nodes = utilslib.conversion.as_list(nodes)

	# remove non-shape objects from the list
	if shapes_only:
		nodes = selectionlib.extend_with_shapes(nodes)
		nodes = selectionlib.exclude_type(nodes, "transform")

	# enable override
	set_display_override(nodes, True)

	# loop nodes
	for node in nodes:
		# get attributes
		display_path = get_type_path(node)

		try:
			cmds.setAttr(display_path, display_index)
		except Exception as e:
			log.warning(e.message)


def create_display_type_link(control, nodes, attribute_name="model_display", display_type="reference"):
	"""
	Create a display override attribute and link it to the override types of
	all of the provided nodes. Ideally used to setup a control that is able
	to change the display override attributes on all geometry.

	:param str control:
	:param str/list nodes:
	:param str attribute_name:
	:param str display_type:
	"""
	# set display overrides
	nodes = utilslib.conversion.as_list(nodes)
	set_display_type(nodes, display_type)

	# create attribute
	attribute_path = "{}.{}".format(control, attribute_name)
	if not cmds.objExists(attribute_path):
		display_index = DISPLAY_TYPES.get(display_type)

		cmds.addAttr(
			control,
			longName=attribute_name,
			attributeType="enum",
			enumName=":".join(DISPLAY_TYPES.keys()),
			defaultValue=display_index,
		)
		cmds.setAttr(attribute_path, edit=True, keyable=False, channelBox=True)

	# loop nodes
	for node in nodes:
		display_path = get_type_path(node)
		control_path = "{}.{}".format(control, attribute_name)

		if not cmds.isConnected(control_path, display_path):
			cmds.connectAttr(control_path, display_path, force=True)


# ----------------------------------------------------------------------------


def create_visibility_link(control, nodes, attribute_name="secondary", default_value=0, shapes_only=False):
	"""
	Connects the given "nodes" to the named "attribute_name" on the given
	"control". The function prefers to do the visibility connections on a
	shape level, as this is the default behaviour. It is possible to connect
	the visibility of shapeless transforms by making sure the "shapes_only"
	argument is set to False.

	Example:
		This will connect all the *_CTL nodes to an attribute called
		"secondaryControls" - also the default - to the C_global_CTL.

		.. code-block:: python

			connect_to_visibility(
				control="C_global_CTL",
				nodes=["C_global2_CTL", "C_global3_CTL"],
				attribute_name="secondaryControls"
			)

	:param str control:
	:param str/list nodes:
	:param str attribute_name:
	:param int default_value:
	:param bool shapes_only:
	"""
	nodes = utilslib.conversion.as_list(nodes)

	# create attribute
	attribute_path = "{}.{}".format(control, attribute_name)
	if not cmds.objExists(attribute_path):
		cmds.addAttr(
			control,
			longName=attribute_name,
			attributeType="long",
			minValue=0,
			maxValue=1,
			defaultValue=default_value
		)

		cmds.setAttr(attribute_path, edit=True, keyable=False, channelBox=True)

	# link attribute
	for node in nodes:
		# get node shapes
		node_shapes = cmds.listRelatives(node, shapes=True) or []

		# append node if no shapes are found and transforms are allowed
		if not shapes_only:
			node_shapes = [node]

		# validate node shapes
		if not node_shapes:
			log.warning("Node '{}' contains no valid shapes to connect visibility.".format(node))
			continue

		# connect shapes
		for node_shape in node_shapes:
			node_shape_path = "{}.visibility".format(node_shape)

			if not cmds.isConnected(attribute_path, node_shape_path):
				cmds.connectAttr(attribute_path, node_shape_path, force=True)


# ----------------------------------------------------------------------------


def create_resolution_link(control, nodes, display_types, attribute_name="modelResolution", default_value="render"):
	"""
	Create a display override attribute and link it to the override types of
	all of the provided nodes. Ideally used to setup a control that is able
	to change the display override attributes on all geometry.

	:param control:
	:param nodes:
	:param display_types:
	:param attribute_name:
	:param default_value:
	:return:
	"""
	# set display overrides
	nodes = utilslib.conversion.as_list(nodes)
	nodes = [utilslib.conversion.as_list(n) for n in nodes]

	display_types = utilslib.conversion.as_list(display_types)

	# create attribute
	attribute_path = "{}.{}".format(control, attribute_name)
	display_index = display_types.index(default_value) if default_value in display_types else 0

	if not cmds.objExists(attribute_path):

		cmds.addAttr(
			control,
			longName=attribute_name,
			attributeType="enum",
			enumName=":".join(display_types),
			defaultValue=display_index,
		)
		cmds.setAttr(attribute_path, edit=True, keyable=False, channelBox=True)

	else:

		cmds.addAttr(
			attribute_path,
			edit=True,
			enumName=":".join(display_types),
			defaultValue=display_index,
		)
		cmds.setAttr(attribute_path, edit=True, keyable=False, channelBox=True)

	cmds.setAttr(attribute_path, display_index)

	# loop nodes and create choice nodes
	choices = [cmds.createNode("choice") for n in nodes]

	for choice in choices:
		for i, node in enumerate(nodes):
			cmds.setAttr("{}.input[{}]".format(choice, i), 0)

	for i, node in enumerate(nodes):
		choice = choices[i]
		cmds.setAttr("{}.input[{}]".format(choice, i), 1)
		cmds.connectAttr(attribute_path, choice + ".selector")

		for n in node:
			cmds.connectAttr(choice + ".output", n + ".v", f=True)


def create_uniform_scale_link(node, min=0.001):
	"""
	Connect scale Y to scale X and Z for given node.
	Will alias scaleY to UniformScale

	:param str node:
	:param float min: minimum scale limit
	:return:
	"""
	if min:
		cmds.transformLimits(node, sy=[min, 1], esy=[1, 0])

	cmds.connectAttr("{}.sy".format(node), "{}.sx".format(node))
	cmds.connectAttr("{}.sy".format(node), "{}.sz".format(node))
	attributeslib.set_attributes(node, ["sx", "sz"], lock=True, keyable=False)

	cmds.aliasAttr("UniformScale", "{}.sy".format(node))
