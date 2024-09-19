# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.mouth")

from smrig import env
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import rivetlib
from smrig.lib import transformslib
from smrig.lib import colorlib
from smrig.lib import animationlib

left_side, right_side = env.prefs.get_sides()[0:2]
left_colors = colorlib.get_colors_from_side(left_side)
right_colors = colorlib.get_colors_from_side(right_side)

upper_default = [
	[-2.108, -0.238, -1.394],
	[-2.103, -0.086, -0.985],
	[-1.979, -0.341, -0.1],
	[-1.279, 0.023, 1.025],
	[-0.002, 0.088, 1.573],
	[1.289, 0.024, 1.026],
	[1.967, -0.344, -0.097],
	[2.122, -0.082, -0.986],
	[2.109, -0.238, -1.392],
]
lower_default = [
	[-2.108, -0.238, -1.394],
	[-2.128, -0.207, -1.276],
	[-1.677, -0.521, -0.052],
	[-1.422, -0.246, 1.104],
	[-0.002, -0.169, 1.86],
	[1.402, -0.254, 1.096],
	[1.687, -0.518, -0.041],
	[2.132, -0.209, -1.283],
	[2.109, -0.238, -1.392],
]
upper_roll_default = [
	[-2.262, -0.053, -1.463],
	[-2.296, 0.264, -1.168],
	[-2.069, 0.493, -0.365],
	[-1.281, 0.975, 0.525],
	[-0.043, 1.244, 0.847],
	[1.213, 0.997, 0.577],
	[2.066, 0.543, -0.282],
	[2.165, 0.293, -1.124],
	[2.263, 0.003, -1.41],
]
lower_roll_default = [
	[-2.262, -0.053, -1.463],
	[-2.182, -0.526, -1.829],
	[-1.739, -1.054, -0.608],
	[-1.475, -1.113, 0.684],
	[0.025, -1.056, 1.609],
	[1.568, -1.106, 0.62],
	[1.668, -1.063, -0.719],
	[2.287, -0.442, -1.848],
	[2.263, 0.003, -1.41],
]


class Mouth(basepart.Basepart):
	"""
	mouth rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Mouth, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C", editable=False)
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_head_JNT", value_required=True)
		self.register_option("skullJoint", "parent_driver", "C_skull_JNT", value_required=True)
		self.register_option("jawJoint", "parent_driver", "C_jaw_JNT", value_required=True)
		self.register_option("numControls", "int", 1, min=1, value_required=True, rebuild_required=True)
		self.register_option("numJoints", "int", 4, min=1, value_required=True, rebuild_required=True)
		self.register_option("upperLipEdgeLoopRef", "selection", "")
		self.register_option("lowerLipEdgeLoopRef", "selection", "")
		self.register_option("upperLipRollEdgeLoopRef", "selection", "")
		self.register_option("lowerLipRollEdgeLoopRef", "selection", "")

	@property
	def num_joints(self):
		"""

		:return:
		"""
		return self.options.get("numJoints").get("value")

	@property
	def num_controls(self):
		"""

		:return:
		"""
		return self.options.get("numControls").get("value")

	@property
	def upper_edge_loop(self):
		return self.find_stashed_nodes("upperLipEdgeLoopRef")

	@property
	def lower_edge_loop(self):
		return self.find_stashed_nodes("lowerLipEdgeLoopRef")

	@property
	def upper_roll_edge_loop(self):
		return self.find_stashed_nodes("upperLipRollEdgeLoopRef")

	@property
	def lower_roll_edge_loop(self):
		return self.find_stashed_nodes("lowerLipRollEdgeLoopRef")

	@property
	def up_joints(self):
		return [self.format_name(["lip", "upper", i + 1], node_type="joint") for i in range(self.num_joints)]

	@property
	def lo_joints(self):
		return [self.format_name(["lip", "lower", i + 1], node_type="joint") for i in range(self.num_joints)]

	@property
	def up_controls(self):
		return [self.format_name(["lip", "upper", i + 1], node_type="animControl") for i in range(self.num_controls)]

	@property
	def lo_controls(self):
		return [self.format_name(["lip", "lower", i + 1], node_type="animControl") for i in range(self.num_controls)]

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""

		# create curves  -------------------------------------------------------

		crv_name = self.format_name("upperLip", node_type="nurbsCurve")
		if self.upper_edge_loop:
			upper_lip_crv = geometrylib.curve.create_curve_from_edges(self.upper_edge_loop, crv_name)
		else:
			upper_lip_crv = geometrylib.curve.create_curve_from_points(upper_default, name=crv_name)

		crv_name = self.format_name("lowerLip", node_type="nurbsCurve")
		if self.lower_edge_loop:
			lower_lip_crv = geometrylib.curve.create_curve_from_edges(self.lower_edge_loop, crv_name)
		else:
			lower_lip_crv = geometrylib.curve.create_curve_from_points(lower_default, name=crv_name)

		crv_name = self.format_name("upperLipRoll", node_type="nurbsCurve")
		if self.upper_roll_edge_loop:
			upper_roll_lip_crv = geometrylib.curve.create_curve_from_edges(self.upper_roll_edge_loop, crv_name)
		else:
			upper_roll_lip_crv = geometrylib.curve.create_curve_from_points(upper_roll_default, name=crv_name)

		crv_name = self.format_name("lowerLipRoll", node_type="nurbsCurve")
		if self.lower_roll_edge_loop:
			lower_roll_lip_crv = geometrylib.curve.create_curve_from_edges(self.lower_roll_edge_loop, crv_name)
		else:
			lower_roll_lip_crv = geometrylib.curve.create_curve_from_points(lower_roll_default, name=crv_name)

		# reverse curves if needed -------------------------------------------

		geometrylib.curve.set_curve_direction(upper_lip_crv)
		geometrylib.curve.set_curve_direction(lower_lip_crv)
		geometrylib.curve.set_curve_direction(upper_roll_lip_crv)
		geometrylib.curve.set_curve_direction(lower_roll_lip_crv)

		# generate upper joint placers ---------------------------------------

		ctrls = self.create_joints("upper", upper_lip_crv, upper_roll_lip_crv)
		ctrls += self.create_joints("lower", lower_lip_crv, lower_roll_lip_crv, skip_corners=True)
		ctrls += self.create_primary_ctrls("upper", upper_lip_crv)
		ctrls += self.create_primary_ctrls("lower", lower_lip_crv)

		corner_ctrls = [c for c in ctrls if "Corner" in c.path]
		loc = transformslib.xform.match_locator(corner_ctrls)
		all_ctrl = self.create_control("mouthAll", shape="torso", axis="z", color=self.primary_color)
		transformslib.xform.match(loc, all_ctrl.groups[-1])
		ctrls.append(all_ctrl)

		upper_ctrls = [c for c in ctrls if "upper" in c.path]
		lower_ctrls = [c for c in ctrls if "lower" in c.path]

		cmds.addAttr(self.guide_group, ln="controlPivotScale", min=0.001, dv=1, k=True)
		cmds.addAttr(self.guide_group, ln="controlScale", min=0.001, dv=1, k=True)
		cmds.addAttr(self.guide_group, ln="controlOffsetY", min=0, k=True)
		cmds.addAttr(self.guide_group, ln="controlOffsetZ", min=0, k=True)

		for ctrl in ctrls:
			cmds.connectAttr(self.guide_group + ".controlPivotScale", ctrl.groups[-1] + ".sx")
			cmds.connectAttr(self.guide_group + ".controlPivotScale", ctrl.groups[-1] + ".sy")
			cmds.connectAttr(self.guide_group + ".controlPivotScale", ctrl.groups[-1] + ".sz")

			cmds.connectAttr(self.guide_group + ".controlScale", ctrl.path + ".sx")
			cmds.connectAttr(self.guide_group + ".controlScale", ctrl.path + ".sy")
			cmds.connectAttr(self.guide_group + ".controlScale", ctrl.path + ".sz")
			cmds.connectAttr(self.guide_group + ".controlOffsetZ", ctrl.path + ".tz")

			if ctrl in upper_ctrls:
				cmds.connectAttr(self.guide_group + ".controlOffsetY", ctrl.path + ".ty")

			elif ctrl in lower_ctrls:
				attributeslib.connection.negative_connection(self.guide_group + ".controlOffsetY", ctrl.path + ".ty")

		cmds.delete(upper_roll_lip_crv, lower_roll_lip_crv, upper_lip_crv, lower_lip_crv, loc)
		cmds.setAttr(self.guide_group + ".controlDisplayLocalAxis", 1)

	def create_joints(self, token, curve, roll_curve, skip_corners=False):
		"""

		:param token:
		:param curve:
		:param roll_curve:
		:param skip_corners:
		:return:
		"""
		name_tokens = [[["lipCorner"], right_side]]
		name_tokens += reversed([[["{}Lip".format(token), i + 1], right_side] for i in range(self.num_joints)])
		name_tokens += [[["{}Lip".format(token)], self.side]]
		name_tokens += [[["{}Lip".format(token), i + 1], left_side] for i in range(self.num_joints)]
		name_tokens += [[["lipCorner"], left_side]]

		pts = geometrylib.curve.get_uniform_points_on_curve(curve, num=len(name_tokens))
		ctrls = []
		for tokens, pt in zip(name_tokens, pts):
			tk, side = list(tokens)

			if cmds.objExists(self.format_name(name=list(tk), side=str(side), node_type="joint")):
				continue

			plc = self.create_placer(name=list(tk), side=str(side))

			tk, side = list(tokens)
			jnt = self.create_joint(name=list(tk), side=str(side), placer_driver=plc)
			cmds.xform(plc.path, ws=1, t=pt[:-1])

			color = self.secondary_color
			color = left_colors[1] if side == left_side else right_colors[1] if side == right_side else color

			if "Corner" in jnt:
				jntr = jnt

			else:
				tkb = [tk[0] + "Base"] + tk[1:] if len(tk) > 1 else [tk[0] + "Base"]
				plcb = self.create_placer(name=tkb, side=side)

				tkb = [tk[0] + "Base"] + tk[1:] if len(tk) > 1 else [tk[0] + "Base"]
				jntb = self.create_joint(name=tkb, side=side, placer_driver=plcb)
				get_nearest_point_in_YZ(roll_curve, plc.path, plcb.path)

				tkr = [tk[0] + "Roll"] + tk[1:] if len(tk) > 1 else [tk[0] + "Roll"]
				plcr = self.create_placer(name=tkr, side=side)

				tkr = [tk[0] + "Roll"] + tk[1:] if len(tk) > 1 else [tk[0] + "Roll"]
				jntr = self.create_joint(name=tkr, side=side, placer_driver=plcr)
				transformslib.xform.match_blend(plcb, plc, plcr, weight=0.1)

				cmds.parent(plcr.groups[-1], plcb.last_node)
				cmds.parent(jnt, jntr)
				cmds.parent(jntr, jntb)

				tctrl = self.create_control(name=list(tk) + ["tip"],
				                            side=str(side),
				                            shape="diamond",
				                            color=color,
				                            driver=jnt,
				                            create_offset_controls=False)
				ctrls.append(tctrl)

			# create ctrl
			ctrl = self.create_control(name=list(tk),
			                           side=str(side),
			                           shape="cube",
			                           color=color,
			                           driver=jntr,
			                           create_offset_controls=False)
			ctrls.append(ctrl)

			if side == right_side:
				cmds.xform(ctrl.groups[0], r=True, ro=[0, 180, 0], s=[1, 1, -1])

		return ctrls

	def create_primary_ctrls(self, token, curve):
		"""

		:return:
		"""
		name_tokens = [[["lipCorner"], right_side]]
		name_tokens += reversed([[["{}Lip".format(token), i + 1], right_side] for i in range(self.num_controls)])
		name_tokens += [[["{}Lip".format(token)], self.side]]
		name_tokens += [[["{}Lip".format(token), i + 1], left_side] for i in range(self.num_controls)]
		name_tokens += [[["lipCorner"], left_side]]

		pts = geometrylib.curve.get_uniform_points_on_curve(curve, num=len(name_tokens))
		ctrls = []

		for tokens, pt in zip(name_tokens, pts):
			tk, side = list(tokens)

			name_check = self.format_name(name=list(tk) + ["primary"], side=str(side), node_type="animControl")
			if cmds.objExists(name_check):
				continue

			color = self.primary_color
			color = left_colors[0] if side == left_side else right_colors[0] if side == right_side else color
			shape = "sphere" if "Corner" in name_check else "circle"
			ctrl = self.create_control(name=list(tk) + ["primary"],
			                           side=str(side),
			                           shape="sphere",
			                           color=color,
			                           scale=1.5,
			                           axis="z",
			                           create_offset_controls=False)

			cmds.xform(ctrl.groups[-1], ws=1, t=pt[:-1])

			if side == right_side:
				cmds.xform(ctrl.groups[0], r=True, ro=[0, 180, 0], s=[1, 1, -1])
			ctrls.append(ctrl)

		return ctrls

	def get_control_names(self, token, num, extra_token=None, node_type="animControl"):
		"""

		:param token:
		:param num:
		:param extra_token:
		:param node_type:
		:return:
		"""
		ctrls = []
		name_tokens = [[["lipCorner"], right_side]]
		name_tokens += reversed([[["{}Lip".format(token), i + 1], right_side] for i in range(num)])
		name_tokens += [[["{}Lip".format(token)], self.side]]
		name_tokens += [[["{}Lip".format(token), i + 1], left_side] for i in range(num)]
		name_tokens += [[["lipCorner"], left_side]]

		for tokens in name_tokens:
			tk, side = list(tokens)

			if extra_token:
				tkk = list(tk) + [extra_token]
			else:
				tkk = list(tk)

			name_check = self.format_name(name=tkk, side=str(side), node_type=node_type)
			ctrls.append(name_check)

		return ctrls

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		upper_jnts = self.get_control_names("upper", self.num_joints, node_type="joint")
		lower_jnts = self.get_control_names("lower", self.num_joints, node_type="joint")

		upper_ctrls = self.get_control_names("upper", self.num_joints)
		lower_ctrls = self.get_control_names("lower", self.num_joints)
		upper_primary_ctrls = self.get_control_names("upper", self.num_controls, extra_token="primary")
		lower_primary_ctrls = self.get_control_names("lower", self.num_controls, extra_token="primary")

		t_upper_ctrls = self.get_control_names("upper", self.num_joints, extra_token="tip")
		t_lower_ctrls = self.get_control_names("lower", self.num_joints, extra_token="tip")

		t_upper_ctrls = [self.create_control_from_guide(c, scale=True) for c in t_upper_ctrls[1:-1] if
		                 not cmds.objExists(c)]
		t_lower_ctrls = [self.create_control_from_guide(c, scale=True) for c in t_lower_ctrls[1:-1] if
		                 not cmds.objExists(c)]

		upper_ctrls = [self.create_control_from_guide(c, scale=True) for c in upper_ctrls if not cmds.objExists(c)]
		lower_ctrls = [self.create_control_from_guide(c, scale=True) for c in lower_ctrls if not cmds.objExists(c)]

		upper_primary_ctrls = [self.create_control_from_guide(c, scale=True)
		                       for c in upper_primary_ctrls if not cmds.objExists(c)]

		lower_primary_ctrls = [self.create_control_from_guide(c, scale=True)
		                       for c in lower_primary_ctrls if not cmds.objExists(c)]

		mouth_all_ctrl = self.create_control_from_guide(self.format_name("mouthAll",
		                                                                 node_type="animControl"), scale=True)

		"""for ctrl in upper_ctrls[1:-1] + lower_ctrls:
			pos = cmds.xform(ctrl, ws=1, q=1, t=1)
			jnt = ctrl.path.replace("CTL", "JNT").replace("Lip", "LipRoll")
			sp_pos = transformslib.xform.match_blend(jnt, ctrl, None, weight=0.75, return_only=True)
			transformslib.xform.match(jnt, ctrl.groups[0], rotate=False, scale=False)

			cmds.xform(ctrl, ws=1, t=pos)
			cmds.makeIdentity(ctrl, apply=1, t=1, r=1, s=1, n=0, pn=1)
			cmds.xform(ctrl, piv=[0, 0, 0])
			cmds.xform(ctrl, ws=True, sp=sp_pos)"""

		# create upper and lower lip all ctrls ---------------------------------------------------------

		name = self.format_name("upperLipAll", node_type="animControl")
		upper_lip_all_ctrl = controlslib.create_control(name, color=self.secondary_color)

		name = self.format_name("lowerLipAll", node_type="animControl")
		lower_lip_all_ctrl = controlslib.create_control(name, color=self.secondary_color)

		drv_ctrl = self.format_name("upperLip", node_type="animControl")
		transformslib.xform.match(drv_ctrl, upper_lip_all_ctrl.groups[-1], rotate=True, scale=True)

		drv_ctrl = self.format_name("lowerLip", node_type="animControl")
		transformslib.xform.match(drv_ctrl, lower_lip_all_ctrl.groups[-1], rotate=True, scale=True)

		# create link drivers
		u_targets = [transformslib.xform.match_locator(c.path,
		                                               name=c.path + "_crv_link",
		                                               node_type="transform",
		                                               parent=c.path) for c in upper_primary_ctrls]

		geometrylib.curve.create_curve_link(u_targets, degree=1, parent=upper_lip_all_ctrl.path, replace_shapes=True)

		l_targets = [transformslib.xform.match_locator(c.path,
		                                               name=c.path + "_crv_link",
		                                               node_type="transform",
		                                               parent=c.path) for c in lower_primary_ctrls]

		targets = [u_targets[0]] + l_targets + [u_targets[-1]]
		geometrylib.curve.create_curve_link(targets, degree=1, parent=lower_lip_all_ctrl.path, replace_shapes=True)

		# Create splines ---------------------------------------------------------

		name = self.format_name("upperLip", node_type="nurbsCurve")
		upper_crv = geometrylib.curve.create_curve_link([c.path for c in upper_primary_ctrls], name=name, degree=2)

		name = self.format_name("lowerLip", node_type="nurbsCurve")
		targets = [upper_primary_ctrls[0]] + lower_primary_ctrls + [upper_primary_ctrls[-1]]
		lower_crv = geometrylib.curve.create_curve_link([c.path for c in targets], name=name, degree=2)

		# rivet ctrls to splines --------------------------------------------------

		pos = [cmds.xform(c.groups[-2], q=1, ws=1, t=1) for c in upper_ctrls + lower_ctrls]

		rivetlib.create_curve_rivet(upper_crv, [c.groups[-1] for c in upper_ctrls], maintain_offset=False)
		rivetlib.create_curve_rivet(lower_crv, [c.groups[-1] for c in lower_ctrls], maintain_offset=False)

		for ctrl, p in zip(upper_ctrls + lower_ctrls, pos):
			cmds.xform(ctrl.groups[-2], ws=1, t=p)

		cmds.parent(upper_crv, lower_crv, self.noxform_group)

		# parent ctrls --------------------------------------------------

		upper_jaw = self.create_node("transform", "upperJaw", p=mouth_all_ctrl.last_node)
		lower_jaw = self.create_node("transform", "lowerJaw", p=mouth_all_ctrl.last_node)
		blend_jaw = self.create_node("transform", "blendJaw", p=mouth_all_ctrl.last_node)

		cmds.parent(upper_lip_all_ctrl.groups[-1], upper_jaw)
		cmds.parent([c.groups[-1] for c in upper_primary_ctrls[1:-1]], upper_lip_all_ctrl.last_node)

		cmds.parent(lower_lip_all_ctrl.groups[-1], lower_jaw)
		cmds.parent([c.groups[-1] for c in lower_primary_ctrls], lower_lip_all_ctrl.last_node)

		cmds.parent(upper_primary_ctrls[0].groups[-1], blend_jaw)
		cmds.parent(upper_primary_ctrls[-1].groups[-1], blend_jaw)

		cmds.parent([c.groups[-1] for c in upper_ctrls[1:-1]], upper_lip_all_ctrl.last_node)
		cmds.parent([c.groups[-1] for c in lower_ctrls], lower_lip_all_ctrl.last_node)
		cmds.parent(upper_ctrls[0].groups[-1], blend_jaw)
		cmds.parent(upper_ctrls[-1].groups[-1], blend_jaw)

		cmds.parent(mouth_all_ctrl.groups[-1], self.get_control_group("parent"))

		for ctrl, t_ctrl in zip(upper_ctrls[1:-1] + lower_ctrls, t_upper_ctrls + t_lower_ctrls):
			cmds.parent(t_ctrl.groups[-1], ctrl.last_node)

		# Create jaw blend ---------------------------------------------------------------------------

		upper_jaw_drv = self.create_node("transform", "upperJaw_driver", p=mouth_all_ctrl.groups[-2])
		lower_jaw_drv = self.create_node("transform", "lowerJaw_driver", p=mouth_all_ctrl.groups[-2])

		constraintslib.matrix_constraint(self.get_control_group("skullJoint"), upper_jaw_drv, maintain_offset=True)
		constraintslib.matrix_constraint(self.get_control_group("jawJoint"), lower_jaw_drv, maintain_offset=True)

		cmds.connectAttr(upper_jaw_drv + ".t", upper_jaw + ".t")
		cmds.connectAttr(upper_jaw_drv + ".r", upper_jaw + ".r")
		cmds.connectAttr(upper_jaw_drv + ".s", upper_jaw + ".s")
		cmds.connectAttr(upper_jaw_drv + ".shear", upper_jaw + ".shear")

		cmds.connectAttr(lower_jaw_drv + ".t", lower_jaw + ".t")
		cmds.connectAttr(lower_jaw_drv + ".r", lower_jaw + ".r")
		cmds.connectAttr(lower_jaw_drv + ".s", lower_jaw + ".s")
		cmds.connectAttr(lower_jaw_drv + ".shear", lower_jaw + ".shear")

		mtx = constraintslib.matrix_constraint_multi([upper_jaw, lower_jaw],
		                                             blend_jaw,
		                                             maintain_offset=True,
		                                             translate=True,
		                                             rotate=True,
		                                             scale=True,
		                                             weighted=True,
		                                             split=False,
		                                             matrix_plug="worldMatrix")

		cmds.addAttr(mouth_all_ctrl.path, ln="cornerJawBlend", min=0, max=1, dv=0.5, k=True)
		cmds.connectAttr(mouth_all_ctrl.path + ".cornerJawBlend", "{}.{}W0".format(mtx, upper_jaw))
		attributeslib.connection.reverse_connection(mouth_all_ctrl.path + ".cornerJawBlend",
		                                            "{}.{}W1".format(mtx, lower_jaw))

		# constrain joints and create roll -------------------------------------------------------------------

		for ctrl in upper_ctrls[1:-1] + lower_ctrls:
			constraintslib.matrix_constraint(ctrl.path, ctrl.path.replace("CTL", "JNT").replace("Lip", "LipBase"))

		for ctrl in t_upper_ctrls + t_lower_ctrls:
			constraintslib.matrix_constraint(ctrl.path, ctrl.path.replace("tip_CTL", "JNT"))

			jnt = ctrl.path.replace("CTL", "JNT").replace("Lip", "LipRoll").replace("tip_", "")
			constraintslib.matrix_constraint(jnt, ctrl.groups[-1])

		constraintslib.matrix_constraint(upper_ctrls[0].path, upper_ctrls[0].path.replace("CTL", "JNT"))
		constraintslib.matrix_constraint(upper_ctrls[-1].path, upper_ctrls[-1].path.replace("CTL", "JNT"))

		self.create_roll_sdk(upper_lip_all_ctrl,
		                     upper_primary_ctrls, upper_ctrls, negative=True)

		self.create_roll_sdk(lower_lip_all_ctrl,
		                     [upper_primary_ctrls[0]] + lower_primary_ctrls + [upper_primary_ctrls[-1]],
		                     [upper_ctrls[0]] + lower_ctrls + [upper_ctrls[-1]])

		# lock and hide stuff -------------------------------------------------------------------
		attributeslib.set_attributes(upper_primary_ctrls + lower_primary_ctrls, ["r", "s", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(upper_ctrls + lower_ctrls, ["primaryRoll"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

	def create_roll_sdk(self, all_ctrl, primary_ctrls, secondary_ctrls, interpolation=1, negative=False):
		"""

		:param all_ctrl:
		:param primary_ctrls:
		:param secondary_ctrls:
		:param interpolation:
		:param negative:
		:return:
		"""
		# create ramps
		number_p_ctrls = len(primary_ctrls)
		number_s_ctrls = len(secondary_ctrls)
		div = 1.0 / (number_p_ctrls - 1)
		ramps = []

		for i in range(number_p_ctrls):
			pre = (i - 1) * div
			post = (i + 1) * div
			current = i * div

			ramp = cmds.createNode("ramp")
			cmds.setAttr(ramp + ".colorEntryList[0].color", 0, 0, 0, type="double3")
			cmds.setAttr(ramp + ".colorEntryList[1].color", 1, 1, 1, type="double3")
			cmds.setAttr(ramp + ".colorEntryList[2].color", 0, 0, 0, type="double3")
			cmds.setAttr(ramp + ".colorEntryList[0].position", max(min(1, pre), 0))
			cmds.setAttr(ramp + ".colorEntryList[1].position", current)
			cmds.setAttr(ramp + ".colorEntryList[2].position", max(min(1, post), 0))
			cmds.setAttr(ramp + ".interpolation", interpolation)
			ramps.append(ramp)

		cmds.removeMultiInstance(ramps[-1] + ".colorEntryList[2]", b=True)
		cmds.removeMultiInstance(ramps[0] + ".colorEntryList[0]", b=True)

		# setup joint twist and Scale readers//
		# setup joint twist and Scale readers//
		div = 1.0 / (number_s_ctrls - 1)
		tt = "spline"

		cmds.addAttr(all_ctrl, ln="roll", k=True)

		for p_idx, p_ctrl in enumerate(primary_ctrls[1:-1], 1):
			if not cmds.objExists(p_ctrl.path + ".roll"):
				cmds.addAttr(p_ctrl, ln="roll", k=True)
				adl = attributeslib.connection.add_connection(all_ctrl.path + ".roll",
				                                              add_plug=p_ctrl.path + ".roll")

			for s_idx, s_ctrl in enumerate(secondary_ctrls[1:-1], 1):
				if not cmds.objExists(s_ctrl.path + ".roll"):
					cmds.addAttr(s_ctrl, ln="roll", k=True)
					cmds.addAttr(s_ctrl, ln="primaryRoll", k=True)

					jnt_name = s_ctrl.path.replace("CTL", "JNT").replace("Lip", "LipRoll")

					if negative:
						neg = attributeslib.connection.add_connection(s_ctrl.path + ".roll",
						                                              s_ctrl.path + ".primaryRoll")

						attributeslib.connection.negative_connection(neg, jnt_name + ".rx")

					else:
						attributeslib.connection.add_connection(s_ctrl.path + ".roll",
						                                        s_ctrl.path + ".primaryRoll",
						                                        target_plug=jnt_name + ".rx")

				cmds.setAttr(ramps[p_idx] + ".vCoord", div * s_idx)
				value = cmds.getAttr(ramps[p_idx] + ".outColorR")

				cmds.setDrivenKeyframe(s_ctrl.path + ".primaryRoll", cd=adl, dv=0, v=0, ott=tt, itt=tt)
				cmds.setDrivenKeyframe(s_ctrl.path + ".primaryRoll", cd=adl, dv=1, v=value, ott=tt, itt=tt)

		# set infinity
		cmds.delete(ramps)
		animationlib.set_inifity(animationlib.get_anim_curves(secondary_ctrls))


def get_nearest_point_in_YZ(curve, node, target=None):
	"""

	:return:
	"""
	orig = cmds.xform(node, q=1, ws=1, t=1)
	npoc = geometrylib.curve.get_nearest_point_on_curve(curve, node)[:-1]

	for iter in range(10):
		npoc[0] = orig[0]
		npoc = geometrylib.curve.get_nearest_point_on_curve(curve, npoc)[:-1]

	if target:
		cmds.xform(target, ws=1, t=npoc)

	return npoc
