import maya.cmds as cmds

from smrig.lib import naminglib

TRANSFORM_NODES = ["animControl", "animControlPivot"]
JOINT_NODES = ["jointPlacer"]


def node(node_type,
         name,
         generate_new_index=True,
         parent=None,
         **kwargs):
	"""
	Create a node, the naming of the suffix of the node will be handled by
	this function. Any additional keyword arguments available in the
	cmds.createNode function can be used here as well.

	:param node_type:
	:param name:
	:param generate_new_index:
	:param parent:
	:param suffix:
	:param kwargs:
	:return:
	"""
	name = naminglib.format_name(naminglib.strip_suffix(name),
	                             node_type=node_type,
	                             generate_new_index=generate_new_index)

	node_type = "transform" if node_type in TRANSFORM_NODES else node_type
	node_type = "joint" if node_type in JOINT_NODES else node_type

	if parent:
		new_node = cmds.createNode(node_type, name=name, parent=parent, **kwargs)
	else:
		new_node = cmds.createNode(node_type, name=name, **kwargs)

	return new_node


def locator(nodes=None, name="locator#", relative=False, absolute=True, local_scale=0.5):
	"""
	Wrapper to create a locator. The benefit of this wrapper function is that
	the local scale can be set during creation.

	:param nodes:
	:param name:
	:param relative:
	:param absolute:
	:param local_scale:
	:return:
	"""
	# build name
	locator = cmds.spaceLocator(name=name, relative=relative, absolute=absolute)[0]

	# set local scale
	local_scale = local_scale if isinstance(local_scale, list) else [local_scale] * 3
	cmds.setAttr("{}.localScale".format(locator), *local_scale)

	return locator
