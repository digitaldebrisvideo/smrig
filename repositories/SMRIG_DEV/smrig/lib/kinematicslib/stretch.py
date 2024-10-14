import logging

import maya.cmds as cmds

from smrig.lib import attributeslib
from smrig.lib import controlslib
from smrig.lib import rivetlib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.lib.kinematicslib.ik import soft_ik_chain_length_attribute, blend_attribute_name

log = logging.getLogger("smrig.lib.kinematicslib.stretch")


def create_nonuniform_stretch_nodes(curve, joints, mirror_value=1.0):
	"""
	Create non uniform stretch joints based riveted to a curve.

	:param curve:
	:param joints:
	:param mirror_value:
	:return:
	"""
	# rivet non uniform joints to surf
	jnt_parent = selectionlib.get_parent(joints[0])

	non_uniform_ik_nodes = [cmds.createNode("transform", p=j, n=j + "_nojnuniform_stretch_GRP") for j in joints]
	for i, node in enumerate(non_uniform_ik_nodes[1:], 1):
		cmds.parent(node, non_uniform_ik_nodes[i - 1])

	cmds.parent(non_uniform_ik_nodes[0], jnt_parent)

	rivets = rivetlib.create_curve_rivet(curve, non_uniform_ik_nodes)

	# create dummy aim constraints and reconnect them to the decompose matrix
	tmp = cmds.createNode("transform")
	for i, jnt in enumerate(non_uniform_ik_nodes[:-1]):
		aim_rivet = rivets[i + 1]
		aim = cmds.aimConstraint(tmp, jnt, aim=[mirror_value, 0, 0])[0]

		cmds.connectAttr("{}.position".format(aim_rivet), "{}.target[0].targetTranslate".format(aim), f=True)
		cmds.disconnectAttr("{}.rotatePivot".format(tmp), "{}.target[0].targetRotatePivot".format(aim))
		cmds.disconnectAttr("{}.rotatePivotTranslate".format(tmp), "{}.target[0].targetRotateTranslate".format(aim))
		cmds.disconnectAttr("{}.parentMatrix".format(tmp), "{}.target[0].targetParentMatrix".format(aim))

	cmds.delete(tmp)
	return non_uniform_ik_nodes


def create_ik_spline_stretch(curve,
                             joints,
                             control=None,
                             axis="tx",
                             world_scale_atrtibute=None,
                             default_stretch_value=1.0,
                             default_squash_value=1.0,
                             default_nonuniform_value=1.0,
                             non_uniform_joints=None):
	"""
	:param curve:
	:param joints:
	:param control:
	:param axis:
	:param world_scale_atrtibute:
	:param default_stretch_value:
	:param default_squash_value:
	:param default_nonuniform_value:
	:param non_uniform_joints:
	:return:
	"""
	curve_shape = selectionlib.get_shapes(curve)[0]
	arc_len = cmds.rename(cmds.arclen(curve_shape, ch=1), "{}_stretch_LEN".format(curve))

	mult = cmds.createNode("multiplyDivide", n="{}_stretch_MD".format(arc_len))
	cmds.setAttr(mult + ".operation", 2)

	cmds.connectAttr(arc_len + ".arcLength", mult + ".input1X")
	cmds.setAttr(mult + ".input2X", cmds.getAttr(arc_len + ".arcLength"))

	squash_mdl = None

	if world_scale_atrtibute:
		mdl = cmds.createNode("multDoubleLinear", n=mult + "_worldScale_MDL")
		cmds.connectAttr(world_scale_atrtibute, mdl + ".i1")
		cmds.setAttr(mdl + ".i2", cmds.getAttr(arc_len + ".arcLength"))
		cmds.connectAttr(mdl + ".o", mult + ".input2X")

	if control:
		cmds.addAttr(control, ln="stretch", min=0, max=1.0, dv=default_stretch_value, k=True)
		if non_uniform_joints:
			cmds.addAttr(control, ln="nonUniform", min=0, max=1.0, dv=default_nonuniform_value, k=True)
			squash_mdl = attributeslib.connection.multiply_connection(control + ".nonUniform", control + ".stretch")

		else:
			cmds.addAttr(control, ln="squash", min=0, max=1.0, dv=default_squash_value, k=True)

	for i, joint in enumerate(joints):
		mdl = cmds.createNode("multDoubleLinear", n=joint + "_stretch_MDL")
		cmds.setAttr("{}.i1".format(mdl), cmds.getAttr("{}.{}".format(joint, axis)))
		cmds.connectAttr(mult + ".outputX", mdl + ".i2")

		# if stretch is off then squash must be uniform
		if control:
			if non_uniform_joints:
				# first create a blender between uniform stretch (mdl) and non_uniform (nu_joint.tx)
				stretch_nonu_bta = attributeslib.connection.blend_connection(mdl + ".output",
				                                                             second_plug=non_uniform_joints[i] + ".tx",
				                                                             blender_plug=control + ".nonUniform")

				squash_nonu_bta = attributeslib.connection.blend_connection(mdl + ".output",
				                                                            second_plug=non_uniform_joints[i] + ".tx",
				                                                            blender_plug=squash_mdl)

				# then create the stretch (stretch_bt) no stretch (joint.tx) blender
				stretch_enable_bta = attributeslib.connection.blend_connection(
					first_value=cmds.getAttr("{}.{}".format(joint, axis)),
					second_plug=stretch_nonu_bta,
					blender_plug=control + ".stretch")

				# now create condtion for handling either squash or stretch
				cnd = cmds.createNode("condition")
				cmds.setAttr(cnd + ".operation", 3)
				cmds.setAttr(cnd + ".firstTerm", cmds.getAttr("{}.{}".format(joint, axis)))
				cmds.connectAttr(mdl + ".o", cnd + ".secondTerm")
				cmds.connectAttr(stretch_enable_bta, cnd + ".colorIfFalseR")
				cmds.connectAttr(squash_nonu_bta, cnd + ".colorIfTrueR")

				cmds.connectAttr(cnd + ".outColorR", "{}.{}".format(joint, axis), f=1)

			else:
				stretch_bta = attributeslib.connection.blend_connection(
					first_value=cmds.getAttr("{}.{}".format(joint, axis)),
					second_plug=mdl + ".o",
					blender_plug=control + ".stretch"
				)

				squash_bta = attributeslib.connection.blend_connection(
					first_value=cmds.getAttr("{}.{}".format(joint, axis)),
					second_plug=mdl + ".o",
					blender_plug=control + ".squash"
				)

				cnd = cmds.createNode("condition")
				cmds.setAttr(cnd + ".operation", 3)
				cmds.setAttr(cnd + ".firstTerm", cmds.getAttr("{}.{}".format(joint, axis)))
				cmds.connectAttr(mdl + ".o", cnd + ".secondTerm")
				cmds.connectAttr(stretch_bta, cnd + ".colorIfFalseR")
				cmds.connectAttr(squash_bta, cnd + ".colorIfTrueR")

				cmds.connectAttr(cnd + ".outColorR", "{}.{}".format(joint, axis), f=1)

		else:
			cmds.connectAttr(mdl + ".o", "{}.{}".format(joint, axis), f=1)


def biped_stretch(ik_ctrl,
                  pv_ctrl,
                  switch_ctrl,
                  fk_ctrls,
                  ik_joints,
                  ik_handles,
                  start_parent,
                  end_parent,
                  soft_ik_grp=None):
	"""
	Stretch setup for biped (2 joint chain) arms and legs.

	:param ik_ctrl:
	:param pv_ctrl:
	:param switch_ctrl:
	:param fk_ctrls:
	:param ik_joints:
	:param ik_handles:
	:param start_parent:
	:param end_parent:
	:param soft_ik_grp:
	:return:
	"""
	# add all my attrs on ctrls
	cmds.addAttr(ik_ctrl, ln="autoStretch", at="double", min=0, max=1, k=1)
	cmds.addAttr(ik_ctrl, ln="upperJointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(ik_ctrl, ln="lowerJointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(ik_ctrl, ln="shiftJointsLengths", at="double", min=-1, max=1, k=1)
	cmds.addAttr(ik_ctrl, ln="pin", at="double", min=0, max=1, k=1)
	cmds.addAttr(fk_ctrls[0], ln="jointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(fk_ctrls[1], ln="jointLength", at="double", dv=1, min=0.001, k=1)

	# store initial length of joint
	lo_init_length = cmds.getAttr(ik_joints[1] + ".tx")
	wrist_init_length = cmds.getAttr(ik_joints[2] + ".tx")
	max_init_length = lo_init_length + wrist_init_length

	# create nodes for distance
	start_grp = cmds.createNode("transform", n=ik_joints[0] + "_stretch_pos_GRP", p=start_parent)
	end_grp = cmds.createNode("transform", n=ik_joints[-1] + "_stretch_pos_GRP", p=end_parent)

	transformslib.xform.match(ik_joints[0], start_grp, rotate=False, scale=False)
	transformslib.xform.match(ik_joints[-1], end_grp, rotate=False, scale=False)

	# Create distance nodes between base, end, and pv ctrl to get the length of side of the triangle
	root_to_end_dist = utilslib.distance.create_reader(start_grp, end_grp, stretch=True,
	                                                   chain_length=abs(max_init_length))
	root_to_pv_dist = utilslib.distance.create_reader(start_grp, pv_ctrl, stretch=True)
	pv_to_end_dist = utilslib.distance.create_reader(pv_ctrl, end_grp, stretch=True)

	# easy stuff first - create fk stretch nodes
	lo_arm_fk_mdl = cmds.createNode("multDoubleLinear")
	wrist_fk_mdl = cmds.createNode("multDoubleLinear")

	cmds.setAttr(lo_arm_fk_mdl + ".input1", cmds.getAttr(ik_joints[1] + ".tx"))
	cmds.setAttr(wrist_fk_mdl + ".input1", cmds.getAttr(ik_joints[2] + ".tx"))
	cmds.connectAttr(fk_ctrls[0] + ".jointLength", lo_arm_fk_mdl + ".input2")
	cmds.connectAttr(fk_ctrls[1] + ".jointLength", wrist_fk_mdl + ".input2")

	fk_ctrls = [controlslib.Control(c) for c in fk_ctrls]
	attributeslib.connection.abs_connection(lo_arm_fk_mdl + ".output", fk_ctrls[1].groups[-1] + ".tx")
	if fk_ctrls[2] and cmds.objExists(fk_ctrls[2]):
		attributeslib.connection.abs_connection(wrist_fk_mdl + ".output", fk_ctrls[2].groups[-1] + ".tx")

	# These arethe final fk stretch outputs to connect to joints
	fk_stretch_final_output = [lo_arm_fk_mdl + ".output", wrist_fk_mdl + ".output"]

	# NOW creates node s for thew elbow pin
	lo_arm_pin_mdl = cmds.createNode("multDoubleLinear")
	wrist_pin_mdl = cmds.createNode("multDoubleLinear")

	cmds.setAttr(lo_arm_pin_mdl + ".input1", 1)
	cmds.setAttr(wrist_pin_mdl + ".input1", 1)

	if lo_init_length < 0.0:
		cmds.setAttr(lo_arm_pin_mdl + ".input1", -1)

	if wrist_init_length < 0.0:
		cmds.setAttr(wrist_pin_mdl + ".input1", -1)

	cmds.connectAttr(root_to_pv_dist + ".localDistance", lo_arm_pin_mdl + ".input2")
	cmds.connectAttr(pv_to_end_dist + ".localDistance", wrist_pin_mdl + ".input2")

	# These arethe final elbow pin stretch outputs to connect to joints
	pin_final_output = [lo_arm_pin_mdl + ".output", wrist_pin_mdl + ".output"]

	# create shift nodes
	cmds.addAttr(ik_joints[1], ln="shiftLength", k=1)
	cmds.addAttr(ik_joints[2], ln="shiftLength", k=1)

	cmds.setDrivenKeyframe("{}.shiftLength".format(ik_joints[1]),
	                       cd="{}.{}".format(ik_ctrl, "shiftJointsLengths"),
	                       dv=0,
	                       v=lo_init_length,
	                       itt="linear",
	                       ott="linear")

	cmds.setDrivenKeyframe("{}.shiftLength".format(ik_joints[1]),
	                       cd="{}.{}".format(ik_ctrl, "shiftJointsLengths"),
	                       dv=1, v=0,
	                       itt="linear",
	                       ott="linear")

	cmds.setDrivenKeyframe("{}.shiftLength".format(ik_joints[1]),
	                       cd="{}.{}".format(ik_ctrl, "shiftJointsLengths"),
	                       dv=-1,
	                       v=max_init_length,
	                       itt="linear",
	                       ott="linear")

	cmds.setDrivenKeyframe("{}.shiftLength".format(ik_joints[2]),
	                       cd="{}.{}".format(ik_ctrl, "shiftJointsLengths"),
	                       dv=0,
	                       v=wrist_init_length,
	                       itt="linear",
	                       ott="linear")

	cmds.setDrivenKeyframe("{}.shiftLength".format(ik_joints[2]),
	                       cd="{}.{}".format(ik_ctrl, "shiftJointsLengths"),
	                       dv=1,
	                       v=max_init_length,
	                       itt="linear",
	                       ott="linear")

	cmds.setDrivenKeyframe("{}.shiftLength".format(ik_joints[2]),
	                       cd="{}.{}".format(ik_ctrl, "shiftJointsLengths"),
	                       dv=-1,
	                       v=0,
	                       itt="linear",
	                       ott="linear")

	shift_final_output = ["{}.shiftLength".format(ik_joints[1]), "{}.shiftLength".format(ik_joints[2])]

	# Create ik indivisual stretch nodes
	lo_arm_ik_scale_mdl = cmds.createNode("multDoubleLinear")
	wrist_ik_scale_mdl = cmds.createNode("multDoubleLinear")

	cmds.connectAttr(shift_final_output[0], lo_arm_ik_scale_mdl + ".input1")
	cmds.connectAttr(shift_final_output[1], wrist_ik_scale_mdl + ".input1")
	cmds.connectAttr(ik_ctrl + ".upperJointLength", lo_arm_ik_scale_mdl + ".input2")
	cmds.connectAttr(ik_ctrl + ".lowerJointLength", wrist_ik_scale_mdl + ".input2")

	# This is the final output for scale and shift
	ik_stretch_final_output = [lo_arm_ik_scale_mdl + ".output", wrist_ik_scale_mdl + ".output"]

	# Now create the IK auto stretch nodes
	lo_auto_stretch_mdl = cmds.createNode("multDoubleLinear")
	wrist_auto_stretch_mdl = cmds.createNode("multDoubleLinear")

	auto_stretch_clamp = cmds.createNode("clamp")
	cmds.setAttr(auto_stretch_clamp + ".minR", 1)
	cmds.setAttr(auto_stretch_clamp + ".maxR", 10000000)

	cmds.connectAttr(ik_stretch_final_output[0], lo_auto_stretch_mdl + ".input1", f=1)
	cmds.connectAttr(ik_stretch_final_output[1], wrist_auto_stretch_mdl + ".input1", f=1)
	cmds.connectAttr(root_to_end_dist + ".stretchFactor", auto_stretch_clamp + ".inputR")

	cmds.connectAttr(auto_stretch_clamp + ".outputR", lo_auto_stretch_mdl + ".input2", f=1)
	cmds.connectAttr(auto_stretch_clamp + ".outputR", wrist_auto_stretch_mdl + ".input2", f=1)

	adl = cmds.createNode("addDoubleLinear")
	cmds.connectAttr(lo_arm_ik_scale_mdl + ".output", adl + ".input1")
	cmds.connectAttr(wrist_ik_scale_mdl + ".output", adl + ".input2")
	attributeslib.connection.abs_connection(adl + ".output", root_to_end_dist + ".jointChainLength")

	# handle soft ik handle constraint override
	if soft_ik_grp and cmds.objExists("{}.{}".format(soft_ik_grp, soft_ik_chain_length_attribute)):
		attributeslib.connection.abs_connection(adl + ".output",
		                                        "{}.{}".format(soft_ik_grp, soft_ik_chain_length_attribute))

		# blend off the soft ik constraint IF im in auto s tretch or pin mode
		mdl = cmds.createNode("multDoubleLinear")
		attributeslib.connection.reverse_connection(ik_ctrl + ".pin", mdl + ".input1")
		attributeslib.connection.reverse_connection(ik_ctrl + ".autoStretch", mdl + ".input2")

		current_parent = selectionlib.get_parent(ik_handles[0])
		parent_grp = selectionlib.get_parent(soft_ik_grp)
		prcs = [cmds.parentConstraint(current_parent, parent_grp, ik, mo=True)[0] for ik in ik_handles]

		for prc in prcs:
			cmds.connectAttr(mdl + ".output", prc + ".w0")
			attributeslib.connection.reverse_connection(prc + ".w0", prc + ".w1")

	ik_auto_stretch_final_output = [lo_auto_stretch_mdl + ".output", wrist_auto_stretch_mdl + ".output"]

	# first blend btween FK and an empty ik input
	fk_to_ik_blend = cmds.createNode("blendColors")
	cmds.connectAttr(switch_ctrl + "." + blend_attribute_name, fk_to_ik_blend + ".blender")
	cmds.connectAttr(fk_stretch_final_output[0], fk_to_ik_blend + ".color2R")
	cmds.connectAttr(fk_stretch_final_output[1], fk_to_ik_blend + ".color2G")

	# now create a blender between pin elbow  and the rest of the ik options
	auto_ik_blend = cmds.createNode("blendColors")
	cmds.connectAttr(ik_ctrl + ".autoStretch", auto_ik_blend + ".blender")
	cmds.connectAttr(ik_auto_stretch_final_output[0], auto_ik_blend + ".color1R")
	cmds.connectAttr(ik_auto_stretch_final_output[1], auto_ik_blend + ".color1G")

	# Now connect it toth fk blend
	cmds.connectAttr(auto_ik_blend + ".outputR", fk_to_ik_blend + ".color1R")
	cmds.connectAttr(auto_ik_blend + ".outputG", fk_to_ik_blend + ".color1G")

	# now create a blender between pin elbow  and the rest of the ik options
	pin_ik_blend = cmds.createNode("blendColors")
	cmds.connectAttr(ik_ctrl + ".pin", pin_ik_blend + ".blender")
	cmds.connectAttr(pin_final_output[0], pin_ik_blend + ".color1R")
	cmds.connectAttr(pin_final_output[1], pin_ik_blend + ".color1G")

	# Now connect it toth fk blend
	cmds.connectAttr(pin_ik_blend + ".outputR", auto_ik_blend + ".color2R")
	cmds.connectAttr(pin_ik_blend + ".outputG", auto_ik_blend + ".color2G")

	# now connect the shift and scale
	cmds.connectAttr(ik_stretch_final_output[0], pin_ik_blend + ".color2R")
	cmds.connectAttr(ik_stretch_final_output[1], pin_ik_blend + ".color2G")

	# now for the magic! Connect the blend networll to joints
	cmds.connectAttr(fk_to_ik_blend + ".outputR", ik_joints[1] + ".tx")
	cmds.connectAttr(fk_to_ik_blend + ".outputG", ik_joints[2] + ".tx")


def quadruped_stretch(ik_ctrl,
                      switch_ctrl,
                      fk_ctrls,
                      ik_joints,
                      ik_handles,
                      start_parent,
                      end_parent,
                      soft_ik_grp=None):
	"""
	Stretch setup for biped (2 joint chain) arms and legs.

	:param ik_ctrl:
	:param pv_ctrl:
	:param switch_ctrl:
	:param fk_ctrls:
	:param ik_joints:
	:param ik_handles:
	:param start_parent:
	:param end_parent:
	:param soft_ik_grp:
	:return:
	"""
	# add all my attrs on ctrls
	cmds.addAttr(ik_ctrl, ln="autoStretch", at="double", min=0, max=1, k=1)
	cmds.addAttr(ik_ctrl, ln="upperJointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(ik_ctrl, ln="middleJointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(ik_ctrl, ln="lowerJointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(fk_ctrls[0], ln="jointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(fk_ctrls[1], ln="jointLength", at="double", dv=1, min=0.001, k=1)
	cmds.addAttr(fk_ctrls[2], ln="jointLength", at="double", dv=1, min=0.001, k=1)

	# store initial length of joint
	mid_init_length = cmds.getAttr(ik_joints[1] + ".tx")
	lo_init_length = cmds.getAttr(ik_joints[2] + ".tx")
	wrist_init_length = cmds.getAttr(ik_joints[3] + ".tx")
	max_init_length = mid_init_length + lo_init_length + wrist_init_length

	# create nodes for distance
	start_grp = cmds.createNode("transform", n=ik_joints[0] + "_stretch_pos_GRP", p=start_parent)
	end_grp = cmds.createNode("transform", n=ik_joints[-1] + "_stretch_pos_GRP", p=end_parent)

	transformslib.xform.match(ik_joints[0], start_grp, rotate=False, scale=False)
	transformslib.xform.match(ik_joints[-1], end_grp, rotate=False, scale=False)

	# Create distance nodes between base, end, and pv ctrl to get the length of side of the triangle
	root_to_end_dist = utilslib.distance.create_reader(start_grp,
	                                                   end_grp,
	                                                   stretch=True,
	                                                   chain_length=abs(max_init_length))

	# easy stuff first - create fk stretch nodes
	mid_arm_fk_mdl = cmds.createNode("multDoubleLinear")
	lo_arm_fk_mdl = cmds.createNode("multDoubleLinear")
	wrist_fk_mdl = cmds.createNode("multDoubleLinear")

	cmds.setAttr(mid_arm_fk_mdl + ".input1", cmds.getAttr(ik_joints[1] + ".tx"))
	cmds.setAttr(lo_arm_fk_mdl + ".input1", cmds.getAttr(ik_joints[2] + ".tx"))
	cmds.setAttr(wrist_fk_mdl + ".input1", cmds.getAttr(ik_joints[3] + ".tx"))

	cmds.connectAttr(fk_ctrls[0] + ".jointLength", mid_arm_fk_mdl + ".input2")
	cmds.connectAttr(fk_ctrls[1] + ".jointLength", lo_arm_fk_mdl + ".input2")
	cmds.connectAttr(fk_ctrls[2] + ".jointLength", wrist_fk_mdl + ".input2")

	fk_ctrls = [controlslib.Control(c) for c in fk_ctrls]
	attributeslib.connection.abs_connection(mid_arm_fk_mdl + ".output", fk_ctrls[1].groups[-1] + ".tx")
	attributeslib.connection.abs_connection(lo_arm_fk_mdl + ".output", fk_ctrls[2].groups[-1] + ".tx")
	attributeslib.connection.abs_connection(wrist_fk_mdl + ".output", fk_ctrls[3].groups[-1] + ".tx")

	# These arethe final fk stretch outputs to connect to joints
	fk_stretch_final_output = [mid_arm_fk_mdl + ".output", lo_arm_fk_mdl + ".output", wrist_fk_mdl + ".output"]

	# Create ik individual stretch nodes
	mid_arm_ik_mdl = cmds.createNode("multDoubleLinear")
	lo_arm_ik_mdl = cmds.createNode("multDoubleLinear")
	wrist_ik_mdl = cmds.createNode("multDoubleLinear")

	cmds.setAttr(mid_arm_ik_mdl + ".input1", cmds.getAttr(ik_joints[1] + ".tx"))
	cmds.setAttr(lo_arm_ik_mdl + ".input1", cmds.getAttr(ik_joints[2] + ".tx"))
	cmds.setAttr(wrist_ik_mdl + ".input1", cmds.getAttr(ik_joints[3] + ".tx"))

	cmds.connectAttr(ik_ctrl + ".upperJointLength", mid_arm_ik_mdl + ".input2")
	cmds.connectAttr(ik_ctrl + ".middleJointLength", lo_arm_ik_mdl + ".input2")
	cmds.connectAttr(ik_ctrl + ".lowerJointLength", wrist_ik_mdl + ".input2")

	# These arethe final ik stretch outputs to connect to joints
	ik_stretch_final_output = [mid_arm_ik_mdl + ".output", lo_arm_ik_mdl + ".output", wrist_ik_mdl + ".output"]

	# Now create the IK auto stretch nodes
	mid_auto_stretch_mdl = cmds.createNode("multDoubleLinear")
	lo_auto_stretch_mdl = cmds.createNode("multDoubleLinear")
	wrist_auto_stretch_mdl = cmds.createNode("multDoubleLinear")

	auto_stretch_clamp = cmds.createNode("clamp")
	cmds.setAttr(auto_stretch_clamp + ".minR", 1)
	cmds.setAttr(auto_stretch_clamp + ".maxR", 10000000)

	cmds.connectAttr(ik_stretch_final_output[0], mid_auto_stretch_mdl + ".input1", f=1)
	cmds.connectAttr(ik_stretch_final_output[1], lo_auto_stretch_mdl + ".input1", f=1)
	cmds.connectAttr(ik_stretch_final_output[2], wrist_auto_stretch_mdl + ".input1", f=1)
	cmds.connectAttr(root_to_end_dist + ".stretchFactor", auto_stretch_clamp + ".inputR")

	cmds.connectAttr(auto_stretch_clamp + ".outputR", mid_auto_stretch_mdl + ".input2", f=1)
	cmds.connectAttr(auto_stretch_clamp + ".outputR", lo_auto_stretch_mdl + ".input2", f=1)
	cmds.connectAttr(auto_stretch_clamp + ".outputR", wrist_auto_stretch_mdl + ".input2", f=1)

	pma = cmds.createNode("plusMinusAverage")
	cmds.connectAttr(ik_stretch_final_output[0], pma + ".input1D[0]")
	cmds.connectAttr(ik_stretch_final_output[1], pma + ".input1D[1]")
	cmds.connectAttr(ik_stretch_final_output[2], pma + ".input1D[2]")
	attributeslib.connection.abs_connection(pma + ".output1D", root_to_end_dist + ".jointChainLength")

	# handle soft ik handle constraint override
	if soft_ik_grp and cmds.objExists("{}.{}".format(soft_ik_grp, soft_ik_chain_length_attribute)):
		attributeslib.connection.abs_connection(pma + ".output1D",
		                                        "{}.{}".format(soft_ik_grp, soft_ik_chain_length_attribute))

		current_parent = selectionlib.get_parent(ik_handles[0])
		parent_grp = selectionlib.get_parent(soft_ik_grp)
		prcs = [cmds.parentConstraint(current_parent, parent_grp, ik, mo=True)[0] for ik in ik_handles]

		for prc in prcs:
			cmds.connectAttr(ik_ctrl + ".autoStretch", prc + ".w1", f=1)
			attributeslib.connection.reverse_connection(prc + ".w1", prc + ".w0")

	ik_auto_stretch_final_output = [mid_auto_stretch_mdl + ".output",
	                                lo_auto_stretch_mdl + ".output",
	                                wrist_auto_stretch_mdl + ".output"]

	# create blender between auto stretch and ik stretch
	auto_ik_blend = cmds.createNode("blendColors")
	cmds.connectAttr(ik_ctrl + ".autoStretch", auto_ik_blend + ".blender")
	cmds.connectAttr(ik_auto_stretch_final_output[0], auto_ik_blend + ".color1R")
	cmds.connectAttr(ik_auto_stretch_final_output[1], auto_ik_blend + ".color1G")
	cmds.connectAttr(ik_auto_stretch_final_output[2], auto_ik_blend + ".color1B")

	cmds.connectAttr(ik_stretch_final_output[0], auto_ik_blend + ".color2R")
	cmds.connectAttr(ik_stretch_final_output[1], auto_ik_blend + ".color2G")
	cmds.connectAttr(ik_stretch_final_output[2], auto_ik_blend + ".color2B")

	# now create a blender between IK to FK
	fk_to_ik_blend = cmds.createNode("blendColors")
	cmds.connectAttr(switch_ctrl + "." + blend_attribute_name, fk_to_ik_blend + ".blender")

	cmds.connectAttr(auto_ik_blend + ".outputR", fk_to_ik_blend + ".color1R")
	cmds.connectAttr(auto_ik_blend + ".outputG", fk_to_ik_blend + ".color1G")
	cmds.connectAttr(auto_ik_blend + ".outputB", fk_to_ik_blend + ".color1B")

	cmds.connectAttr(fk_stretch_final_output[0], fk_to_ik_blend + ".color2R")
	cmds.connectAttr(fk_stretch_final_output[1], fk_to_ik_blend + ".color2G")
	cmds.connectAttr(fk_stretch_final_output[2], fk_to_ik_blend + ".color2B")

	# now connect fk ik blender to joints
	cmds.connectAttr(fk_to_ik_blend + ".outputR", ik_joints[1] + ".tx", f=1)
	cmds.connectAttr(fk_to_ik_blend + ".outputG", ik_joints[2] + ".tx", f=1)
	cmds.connectAttr(fk_to_ik_blend + ".outputB", ik_joints[3] + ".tx", f=1)
