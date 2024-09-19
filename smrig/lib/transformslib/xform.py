import logging

import maya.cmds as cmds
from maya import OpenMaya as OpenMaya

from smrig.lib import decoratorslib
from smrig.lib import mathlib
from smrig.lib import nodeslib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.transformslib.xform")


@decoratorslib.preserve_selection
def match(source, targets, translate=True, rotate=True, scale=False, pivot=False):
	"""
	Match the transformation from source to targets in world space. By default
	the translation and rotation will be matched. If the "pivot" is defined it
	will override the "translate" argument.

	:param str source:
	:param str/list targets:
	:param bool translate: Match translate
	:param bool rotate: Match rotate
	:param bool scale: Match scale
	:param bool pivot: Match the object's pivot rather than it's translate
	:raise ValueError: When no match dataexporter is provided.
	"""
	arguments = {}
	targets = utilslib.conversion.as_list(targets)

	# populate arguments
	if pivot:
		arguments["translation"] = cmds.xform(source, query=True, rotatePivot=True, worldSpace=True)
	elif translate:
		arguments["translation"] = cmds.xform(source, query=True, translation=True, worldSpace=True)
	if rotate:
		arguments["rotation"] = cmds.xform(source, query=True, rotation=True, worldSpace=True)
	if scale:
		arguments["scale"] = cmds.xform(source, query=True, scale=True, worldSpace=True)

	# validate arguments
	if not arguments:
		error_message = "Unable to perform match as no match dataexporter is provided."
		log.error(error_message)
		raise ValueError(error_message)

	# loop targets
	for target in targets:
		cmds.xform(target, worldSpace=True, **arguments)

		if rotate:
			tmp = cmds.duplicate(target, po=True)
			cmds.delete(cmds.pointConstraint(source, tmp))
			cmds.delete(cmds.orientConstraint(source, tmp))
			cmds.xform(target, a=True, ro=cmds.xform(tmp, q=True, a=True, ro=True))
			cmds.delete(tmp)


def match_blend(target1, target2, node, weight=0.5, return_only=False):
	"""

	:param target1:
	:param target2:
	:param node:
	:param weight:
	:return:
	"""
	target1_xforms = cmds.xform(target1, ws=True, t=True, q=True)
	target2_xforms = cmds.xform(target2, ws=True, t=True, q=True)

	v1 = OpenMaya.MVector(target1_xforms[0], target1_xforms[1], target1_xforms[2])
	v2 = OpenMaya.MVector(target2_xforms[0], target2_xforms[1], target2_xforms[2])

	result = (v1 * (1.0 - weight)) + (v2 * weight)

	if not return_only:
		cmds.xform(node, ws=1, t=[result.x, result.y, result.z])

	return [result.x, result.y, result.z]


def match_locator(source=None, name=None, node_type="locator", parent=None):
	"""
	Create and snap a locator.

	:param source:
	:param name:
	:param node_type:
	:param parent:
	:return:
	"""
	components = cmds.ls(source) if source else cmds.ls(sl=1)
	position = mathlib.get_center_from_bounding_box(components)

	joint_nodes = [c for c in components if cmds.nodeType(c) == "joint"]
	transform_nodes = [c for c in components if cmds.nodeType(c) == "transform"]

	locator = nodeslib.create.locator(name=name)
	if joint_nodes + transform_nodes and position == [0, 0, 0]:
		cmds.delete(cmds.pointConstraint(joint_nodes + transform_nodes, locator))

	else:
		cmds.xform(locator, ws=1, t=position)

	if node_type != "locator":
		cmds.delete(cmds.listRelatives(locator, s=True))

	if parent:
		cmds.parent(locator, parent)

	return locator


def match_pivot(source, targets):
	"""
	Match the pivot of the nodes in "targets" to the node in source without
	moving the actual objects.

	:param str source:
	:param str/list targets:
	"""
	targets = utilslib.conversion.as_list(targets)
	pivot = cmds.xform(source, query=True, worldSpace=True, rotatePivot=True)

	for target in targets:
		cmds.xform(target, preserve=True, worldSpace=True, rotatePivot=pivot)
		cmds.xform(target, preserve=True, worldSpace=True, scalePivot=pivot)


def print_transforms(nodes=None, world_space=True, absolute=False):
	"""
	Print world transforms as maya python command.

	:nodes list/str: Node(s) to query.
		:rtype: None
	"""
	nodes = nodes if nodes else cmds.ls(sl=1)
	nodes = cmds.ls(nodes)

	for node in nodes:
		if world_space:
			translates = [round(v, 4) for v in cmds.xform(node, q=1, ws=1, t=1)]
			rotates = [round(v, 4) for v in cmds.xform(node, q=1, ws=1, ro=1)]
			print('cmds.xform("{}", ws=True, t={}, ro={})'.format(node, translates, rotates))

		elif absolute:
			translates = [round(v, 4) for v in cmds.xform(node, q=1, a=1, t=1)]
			rotates = [round(v, 4) for v in cmds.xform(node, q=1, a=1, ro=1)]
			print('cmds.xform("{}", a=True, t={}, ro={})'.format(node, translates, rotates))


@decoratorslib.preserve_selection
def get_selection_position(selection=None):
	"""

	:param selection:
	:return:
	"""
	locator = match_locator(selection)
	pos = cmds.xform(q=True, ws=True, t=True)
	cmds.delete(locator)

	return pos


@decoratorslib.preserve_selection
def match_selection_position(selection=None):
	"""

	:param selection:
	:return:
	"""
	selection = selection if selection else cmds.ls(sl=1)
	locator = match_locator(selection[:-1])
	pos = cmds.xform(q=True, ws=True, t=True)
	cmds.delete(locator)

	cmds.xform(selection[-1], ws=1, t=pos)
	return pos
