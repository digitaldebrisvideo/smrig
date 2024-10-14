import logging

import maya.cmds as cmds

from smrig.lib import constraintslib
from smrig.lib import mathlib
from smrig.lib import nodeslib
from smrig.lib import selectionlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.kinematicslib.joint")


def orient_chain(root_joints, orientation="xyz", secondary_orientation="yup"):
	"""
	Orient chain, all of the children of the chain will be orientated the same
	as the provided roots. All children that do not have another joint as a
	child will be orientated to the previous joint.

	:param list root_joints:
	:param str orientation:
	:param str secondary_orientation:
	"""
	# filter roots
	root_joints = selectionlib.filter_by_type(root_joints, types="joint")

	# validate joints
	if not root_joints:
		error_message = "Provided roots should be of type 'joint'."
		log.error(error_message)
		raise ValueError(error_message)

	# orient roots and children
	cmds.joint(
		root_joints,
		edit=True,
		orientJoint=orientation,
		secondaryAxisOrient=secondary_orientation,
		children=True,
		zeroScaleOrient=True
	)

	# orient children without parent to the world
	children = cmds.listRelatives(root_joints, type="joint", allDescendents=True, fullPath=True) or []
	for child in children:
		if not cmds.listRelatives(child, type="joint", children=True):
			cmds.joint(
				child,
				edit=True,
				orientJoint="none",
				children=False,
				zeroScaleOrient=True
			)


def duplicate_chain(joints, search="JNT", replace="ik_JNT"):
	"""
	Duplicate a joint chain.

	:param joints:
	:param search:
	:param replace:
	:return:
	"""
	new_chain = [cmds.duplicate(j, n=j.replace(search, replace), po=True)[0] for j in joints]

	for i in range(1, len(new_chain), 1):
		cmds.parent(new_chain[i], new_chain[i - 1])

	return new_chain


def create_box_joints(joints, name, control=None):
	"""
	Creates polygon cubes along the length of each given joint. The width and
	depth of the cubes are determined by the radius of the joint. If a control
	is provided a visibility switch will be setup and connected to the group.

	:param list joints:
	:param str name:
	:param str control:
	:return: Group node
	:rtype: str
	"""
	# variable
	container_name = "{}_GRP".format(name)
	attribute_name = "{}_vis".format(name)

	# create container
	if not cmds.objExists(container_name):
		cmds.group(name=container_name, empty=True, world=True)

	# set container display type to reference
	nodeslib.display.set_display_type(container_name, display_type="reference")

	# create box joints
	for joint in joints:
		# only process if the joint has a joint parent
		parent = cmds.listRelatives(joint, parent=True, type="joint") or []
		parent = utilslib.conversion.get_first(parent)
		if not parent:
			continue

		# get joint info
		radius = cmds.getAttr("{}.radius".format(parent))
		distance = mathlib.get_distance_between(parent, joint)

		# create cube
		cube = cmds.polyCube(
			name="{0}_MESH".format(joint),
			width=radius / 2.0,
			depth=radius / 2.0,
			height=distance,
			axis=[1, 0, 0],
			constructionHistory=False,
		)[0]

		# position cube
		cmds.delete(cmds.pointConstraint([parent, joint], cube, maintainOffset=False))
		cmds.delete(cmds.orientConstraint(parent, cube, maintainOffset=False))

		# constraint cube
		cmds.parentConstraint(parent, cube, maintainOffset=True)
		cmds.scaleConstraint(parent, cube, maintainOffset=True)

		# parent cube
		cmds.parent(cube, container_name)

	if control:
		nodeslib.display.create_visibility_link(
			control=control,
			nodes=container_name,
			attribute_name=attribute_name,
			default_value=1,
			shapes_only=False
		)

	return container_name


def distribute_chain(joints, xform=None):
	"""
	Distribute a chain along an axis

	:param joints:
	:param xform:
	:return:
	"""
	xform = xform if xform else [10.0, 0, 0]
	div = [float(x) / len(joints[:-1]) for x in xform]

	for i, joint in enumerate(joints):
		cmds.xform(joint, a=1, t=[i * div[0], i * div[1], i * div[2]])


def breakout_rotations(joint):
	"""
	Breakout ritations into each joint for x y and z

	:return:
	"""
	rx = cmds.duplicate(joint, n=joint + 'X', po=1)[0]
	ry = cmds.duplicate(joint, n=joint + 'Y', po=1)[0]
	rz = cmds.duplicate(joint, n=joint + 'Z', po=1)[0]

	attrs = cmds.listAttr(joint, ud=1)
	if attrs:
		for r in [rx, ry, rz]:
			for a in attrs:
				if cmds.objExists(r + "." + a):
					cmds.deleteAttr(r + "." + a)

	# get rotation order for parenting
	ro = cmds.getAttr(joint + ".ro")

	order = [rx, ry, rz]
	if ro == 1:
		order = [ry, rz, rx]
	elif ro == 2:
		order = [rz, rx, ry]
	elif ro == 3:
		order = [rx, rz, ry]
	elif ro == 4:
		order = [ry, rx, rz]
	elif ro == 5:
		order = [rz, ry, rx]

	cmds.parent(order[0], order[1])
	cmds.parent(order[1], order[2])
	cmds.connectAttr(joint + ".rx", rx + ".rx")
	cmds.connectAttr(joint + ".ry", ry + ".ry")
	cmds.connectAttr(joint + ".rz", rz + ".rz")
	constraintslib.matrix_constraint(joint, order[-1], rotate=False, scale=False)

	return order
