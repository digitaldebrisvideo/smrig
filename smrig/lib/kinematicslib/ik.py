import logging

import maya.cmds as cmds
import maya.mel as mel

from smrig.lib import constraintslib
from smrig.lib import nodepathlib
from smrig.lib import transformslib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.kinematicslib.ik")

IK_SOLVERS = ["RP", "SC", "Spring"]
blend_attribute_name = "ikBlend"
visibility_attribute_name = "fkIkControlVis"
soft_ik_chain_length_attribute = "softIkChainLength"

mel.eval("ikSpringSolver")


def get_joint_chain_from_ik_handle(ik_handle, full_path=True):
	"""
	Get the joint chain that is driven by the ik handle. The joint chain is
	in order from start to end and by default contains the full path to the
	nodes.

	:param str ik_handle:
	:param bool full_path:
	:return: Joint chain
	:rtype: list
	"""
	# get start and end joint
	start_joint = cmds.ikHandle(ik_handle, query=True, startJoint=True)
	end_effector = cmds.ikHandle(ik_handle, query=True, endEffector=True)
	end_joint = cmds.listConnections(end_effector, type="joint", source=True, destination=False)[0]
	end_joint = nodepathlib.get_long_name(end_joint)

	# get entire joint chain
	chain = cmds.listRelatives(start_joint, type="joint", allDescendents=True, fullPath=True)
	chain.reverse()
	chain.insert(0, start_joint)

	# get end joint index
	end_joint_index = chain.index(end_joint)
	return cmds.ls(chain[:end_joint_index + 1], l=full_path)


def create_ik_handle(start_joint, end_joint, solver="RP"):
	"""
	A wrapped function for creating an ik handle of types, "RP" and "SC".
	The function will name the end effector and ik handle automatically using
	the end joint name.

	:param str start_joint:
	:param str end_joint:
	:param str solver: Which solver to use - "RP", "SC", "Spring"
	:return: IK handle
	:rtype: str
	"""
	# get solver
	solver = solver.capitalize() if solver.lower() == "spring" else solver.upper()

	# validate solver
	if solver not in IK_SOLVERS:
		error_message = "Provided solver name '{}' is not a valid mixin, options are: {}".format(solver, IK_SOLVERS)
		log.error(error_message)
		raise ValueError(error_message)

	# create ik handle
	solver_type = "ikSpringSolver" if solver == "Spring" else "ik{}solver".format(solver)
	ik_handle, end_effector = cmds.ikHandle(startJoint=start_joint, endEffector=end_joint, solver=solver_type,
	                                        s="sticky")

	# rename nodes
	end_joint_name = nodepathlib.get_leaf_name(end_joint)
	ik_handle = cmds.rename(ik_handle, "{}_IKH".format(end_joint_name))
	cmds.rename(end_effector, "{}_EFF".format(end_joint_name))

	return ik_handle


def align_ik_twist(target_joint, ik_joint, ik_handle, tolerance=0.001):
	"""

	:param target_joint:
	:param ik_joint:
	:param ik_handle:
	:param tolerance:
	:return:
	"""

	# first figure out the direction we need to go.
	start_dist = utilslib.distance.get(target_joint, ik_joint)

	if start_dist < tolerance:
		return 0.0

	cmds.setAttr(ik_handle + ".twist", 10 + cmds.getAttr(ik_handle + ".twist"))
	mult = 1.0 if utilslib.distance.get(target_joint, ik_joint) < start_dist else -1.0

	lowest_distance = utilslib.distance.get(target_joint, ik_joint) * 2.0
	value = 0.0

	while utilslib.distance.get(target_joint, ik_joint) > tolerance:
		cmds.setAttr(ik_handle + ".twist", cmds.getAttr(ik_handle + ".twist") + (0.05 * mult))
		dist = utilslib.distance.get(target_joint, ik_joint)

		if dist > lowest_distance:
			break

		lowest_distance = dist
		value = cmds.getAttr(ik_handle + ".twist")

	cmds.setAttr(ik_handle + ".twist", value)
	return value


def create_spline_ik_handle(start_joint, end_joint, curve=None, spans=3):
	"""
	Create a spline ik handle using the start and end joints. It is possible
	to provide a pre-made curve. If no curve is provided one will be created
	using the provided spans. The IK handle, end effector and curve will be
	automatically (re)named, even if a curve is provided.

	:param str start_joint:
	:param str end_joint:
	:param str/None curve:
	:param int spans:
	:return: Ik handle and curve
	:raise: tuple
	"""
	# variables
	solver_arguments = {}
	solver_type = "ikSplineSolver"

	# determine solver keyword arguments
	if curve:
		solver_arguments["curve"] = curve
		solver_arguments["createCurve"] = False
	else:
		solver_arguments["createCurve"] = True
		solver_arguments["simplifyCurve"] = True
		solver_arguments["rootOnCurve"] = True
		solver_arguments["numSpans"] = spans

	# create ik handle
	ik_data = cmds.ikHandle(
		startJoint=start_joint,
		endEffector=end_joint,
		solver=solver_type,
		**solver_arguments
	)

	# unpack ik dataexporter
	ik_handle, end_effector = ik_data[:2]
	curve = curve if curve else ik_data[2]

	# rename nodes
	end_joint_name = nodepathlib.get_leaf_name(end_joint)
	ik_handle = cmds.rename(ik_handle, "{}_IKH".format(end_joint_name))
	curve = cmds.rename(curve, "{}_CRV".format(ik_handle))
	cmds.rename(end_effector, "{}_EFF".format(end_joint_name))

	return ik_handle, curve


def create_advanced_twist_locators(ik_handle, axis="y", match_start_orientation=False, local_scale=0.25):
	"""
	Creates and connects two locators that are used in the advanced twist
	section of an ik solver. The locators as positioned at the start and
	end joints of the chain but contain an offset in the direction of the
	provided axis.

	:param str ik_handle:
	:param str axis: "x", "y" or "z"
	:param int/float offset:
	:param bool match_start_orientation:
	:param int/float local_scale:
	:return: Start and end twist locators
	:rtype: list
	"""
	# get chain
	chain = get_joint_chain_from_ik_handle(ik_handle)
	start_joint = chain[0]
	end_joint = chain[-1]

	# get names
	# TODO: handle names better
	start_name = "{}_twistUpStart_LOC".format(nodepathlib.get_leaf_name(start_joint).rsplit("_", 1)[0])
	end_name = "{}_twistUpEnd_LOC".format(nodepathlib.get_leaf_name(end_joint).rsplit("_", 1)[0])

	# create locators
	start_loc = cmds.createNode("transform", n=start_name, p=start_joint)
	end_loc = cmds.createNode("transform", n=end_name, p=end_joint)
	cmds.parent(start_loc, end_loc, w=True)

	# attach locators to the ik handle
	cmds.setAttr("{}.dTwistControlEnable".format(ik_handle), True)
	cmds.setAttr("{}.dWorldUpType".format(ik_handle), 4)

	cmds.connectAttr("{}.worldMatrix[0]".format(start_loc), "{}.dWorldUpMatrix".format(ik_handle))
	cmds.connectAttr("{}.worldMatrix[0]".format(end_loc), "{}.dWorldUpMatrixEnd".format(ik_handle))
	return [start_loc, end_loc]


def create_fk_ik_switch(control, ik_handles, fk_controls, ik_controls):
	"""
	Create an IK attribute on the given ctrl, connect IK handles to ik switch.
	Also connect fk ctrls and ik ctrls visibility to switch.

	This will create an "IK" attr on the switch ctrl
	will create a "fkIkCtrlVis" on the switch ctrl as an enum to display "auto:fkOnly:ikOnly:both"

	:param control:
	:param ik_handles:
	:param fk_controls:
	:param ik_controls:
	:return:
	"""
	fk_controls = cmds.ls(fk_controls)
	ik_controls = cmds.ls(ik_controls)
	ik_handles = cmds.ls(ik_handles)

	# Create attributes
	if not cmds.objExists(control + "." + blend_attribute_name):
		cmds.addAttr(control, ln=blend_attribute_name, min=0, max=1, dv=1, k=1)

	if not cmds.objExists(control + "." + visibility_attribute_name):
		cmds.addAttr(control, ln=visibility_attribute_name, at="enum", en="auto:fk controls:ik controls:all controls",
		             k=1)

	# Connect ik handles
	for handle in ik_handles:
		cmds.connectAttr(control + "." + blend_attribute_name, handle + ".ikBlend")

	# Create switch for ik ctrl
	ik_choice = cmds.createNode("choice", name=visibility_attribute_name + "_ik_CH")
	cmds.connectAttr(control + "." + visibility_attribute_name, ik_choice + ".selector")
	cmds.connectAttr(control + "." + blend_attribute_name, ik_choice + ".input[0]")
	cmds.setAttr(ik_choice + ".input[1]", 0)
	cmds.setAttr(ik_choice + ".input[2]", 1)
	cmds.setAttr(ik_choice + ".input[3]", 1)

	for ctrl in ik_controls:
		cmds.setAttr(ctrl + ".v", l=0)
		cmds.connectAttr(ik_choice + ".output", ctrl + ".v", f=1)
		cmds.setAttr(ctrl + ".v", l=1)

	# Create swicth for ik ctrl
	fk_choice = cmds.createNode("choice", name=visibility_attribute_name + "_fk_CH")
	fk_rv = cmds.createNode("reverse", name=visibility_attribute_name + "_fk_REV")
	cmds.connectAttr(control + "." + blend_attribute_name, fk_rv + ".inputX")
	cmds.connectAttr(control + "." + visibility_attribute_name, fk_choice + ".selector")
	cmds.connectAttr(fk_rv + ".outputX", fk_choice + ".input[0]")
	cmds.setAttr(fk_choice + ".input[1]", 1)
	cmds.setAttr(fk_choice + ".input[2]", 0)
	cmds.setAttr(fk_choice + ".input[3]", 1)

	for ctrl in fk_controls:
		cmds.setAttr(ctrl + ".v", l=0)
		cmds.connectAttr(fk_choice + ".output", ctrl + ".v", f=1)
		cmds.setAttr(ctrl + ".v", l=1)


def create_soft_ik(ik_control, ik_joints, ik_handles, start_parent, end_parent):
	"""
	Create soft ik constraint on ikHandle.

	:param ik_control:
	:param ik_joints:
	:param ik_handles:
	:param start_parent:
	:param end_parent:
	:return:
	"""
	base_name = ik_control + "_soft"

	chain_length = 0.0
	for jnt in ik_joints[1:]:
		chain_length += abs(cmds.getAttr(jnt + ".tx"))

	# create dist node, (distance between top ik_joint and ik_handle) = X
	soft_ik_start_offset_grp = cmds.createNode("transform", name=base_name + "_start_offset_GRP")
	soft_ik_end_offset_grp = cmds.createNode("transform", name=base_name + "_end_offset_GRP")

	soft_ik_start_grp = cmds.createNode("transform", name=base_name + "_start_GRP", p=soft_ik_start_offset_grp)
	soft_ik_end_grp = cmds.createNode("transform", name=base_name + "_end_GRP", p=soft_ik_end_offset_grp)

	grp = cmds.createNode("transform", n=base_name + "_aim_GRP", p=soft_ik_end_offset_grp)
	soft_ik_grp = cmds.createNode("transform", n=base_name + "_GRP", p=grp)

	transformslib.xform.match(ik_joints[0], soft_ik_start_offset_grp)
	transformslib.xform.match(ik_joints[-1], soft_ik_end_offset_grp)
	cmds.parent(soft_ik_start_offset_grp, start_parent)
	cmds.parent(soft_ik_end_offset_grp, end_parent)

	# create the dSoft and softIK attributes on the controller
	dist = utilslib.distance.create_reader(soft_ik_start_grp, soft_ik_end_grp)

	cmds.addAttr(ik_control, ln="softIK", min=0, k=1)
	ctrl_clamp = cmds.createNode("clamp")
	cmds.connectAttr(ik_control + ".softIK", ctrl_clamp + ".inputR")
	cmds.setAttr(ctrl_clamp + ".minR", 0.0001)
	cmds.setAttr(ctrl_clamp + ".maxR", 10000000)

	# create node network for soft IK
	da_pma = cmds.createNode("plusMinusAverage", n=base_name + "_da_pma")
	x_minus_da_pma = cmds.createNode("plusMinusAverage", n=base_name + "_x_minus_da_pma")
	negate_x_minus_md = cmds.createNode("multiplyDivide", n=base_name + "_negate_x_minus_md")
	div_by_dsoft_md = cmds.createNode("multiplyDivide", n=base_name + "_divBy_dSoft_md")
	pow_e_md = cmds.createNode("multiplyDivide", n=base_name + "_pow_e_md")
	one_minus_pow_e_pma = cmds.createNode("plusMinusAverage", n=base_name + "_one_minus_pow_e_pma")
	times_dsoft_md = cmds.createNode("multiplyDivide", n=base_name + "_times_dSoft_md")
	plus_da_pma = cmds.createNode("plusMinusAverage", n=base_name + "_plus_da_pma")
	da_cond = cmds.createNode("condition", n=base_name + "_da_cond")
	dist_diff_pma = cmds.createNode("plusMinusAverage", n=base_name + "_dist_diff_pma")
	default_pos_pma = cmds.createNode("plusMinusAverage", n=base_name + "_defaultPos_pma")

	# set operations
	cmds.setAttr(da_pma + ".operation", 2)
	cmds.setAttr(x_minus_da_pma + ".operation", 2)
	cmds.setAttr(negate_x_minus_md + ".operation", 1)
	cmds.setAttr(div_by_dsoft_md + ".operation", 2)
	cmds.setAttr(pow_e_md + ".operation", 3)
	cmds.setAttr(one_minus_pow_e_pma + ".operation", 2)
	cmds.setAttr(times_dsoft_md + ".operation", 1)
	cmds.setAttr(plus_da_pma + ".operation", 1)
	cmds.setAttr(da_cond + ".operation", 5)
	cmds.setAttr(dist_diff_pma + ".operation", 2)
	cmds.setAttr(default_pos_pma + ".operation", 2)

	# make connections
	cmds.addAttr(soft_ik_grp, ln=soft_ik_chain_length_attribute, k=1, dv=chain_length)
	cmds.connectAttr(soft_ik_grp + "." + soft_ik_chain_length_attribute, da_pma + ".input1D[0]")
	cmds.connectAttr(ctrl_clamp + ".outputR", da_pma + ".input1D[1]")

	cmds.connectAttr(dist + ".localDistance", x_minus_da_pma + ".input1D[0]")
	cmds.connectAttr(da_pma + ".output1D", x_minus_da_pma + ".input1D[1]")

	cmds.connectAttr(x_minus_da_pma + ".output1D", negate_x_minus_md + ".input1X")
	cmds.setAttr(negate_x_minus_md + ".input2X", -1)

	cmds.connectAttr(negate_x_minus_md + ".outputX", div_by_dsoft_md + ".input1X")
	cmds.connectAttr(ctrl_clamp + ".outputR", div_by_dsoft_md + ".input2X")

	cmds.setAttr(pow_e_md + ".input1X", 2.718281828)
	cmds.connectAttr(div_by_dsoft_md + ".outputX", pow_e_md + ".input2X")

	cmds.setAttr(one_minus_pow_e_pma + ".input1D[0]", 1)
	cmds.connectAttr(pow_e_md + ".outputX", one_minus_pow_e_pma + ".input1D[1]")

	cmds.connectAttr(one_minus_pow_e_pma + ".output1D", times_dsoft_md + ".input1X")
	cmds.connectAttr(ctrl_clamp + ".outputR", times_dsoft_md + ".input2X")

	cmds.connectAttr(times_dsoft_md + ".outputX", plus_da_pma + ".input1D[0]")
	cmds.connectAttr(da_pma + ".output1D", plus_da_pma + ".input1D[1]")

	cmds.connectAttr(da_pma + ".output1D", da_cond + ".firstTerm")
	cmds.connectAttr(dist + ".localDistance", da_cond + ".secondTerm")
	cmds.connectAttr(dist + ".localDistance", da_cond + ".colorIfFalseR")
	cmds.connectAttr(plus_da_pma + ".output1D", da_cond + ".colorIfTrueR")

	cmds.connectAttr(da_cond + ".outColorR", dist_diff_pma + ".input1D[0]")
	cmds.connectAttr(dist + ".localDistance", dist_diff_pma + ".input1D[1]")

	cmds.setAttr(default_pos_pma + ".input1D[0]", 0)
	cmds.connectAttr(dist_diff_pma + ".output1D", default_pos_pma + ".input1D[1]")

	# Create new ik aim node
	cmds.aimConstraint(soft_ik_start_grp,
	                   grp,
	                   aim=[0, 1, 0],
	                   u=[1, 0, 0],
	                   wu=[1, 0, 0],
	                   wut="objectRotation",
	                   wuo=ik_control,
	                   n=grp + "_ac")

	constraintslib.matrix_constraint(end_parent,
	                                 soft_ik_grp,
	                                 maintain_offset=True,
	                                 translate=False,
	                                 rotate=True,
	                                 scale=False)

	cmds.connectAttr(default_pos_pma + ".output1D", soft_ik_grp + ".ty")
	cmds.parent(ik_handles, soft_ik_grp)

	return soft_ik_grp
