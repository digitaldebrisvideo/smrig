import logging

import maya.cmds as cmds

from smrig.lib import nodepathlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.attributeslib.connection")


def get_next_free_multi_index(attribute_path, start_index=0):
	"""
	Get the next free multi index of a attribute. This is a python
	implementation of the mel command 'getNextFreeMultiIndex'.

	:param str attribute_path:
	:param int start_index:
	:return: Available index
	:rtype: int
	"""
	# assume a max of 10 million connections
	while start_index < 10000000:
		attribute_index_path = "{}[{}]".format(attribute_path, start_index)
		connection_info = cmds.connectionInfo(attribute_index_path, sourceFromDestination=True) or []
		if not connection_info:
			return start_index

		start_index += 1

	return 0


# ----------------------------------------------------------------------------


def break_connection(destination_plug):
	"""
	Break the any incoming connections to the provided destination plug.
	It is first checked to see if the source is still connected before an
	attempt is made to disconnect.

	:param str destination_plug:
	"""
	source_plugs = cmds.listConnections(destination_plug, source=True, destination=False, plugs=True) or []
	for source_plug in source_plugs:
		if cmds.isConnected(source_plug, destination_plug):
			cmds.disconnectAttr(source_plug, destination_plug)


def break_connections(nodes, attributes, user_defined=False):
	"""
	Set the locked, keyable and channel box state of a list of attributes. It
	is possible to pick standard from commonly used attribute that will be
	appended to the attributes list.

	:param str/list nodes:
	:param str/list attributes:
	:param bool user_defined:
	"""
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
				log.debug("Unable to process break connections of attribute '{}.{}', "
				          "it doesn't exist.".format(node, attribute))

				continue

			# get children attributes
			component_attributes = cmds.attributeQuery(attribute, node=node, listChildren=True) or []
			component_attributes.append(attribute)

			# set attributes
			for component_attribute in component_attributes:
				break_connection("{}.{}".format(node, component_attribute))


# ----------------------------------------------------------------------------


def reverse_connection(source_plug, target_plug=None):
	"""
	The reverse connection will reverse the input from the source and connect
	this reverse value into the target plug. The reverse connection turns a
	value of 0 into 1 and the other way round.

	:param str source_plug:
	:param str target_plug:
	:return: Reverse plug
	:rtype: str
	"""
	name = nodepathlib.get_leaf_name(source_plug.replace(".", "_"))
	rev = cmds.createNode("reverse", name="{}_REV".format(name))
	cmds.connectAttr(source_plug, "{}.inputX".format(rev))

	# connect to target plug if is defined
	reverse_plug = "{}.outputX".format(rev)
	if target_plug:
		cmds.connectAttr(reverse_plug, target_plug, force=True)

	return reverse_plug


def negative_connection(source_plug, target_plug=None):
	"""
	The negative connection will multiply the input plug with a value of -1 and
	connect this value to the target plug.

	:param str source_plug:
	:param str target_plug:
	:return: Negative plug
	:rtype: str
	"""
	name = nodepathlib.get_leaf_name(source_plug.replace(".", "_"))
	mdl = cmds.createNode("multDoubleLinear", name="{}_MDL".format(name))
	cmds.setAttr("{}.input2".format(mdl), -1)
	cmds.connectAttr(source_plug, "{}.input1".format(mdl))

	# connect to target plug if is defined
	negative_plug = "{}.output".format(mdl)
	if target_plug:
		cmds.connectAttr(negative_plug, target_plug, force=True)

	return negative_plug


def multiply_connection(source_plug, multiply_plug=None, multiply_value=1.0, target_plug=None):
	"""
	The multiply connection will multiply the input plug with a value or another plug and
	connect this value to the target plug.

	:param source_plug:
	:param multiply_plug:
	:param multiply_value:
	:param target_plug:
	:return:
	"""
	name = nodepathlib.get_leaf_name(source_plug.replace(".", "_"))
	mdl = cmds.createNode("multDoubleLinear", name="{}_MDL".format(name))
	cmds.setAttr("{}.input2".format(mdl), multiply_value)
	cmds.connectAttr(source_plug, "{}.input1".format(mdl))

	if multiply_plug:
		cmds.connectAttr(multiply_plug, "{}.input2".format(mdl))

	# connect to target plug if is defined
	if target_plug:
		cmds.connectAttr("{}.output".format(mdl), target_plug, force=True)

	return "{}.output".format(mdl)


def add_connection(source_plug, add_plug=None, add_value=1.0, target_plug=None):
	"""
	The add connection will add the input plug with a value or another plug and
	connect this value to the target plug.

	:param source_plug:
	:param add_plug:
	:param add_value:
	:param target_plug:
	:return:
	"""
	name = nodepathlib.get_leaf_name(source_plug.replace(".", "_"))
	adl = cmds.createNode("addDoubleLinear", name="{}_ADL".format(name))

	cmds.setAttr("{}.input2".format(adl), add_value)
	cmds.connectAttr(source_plug, "{}.input1".format(adl))

	if add_plug:
		cmds.connectAttr(add_plug, "{}.input2".format(adl))

	# connect to target plug if is defined
	if target_plug:
		cmds.connectAttr("{}.output".format(adl), target_plug, force=True)

	return "{}.output".format(adl)


def abs_connection(source_plug, target_plug=None):
	"""
	The abs connections will return the absolute value of the source attribute
	and plug it into the target plug if it is provided. The absolute value is
	calculated by getting the power of 2 of the value and then calculating the
	square root of that value using a power of 0.5.

	:param str source_plug:
	:param str target_plug:
	:return: Abs plug
	:rtype: str
	"""
	name = nodepathlib.get_leaf_name(source_plug.replace(".", "_"))
	abs_plug = source_plug

	for i, value in enumerate([2, 0.5]):
		md = cmds.createNode("multiplyDivide", name="{}Abs{}_MD".format(name, i + 1))
		cmds.setAttr("{}.operation".format(md), 3)
		cmds.setAttr("{}.input2X".format(md), value)
		cmds.connectAttr(abs_plug, "{}.input1X".format(md))
		abs_plug = "{}.outputX".format(md)

	if target_plug:
		cmds.connectAttr(abs_plug, target_plug, force=True)

	return abs_plug


def blend_connection(first_plug=None,
                     first_value=None,
                     second_plug=None,
                     second_value=None,
                     blender_plug=None,
                     target_plug=None):
	"""
	The add connection will add the input plug with a value or another plug and
	connect this value to the target plug.

	:param first_plug:
	:param first_value:
	:param second_plug:
	:param second_value:
	:param blender_plug:
	:param target_plug:
	:return:
	"""
	bta = cmds.createNode("blendTwoAttr")
	if first_plug:
		cmds.connectAttr(first_plug, "{}.input[0]".format(bta))

	elif first_value:
		cmds.setAttr("{}.input[0]".format(bta), first_value)

	if second_plug:
		cmds.connectAttr(second_plug, "{}.input[1]".format(bta))

	elif second_value:
		cmds.setAttr("{}.input[1]".format(bta), second_value)

	if blender_plug:
		cmds.connectAttr(blender_plug, "{}.attributesBlender".format(bta))

	if target_plug:
		cmds.connectAttr("{}.output".format(bta), target_plug, force=True)

	return "{}.output".format(bta)


def get_connections(node, incoming=True, outgoing=True):
	"""
	Return incoming and outgoing connections from specified node.

	:node str: Node to query
	:incoming bool: Print incoming connections
	:outgoing bool: Print outgoing connections
	:return: Connections
	:rtype: list of sets. [(source plug, destination plug)]
	"""
	result = []
	if incoming:
		in_connections = cmds.listConnections(node, s=1, c=1, d=0, p=1, scn=1) or []
		for i in range(0, len(in_connections), 2):
			result.append((in_connections[i + 1], in_connections[i]))

	if outgoing:
		out_connections = cmds.listConnections(node, s=0, c=1, d=1, p=1, scn=1) or []
		for i in range(0, len(out_connections), 2):
			result.append((out_connections[i], out_connections[i + 1]))

	return result


def print_connections(nodes=None, incoming=True, outgoing=True):
	"""
	Print incoming and outgoing connections from specified nodes.

	:nodes list: Nodes to query
	:incoming bool: Print incoming connections
	:outgoing bool: Print outgoing connections
		:rtype: None
	"""
	nodes = nodes if nodes else cmds.ls(sl=1)
	nodes = cmds.ls(nodes)

	for node in nodes:
		if incoming:
			print("")
			message = ['Incoming connections to: {}'.format(node)]
			message.extend([', '.join(c) for c in get_connections(node, incoming=True, outgoing=False)])
			log.info('\n\t'.join(message))

		if outgoing:
			print("")
			message = ['Outgoing connections from: {}'.format(node)]
			message.extend([', '.join(c) for c in get_connections(node, incoming=False, outgoing=True)])
			log.info('\n\t'.join(message))
