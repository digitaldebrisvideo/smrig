# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig import partslib
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import kinematicslib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib.utilslib.scene import STASH_NAMESPACE
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.foot")


class Foot(basepart.Basepart):
	"""
	foot rig part module.
	"""

	BUILD_LAST = True

	def __init__(self, *guide_node, **options):
		super(Foot, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "L_ankle_JNT", value_required=True)
		self.register_option("parentPart",
		                     "rig_part",
		                     "L_bipedLeg_guide_GRP",
		                     value_required=True,
		                     part_types=["bipedLeg", "quadLimb"])

	@property
	def parent_part(self):
		return partslib.part("{}:{}".format(STASH_NAMESPACE, self.options.get("parentPart").get("value")))

	@property
	def leg_nodes(self):
		return self.parent_part.foot_part_required_nodes

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		ball_plc = self.create_placer("ball")
		toe_plc = self.create_placer("toe")

		heel_plc = self.create_placer("heel")
		inner_ball_plc = self.create_placer(["inner", "bal"])
		outter_ball_plc = self.create_placer(["outter", "ball"])

		ball_jnt = self.create_joint("ball", placer_driver=ball_plc, constraints="pointConstraint")
		toe_jnt = self.create_joint("toe", placer_driver=toe_plc, constraints="pointConstraint")

		constraintslib.aim_constraint_chain([ball_plc, toe_plc],
		                                    [ball_jnt, toe_jnt],
		                                    aim=[1, 0, 0],
		                                    up=[0, 1, 0],
		                                    wup=[-1, 0, 0],
		                                    mirror_value=self.mirror_value)

		cmds.parent(toe_jnt, ball_jnt)

		cmds.xform(toe_plc.groups[-1], a=1, t=[0, -1, 2])
		cmds.xform(ball_plc.groups[-1], a=1, t=[0, -1, 1])
		cmds.xform(heel_plc.groups[-1], a=1, t=[0, -1, -1])
		cmds.xform(inner_ball_plc.groups[-1], a=1, t=[-0.5, -1, 1])
		cmds.xform(outter_ball_plc.groups[-1], a=1, t=[0.5, -1, 1])

		self.create_control(["toe", "ik"],
		                    shape="square",
		                    axis="z",
		                    color=self.primary_color,
		                    driver=ball_plc)

		self.create_control(["toe", "fk"],
		                    shape="circle",
		                    axis="x",
		                    color=self.primary_color,
		                    driver=ball_jnt)

		self.create_control("heel",
		                    shape="cube",
		                    scale=0.25,
		                    axis="x",
		                    color=self.secondary_color,
		                    driver=heel_plc)

		self.create_control(["toe", "tip"],
		                    shape="cube",
		                    scale=0.25,
		                    axis="x",
		                    color=self.secondary_color,
		                    driver=toe_plc)

		self.create_control(["ball", "outter"],
		                    shape="cube",
		                    scale=0.25,
		                    axis="x",
		                    color=self.secondary_color,
		                    driver=outter_ball_plc)

		self.create_control(["ball", "inner"],
		                    shape="cube",
		                    scale=0.25,
		                    axis="x",
		                    color=self.secondary_color,
		                    driver=inner_ball_plc)

		self.create_control(["reverse", "ball"],
		                    shape="lollipop",
		                    scale=1,
		                    axis="y",
		                    color=self.secondary_color,
		                    driver=ball_plc)

	def build_rig(self):
		"""

		:return:
		"""
		ankle_ik_jnt, ankle_fk_jnt, leg_ik_ctrl, ankle_fk_ctrl, leg_settings_ctrl = self.leg_nodes

		leg_ik = ankle_ik_jnt + "_IKH"
		soft_ik_parent_grp = selectionlib.get_children(leg_ik_ctrl.last_node)

		ball_jnt = self.format_name("ball", node_type="joint")
		toe_jnt = self.format_name("toe", node_type="joint")

		# create ctrls
		ball_ik_ctrl = self.create_control_from_guide(self.format_name(["toe", "ik"],
		                                                               node_type="animControl"))

		ball_fk_ctrl = self.create_control_from_guide(self.format_name(["toe", "fk"],
		                                                               node_type="animControl"))

		heel_ctrl = self.create_control_from_guide(self.format_name("heel", node_type="animControl"),
		                                           animatable_pivot=True)

		toe_ctrl = self.create_control_from_guide(self.format_name(["toe", "tip"],
		                                                           node_type="animControl"), animatable_pivot=True)

		ball_inner_ctrl = self.create_control_from_guide(self.format_name(["ball", "inner"],
		                                                                  node_type="animControl"),
		                                                 animatable_pivot=True)

		ball_outter_ctrl = self.create_control_from_guide(self.format_name(["ball", "outter"],
		                                                                   node_type="animControl"),
		                                                  animatable_pivot=True)

		reverse_ball_ctrl = self.create_control_from_guide(self.format_name(["reverse", "ball"],
		                                                                    node_type="animControl"))

		# create attributes
		attributeslib.add_spacer_attribute(leg_ik_ctrl.path)
		cmds.addAttr(leg_ik_ctrl.path, ln="rollBias", k=1, min=-1, max=1, dv=0)
		cmds.addAttr(leg_ik_ctrl.path, ln="rollBallUnbend", k=1, min=0, max=1, dv=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="roll", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="sideRoll", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="toeTipPivot", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="ballPivot", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="heelPivot", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="heelLift", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="ballLift", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="toeTipLift", k=1)
		cmds.addAttr(leg_ik_ctrl.path, ln="toeLift", k=1)

		foot_parent_grp = self.create_node("transform", ["foot", "nodes"], p=leg_ik_ctrl.last_node)
		toe_tip_piv_grp = self.create_node("transform", ["toe", "tip", "piv"], p=foot_parent_grp)
		ball_piv_grp = self.create_node("transform", ["ball", "piv"], p=toe_tip_piv_grp)
		heel_piv_grp = self.create_node("transform", ["heel", "piv"], p=ball_piv_grp)
		inner_roll_grp = self.create_node("transform", ["inner", "roll"], p=heel_piv_grp)
		outter_roll_grp = self.create_node("transform", ["outter", "roll"], p=inner_roll_grp)

		transformslib.xform.match(toe_ctrl.path, foot_parent_grp)
		transformslib.xform.match(ball_fk_ctrl.path, ball_piv_grp, rotate=False)
		transformslib.xform.match(heel_ctrl.path, heel_piv_grp, rotate=False)
		transformslib.xform.match(ball_inner_ctrl.path, inner_roll_grp, rotate=False)
		transformslib.xform.match(ball_outter_ctrl.path, outter_roll_grp, rotate=False)

		cmds.parent(reverse_ball_ctrl.groups[-1], ball_ik_ctrl.groups[-1], ball_outter_ctrl.last_node)
		cmds.parent(ball_outter_ctrl.groups[-1], ball_inner_ctrl.last_node)
		cmds.parent(ball_inner_ctrl.groups[-1], toe_ctrl.last_node)
		cmds.parent(toe_ctrl.groups[-1], heel_ctrl.last_node)
		cmds.parent(heel_ctrl.groups[-1], outter_roll_grp)

		cmds.parent(ball_fk_ctrl.groups[-1], ankle_fk_ctrl.last_node)

		# constraint fk
		constraintslib.matrix_constraint(ball_fk_ctrl.last_node, ball_jnt, translate=False, maintain_offset=True)

		# parent ik handles
		ball_ik = kinematicslib.ik.create_ik_handle(ankle_fk_jnt, ball_jnt, solver="SC")
		toe_ik = kinematicslib.ik.create_ik_handle(ball_jnt, toe_jnt, solver="SC")

		ball_ik_grp = cmds.createNode("transform", n=ball_ik + "_GRP")
		toe_ik_grp = cmds.createNode("transform", n=toe_ik + "_GRP")

		cmds.parent(toe_ik, toe_ik_grp)
		cmds.parent(ball_ik, ball_ik_grp)
		cmds.parent(toe_ik_grp, ball_ik_ctrl)
		cmds.parent(ball_ik_grp, soft_ik_parent_grp, reverse_ball_ctrl.last_node)

		# setup ik
		cmds.connectAttr(leg_ik + ".ikBlend", ball_ik + ".ikBlend")
		cmds.connectAttr(leg_ik + ".ikBlend", toe_ik + ".ikBlend")

		# connect attrs
		cmds.connectAttr(leg_ik_ctrl.path + ".toeTipPivot", toe_tip_piv_grp + ".ry")
		cmds.connectAttr(leg_ik_ctrl.path + ".ballPivot", ball_piv_grp + ".ry")
		cmds.connectAttr(leg_ik_ctrl.path + ".heelPivot", heel_piv_grp + ".ry")
		attributeslib.connection.negative_connection(leg_ik_ctrl.path + ".heelLift", heel_piv_grp + ".rx")
		cmds.connectAttr(leg_ik_ctrl.path + ".ballLift", reverse_ball_ctrl.groups[-1] + ".rx")
		attributeslib.connection.negative_connection(leg_ik_ctrl.path + ".toeTipLift", ball_ik_ctrl.groups[-1] + ".rx")
		cmds.connectAttr(leg_ik_ctrl.path + ".toeLift", toe_ctrl.groups[-1] + ".rx")

		# setup side roll
		inner_clamp = cmds.createNode("clamp", n=inner_roll_grp + "_clamp")
		outter_clamp = cmds.createNode("clamp", n=outter_roll_grp + "_clamp")
		cmds.setAttr(inner_clamp + ".minR", -100000)
		cmds.setAttr(outter_clamp + ".maxR", 100000)

		attributeslib.connection.negative_connection(leg_ik_ctrl.path + ".sideRoll", inner_clamp + ".inputR")
		attributeslib.connection.negative_connection(leg_ik_ctrl.path + ".sideRoll", outter_clamp + ".inputR")
		cmds.connectAttr(inner_clamp + ".outputR", outter_roll_grp + ".rz")
		cmds.connectAttr(outter_clamp + ".outputR", inner_roll_grp + ".rz")

		# setup ball heel toe roll
		heel_roll_clamp = cmds.createNode("clamp")
		cmds.connectAttr(leg_ik_ctrl.path + ".roll", heel_roll_clamp + ".inputR")
		cmds.setAttr(heel_roll_clamp + ".minR", -100000)
		cmds.connectAttr(heel_roll_clamp + ".outputR", heel_ctrl.groups[-1] + ".rx", f=True)

		# # set range FROM: -1.0 -- 1.01 TO: 0.0 -- 1.0
		bias_set_range = cmds.createNode("setRange")
		cmds.connectAttr(leg_ik_ctrl.path + ".rollBias", bias_set_range + ".valueX")
		cmds.setAttr(bias_set_range + ".maxX", 1)
		cmds.setAttr(bias_set_range + ".oldMinX", -1)
		cmds.setAttr(bias_set_range + ".oldMaxX", 1)

		# convert value to angular value
		bias_mdl = cmds.createNode("multDoubleLinear")
		cmds.connectAttr(bias_set_range + ".outValueX", bias_mdl + ".input1")
		cmds.setAttr(bias_mdl + ".input2", 90)

		# Create clamp and drive the reverse ball grp  clamp(min: 0 max:value input: leg_ik_ctrl.path.footRoll)
		reverse_ball_roll_clamp = cmds.createNode("clamp")
		cmds.connectAttr(leg_ik_ctrl.path + ".roll", reverse_ball_roll_clamp + ".inputR")
		cmds.connectAttr(bias_mdl + ".output", reverse_ball_roll_clamp + ".maxR")
		cmds.connectAttr(reverse_ball_roll_clamp + ".outputR", reverse_ball_ctrl.groups[-2] + ".rx")

		reverse_ball_negative_clamp = cmds.createNode("clamp")
		cmds.setAttr(reverse_ball_negative_clamp + ".maxR", 1000000)

		# set up subtract node
		reverse_ball_negative_pma = cmds.createNode("plusMinusAverage")
		cmds.setAttr(reverse_ball_negative_pma + ".operation", 2)

		cmds.connectAttr(leg_ik_ctrl.path + ".roll", reverse_ball_negative_pma + ".input1D[0]")
		cmds.connectAttr(reverse_ball_roll_clamp + ".outputR", reverse_ball_negative_pma + ".input1D[1]")
		cmds.connectAttr(reverse_ball_negative_pma + ".output1D", reverse_ball_negative_clamp + ".inputR")
		cmds.connectAttr(reverse_ball_negative_clamp + ".outputR", toe_ctrl.groups[-2] + ".rx")

		# Connect the last part MATH: L_foot_reverseBall_CTRL_GRP.rotateX = -L_foot_toeTip_CTRL_ZERO_adl.input2;
		reverse_ball_roll_grp_mdl = cmds.createNode("multDoubleLinear")
		cmds.setAttr(reverse_ball_roll_grp_mdl + ".input2", -1)
		cmds.connectAttr(reverse_ball_negative_clamp + ".outputR", reverse_ball_roll_grp_mdl + ".input1")
		cmds.connectAttr(reverse_ball_roll_grp_mdl + ".output", reverse_ball_ctrl.groups[0] + ".rx")
		attributeslib.connection.negative_connection(leg_ik_ctrl.path + ".rollBallUnbend",
		                                             reverse_ball_roll_grp_mdl + ".input2")

		cmds.hide(ball_ik, toe_ik)

		ctrls = [reverse_ball_ctrl, toe_ctrl, ball_inner_ctrl, ball_outter_ctrl, heel_ctrl]
		for ctrl in ctrls:
			attributeslib.set_attributes(ctrl.all_controls, "s", lock=True, keyable=False)

		ctrls = [ball_fk_ctrl, ball_ik_ctrl]
		for ctrl in ctrls:
			attributeslib.set_attributes(ctrl.all_controls, ["t", "s"], lock=True, keyable=False)
