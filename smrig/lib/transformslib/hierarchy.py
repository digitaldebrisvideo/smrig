import logging

import maya.cmds as cmds

from smrig.lib import naminglib
from smrig.lib import nodeslib

log = logging.getLogger("smrig.lib.transformslib.hierarchy")

"""
RIG_SETS = {
    JOINT_SET: ["*_JNT"],
    ANIM_CACHE_SET: ["*_anim_PLY", "*_PLY"],
    CACHE_SET: ["*_GES", "*_GEP", "*_GEV"],
    CONTROL_SET: ["*_CTL"]
}
"""


# ----------------------------------------------------------------------------


def null_grp(name="null", node=None, reference_node=None, freeze=False):
	"""
	Places the object in "node" under a pivot matching group which absorbs the
	transform, setting the transform values to zero. If a reference node is
	used the transforms can be frozen to still zero out the transforms even
	though its parent is not in the same position.

	It contrary to the :meth:`~null_grp_multi` this function will only create
	one null group, this null group is returned as a string.

	:param str name:
	:param str/None node:
	:param str/None reference_node:
	:param bool freeze:
	:param bool empty:
	:return: Null group
	:rtype: str
	"""
	return null_grp_multi(
		name=name,
		node=node,
		reference_node=reference_node,
		freeze=freeze,
		num=1
	)[0]


def null_grp_multi(name=None,
                   node=None,
                   parent=None,
                   reference_node=None,
                   freeze=False,
                   reverse_order=False,
                   node_type="transform",
                   num=1):
	"""
	Places the object in "node" under a pivot matching group which absorbs the
	transform, setting the transform values to zero. If a reference node is
	used the transforms can be frozen to still zero out the transforms even
	though its parent is not in the same position.

	:param name:
	:param node:
	:param parent:
	:param reference_node:
	:param freeze:
	:param reverse_order:
	:param node_type:
	:param num:
	:return:
	"""
	if not num:
		return []

	groups = []
	name = naminglib.strip_suffix(name if name else node)

	for i in range(num) if reverse_order else reversed(range(num)):
		group = nodeslib.create_node(node_type, "{}_offset{}".format(name, i) if i else "{}_offset".format(name))

		if groups:
			cmds.parent(group, groups[-1])

		groups.append(group)

	if node and cmds.objExists(node):
		node_parent = cmds.listRelatives(node, p=1)
		if node_parent:
			cmds.parent(groups[0], node_parent)

	elif parent and cmds.objExists(parent):
		cmds.parent(groups[0], parent)

	cmds.xform(groups[0], a=1, t=[0, 0, 0], ro=[0, 0, 0])
	cmds.xform(groups[0], r=1, s=[1, 1, 1])

	if reference_node and cmds.objExists(reference_node):
		cmds.delete(cmds.parentConstraint(reference_node, groups[0]))

	if freeze:
		cmds.makeIdentity(groups, apply=1, t=1, r=1, s=1, n=0, pn=1)

	if node and cmds.objExists(node):
		cmds.parent(node, groups[-1])

	return groups
