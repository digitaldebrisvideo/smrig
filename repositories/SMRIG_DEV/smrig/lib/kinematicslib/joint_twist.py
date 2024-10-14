import logging

import maya.cmds as cmds

from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import transformslib

log = logging.getLogger("smrig.lib.kinematicslib.joint_twist")

AXIS = ["X", "Y", "Z"]
AXIS_ORDER = "XYZX"
AXIS_CROSS_ORDER = {True: [1, 2], False: [2, 1]}
TWIST_METHODS = ["axis", "quat"]


def upper_twist(parent, ik_joints, fk_twist_joints):
	"""
	Quaterion / matrix based twist for upper arms and legs.

	:param parent:
	:param ik_joints:
	:param fk_twist_joints:
	:return:
	"""
	base_name = ik_joints[0] + "twist"

	# Create a grp that will rotate with ik arm
	stable_reader_grp = cmds.createNode("transform", n=base_name + "_stable_GRP", p=ik_joints[0])
	twist_reader_grp = cmds.createNode("transform", n=base_name + "_reader_GRP", p=ik_joints[0])
	twist_driver_grp = cmds.createNode("transform", n=base_name + "_driver_GRP", p=twist_reader_grp)

	cmds.parent(stable_reader_grp, parent)
	cmds.addAttr(twist_reader_grp, ln="twist", k=1)

	# Now set up mult matrix and decomp nodes to extract the twist between the two nodes
	mult_mtx = cmds.createNode("multMatrix")
	decomp_mtx = cmds.createNode("decomposeMatrix")
	quat_to_euler = cmds.createNode("quatToEuler")

	cmds.connectAttr(stable_reader_grp + ".worldInverseMatrix", mult_mtx + ".matrixIn[1]")
	cmds.connectAttr(twist_reader_grp + ".worldMatrix", mult_mtx + ".matrixIn[0]")
	cmds.connectAttr(mult_mtx + ".matrixSum", decomp_mtx + ".inputMatrix")
	cmds.connectAttr(decomp_mtx + ".outputQuatX", quat_to_euler + ".inputQuatX")
	cmds.connectAttr(decomp_mtx + ".outputQuatW", quat_to_euler + ".inputQuatW")

	attributeslib.connection.negative_connection(quat_to_euler + ".outputRotateX", twist_reader_grp + ".twist")
	cmds.connectAttr(twist_reader_grp + ".twist", twist_driver_grp + ".rx")

	# Connect joints
	constraintslib.matrix_constraint(twist_driver_grp, fk_twist_joints[0], maintain_offset=True)

	div = 1.0 / (len(fk_twist_joints[1:]))
	mdl = cmds.createNode("multDoubleLinear")
	cmds.setAttr(mdl + ".input1", div)
	cmds.connectAttr(quat_to_euler + ".outputRotateX", mdl + ".input2")

	for i, joint in enumerate(fk_twist_joints[1:]):
		cmds.connectAttr(mdl + ".output", joint + ".rx")


def lower_twist(ik_joints, twist_joints):
	"""
	Quaterion / matrix based stretch for forearms and lower legs

	:param ik_joints:
	:param twist_joints:
	:return:
	"""
	base_name = ik_joints[0] + "_twist"
	stable_reader_grp = cmds.createNode("transform", n=base_name + "_stable_reader", p=ik_joints[0])
	twist_reader_grp = cmds.createNode("transform", n=base_name + "_twist_reader", p=ik_joints[1])
	transformslib.xform.match(ik_joints[0], twist_reader_grp, translate=False, rotate=True, scale=False)
	cmds.addAttr(twist_reader_grp, ln="twist", k=1)

	# Now set up mult matrix and decomp nodes to extract the twist between the two nodes
	mult_mtx = cmds.createNode("multMatrix")
	decomp_mtx = cmds.createNode("decomposeMatrix")
	quat_to_euler = cmds.createNode("quatToEuler")

	cmds.connectAttr(stable_reader_grp + ".worldInverseMatrix", mult_mtx + ".matrixIn[1]")
	cmds.connectAttr(twist_reader_grp + ".worldMatrix", mult_mtx + ".matrixIn[0]")
	cmds.connectAttr(mult_mtx + ".matrixSum", decomp_mtx + ".inputMatrix")
	cmds.connectAttr(decomp_mtx + ".outputQuatX", quat_to_euler + ".inputQuatX")
	cmds.connectAttr(decomp_mtx + ".outputQuatW", quat_to_euler + ".inputQuatW")

	attributeslib.connection.negative_connection(quat_to_euler + ".outputRotateX", twist_reader_grp + ".twist")

	# Connect joints
	constraintslib.matrix_constraint(ik_joints[0], twist_joints[0], maintain_offset=True)

	div = 1.0 / (len(twist_joints[1:]))
	mdl = cmds.createNode("multDoubleLinear")
	cmds.setAttr(mdl + ".input1", div)
	cmds.connectAttr(quat_to_euler + ".outputRotateX", mdl + ".input2")

	for i, joint in enumerate(twist_joints[1:]):
		cmds.connectAttr(mdl + ".output", joint + ".rx")
