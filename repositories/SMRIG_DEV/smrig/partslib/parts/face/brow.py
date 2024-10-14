# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig import env
from smrig.lib import attributeslib
from smrig.lib import colorlib
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import rivetlib
from smrig.lib import transformslib
from smrig.partslib.common import basepart

left_side, right_side = env.prefs.get_sides()[0:2]
left_colors = colorlib.get_colors_from_side(left_side)
right_colors = colorlib.get_colors_from_side(right_side)
log = logging.getLogger("smrig.partslib.brow")


class Brow(basepart.Basepart):
	"""
	brow rig part module.
	"""

	BUILD_LAST = False

	def __init__(self, *guide_node, **options):
		super(Brow, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C", editable=False)
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_skull_JNT", value_required=True)
		self.register_option("numControls", "int", 3, min=2, rebuild_required=True)
		self.register_option("createCenterControl", "bool", True, rebuild_required=True)
		self.register_option("createSubControls", "bool", True, rebuild_required=True)
		self.register_option("createNurbsSurface", "bool", True, rebuild_required=True)

	@property
	def num_controls(self):
		"""

		:return:
		"""
		return self.options.get("numControls").get("value")

	@property
	def create_center_control(self):
		"""

		:return:
		"""
		return self.options.get("createCenterControl").get("value")

	@property
	def create_sub_controls(self):
		"""

		:return:
		"""
		return self.options.get("createSubControls").get("value")

	@property
	def create_nurbs_surface(self):
		"""

		:return:
		"""
		return self.options.get("createNurbsSurface").get("value")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		div = 2.0 / self.num_controls
		ctrls, plcs, jnts = [], [], []

		for side, colors, direction in zip([left_side, right_side], [left_colors, right_colors], [1, -1]):
			for idx in range(self.num_controls):
				plc = self.create_placer(["brow", idx + 1], side=side)
				jnt = self.create_joint(["brow", idx + 1], side=side, placer_driver=plc)
				ctrl = self.create_control(["brow", idx + 1], side=side, shape="cube", color=colors[0],
				                           driver=jnt, create_offset_controls=False)
				off_ctrl = self.create_control(["brow", "offset", idx + 1], side=side, scale=0.6,
				                               shape="sphere", color=colors[1], driver=jnt)

				plcs.append(plc)
				jnts.append(jnt)
				ctrls.append(ctrl)
				ctrls.append(off_ctrl)

				cmds.xform(plc.path, t=[div * direction * (idx + 1), 0, 0])

				if side == right_side:
					cmds.xform(ctrl.groups[0], off_ctrl.groups[0], r=True, ro=[0, 180, 0], s=[1, 1, -1])

				if self.create_sub_controls:
					plc = self.create_placer(["brow", "upper", idx + 1], side=side)
					jnt = self.create_joint(["brow", "upper", idx + 1], side=side, placer_driver=plc)
					ctrl = self.create_control(["brow", "upper", idx + 1],
					                           side=side, shape="diamond", color=colors[0],
					                           driver=jnt, create_offset_controls=False)

					off_ctrl = self.create_control(["brow", "upper", "offset", idx + 1], scale=0.6,
					                               side=side, shape="sphere", color=colors[1], driver=jnt)

					plcs.append(plc)
					jnts.append(jnt)
					ctrls.append(ctrl)
					ctrls.append(off_ctrl)

					cmds.xform(plc.path, t=[div * direction * (idx + 1), 1, 0])

					if side == right_side:
						cmds.xform(ctrl.groups[0], off_ctrl.groups[0], r=True, ro=[0, 180, 0], s=[1, 1, -1])

		if self.create_center_control:
			plc = self.create_placer(["brow"])
			jnt = self.create_joint(["brow"], placer_driver=plc)
			ctrl = self.create_control(["brow"], shape="cube", color=self.primary_color,
			                           driver=jnt, create_offset_controls=False)

			off_ctrl = self.create_control(["brow", "offset"], shape="sphere", color=self.secondary_color,
			                               driver=jnt, create_offset_controls=False, scale=0.6)

			plcs.append(plc)
			jnts.append(jnt)
			ctrls.append(ctrl)
			ctrls.append(off_ctrl)

			if self.create_sub_controls:
				plc = self.create_placer(["brow", "upper"])
				jnt = self.create_joint(["brow", "upper"], placer_driver=plc)
				ctrl = self.create_control(["brow", "upper"], shape="diamond",
				                           create_offset_controls=False, color=self.primary_color, driver=jnt)

				off_ctrl = self.create_control(["brow", "upper", "offset"], scale=0.6,
				                               shape="sphere", color=self.secondary_color, driver=jnt)

				plcs.append(plc)
				jnts.append(jnt)
				ctrls.append(ctrl)
				ctrls.append(off_ctrl)

				cmds.xform(plc.path, t=[0, 1, 0])

		if self.create_nurbs_surface:
			surf = self.create_guide_surface("brow")

			result = cmds.nonLinear(surf, type="bend")
			cmds.xform(result[1], ro=[0, 90, 0])
			cmds.setAttr(result[0] + ".lowBound", 0)
			cmds.parentConstraint(surf, result[1], mo=1)
			cmds.scaleConstraint(surf, result[1], mo=1)
			cmds.parent(result[1], self.noxform_group)
			cmds.rename(result[0], self.format_name("verticle", node_type="nonLinear"))

			result = cmds.nonLinear(surf, type="bend")
			cmds.xform(result[1], ro=[90, 90, 0])
			cmds.parentConstraint(surf, result[1], mo=1)
			cmds.scaleConstraint(surf, result[1], mo=1)
			cmds.parent(result[1], self.noxform_group)
			cmds.rename(result[0], self.format_name("horizontal", node_type="nonLinear"))

			for plc, jnt in zip(plcs, jnts):
				cmds.delete(jnt + "_PRC")
				rivetlib.create_surface_rivet(surf, jnt, driver=plc.path, maintain_offset=True)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		ctrls, sub_ctrls, off_ctrls, off_sub_ctrls = [], [], [], []
		jnts, sub_jnts = [], []

		for side in [left_side, right_side]:
			for idx in range(self.num_controls):
				jnts.append(self.format_name(["brow", idx + 1], side=side, node_type="joint"))
				ctrls.append(self.format_name(["brow", idx + 1], side=side, node_type="animControl"))
				off_ctrls.append(self.format_name(["brow", "offset", idx + 1], side=side, node_type="animControl"))

				if self.create_sub_controls:
					sub_jnts.append(self.format_name(["brow", "upper", idx + 1], side=side, node_type="joint"))
					sub_ctrls.append(self.format_name(["brow", "upper", idx + 1], side=side, node_type="animControl"))
					off_sub_ctrls.append(self.format_name(["brow", "upper", "offset", idx + 1],
					                                      side=side, node_type="animControl"))

		if self.create_center_control:
			jnts.append(self.format_name(["brow"], node_type="joint"))
			ctrls.append(self.format_name(["brow"], node_type="animControl"))
			off_ctrls.append(self.format_name(["brow", "offset"], node_type="animControl"))

			if self.create_sub_controls:
				sub_jnts.append(self.format_name(["brow", "upper"], node_type="joint"))
				sub_ctrls.append(self.format_name(["brow", "upper"], node_type="animControl"))
				off_sub_ctrls.append(self.format_name(["brow", "upper", "offset"], node_type="animControl"))

		for i, ctrl in enumerate(ctrls):
			ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(sub_ctrls):
			sub_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(off_ctrls):
			off_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(off_sub_ctrls):
			off_sub_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		# create all ctrls
		l_ctrls = [c for c in ctrls if c.path.startswith(left_side)]
		r_ctrls = [c for c in ctrls if c.path.startswith(right_side)]
		l_sub_ctrls = [c for c in sub_ctrls if c.path.startswith(left_side)]
		r_sub_ctrls = [c for c in sub_ctrls if c.path.startswith(right_side)]
		l_off_ctrls = [c for c in off_ctrls if c.path.startswith(left_side)]
		r_off_ctrls = [c for c in off_ctrls if c.path.startswith(right_side)]
		l_off_sub_ctrls = [c for c in off_sub_ctrls if c.path.startswith(left_side)]
		r_off_sub_ctrls = [c for c in off_sub_ctrls if c.path.startswith(right_side)]

		l_all_ctrl = self.create_all_ctrl(["brow", "all"], left_side, left_colors, l_ctrls)
		r_all_ctrl = self.create_all_ctrl(["brow", "all"], right_side, right_colors, r_ctrls)
		l_all_sub_ctrl, r_all_sub_ctrl = None, None

		cmds.parent([c.groups[-1] for c in l_ctrls], l_all_ctrl.last_node)
		cmds.parent([c.groups[-1] for c in r_ctrls], r_all_ctrl.last_node)
		cmds.parent(l_all_ctrl.groups[-1], r_all_ctrl.groups[-1], self.get_control_group())

		for ctrl, off_ctrl in zip(ctrls + sub_ctrls, off_ctrls + off_sub_ctrls):
			cmds.parent(off_ctrl.groups[-1], ctrl.last_node)

		if self.create_center_control:
			pc = cmds.pointConstraint(l_ctrls[0].last_node, r_ctrls[0].last_node, ctrls[-1].groups[-1], mo=1)[0]
			cmds.parent(ctrls[-1].groups[-1], self.get_control_group())

			cmds.addAttr(ctrls[-1].path, ln="LRInfluence", dv=1, min=0, max=1, k=True)
			cmds.connectAttr(ctrls[-1].path + ".LRInfluence", pc + ".w0")
			cmds.connectAttr(ctrls[-1].path + ".LRInfluence", pc + ".w1")

		if self.create_sub_controls:
			l_all_sub_ctrl = self.create_all_ctrl(["brow", "upper", "all"], left_side, left_colors, l_sub_ctrls)
			r_all_sub_ctrl = self.create_all_ctrl(["brow", "upper", "all"], right_side, right_colors, r_sub_ctrls)

			cmds.parent([c.groups[-1] for c in l_sub_ctrls], l_all_sub_ctrl.last_node)
			cmds.parent([c.groups[-1] for c in r_sub_ctrls], r_all_sub_ctrl.last_node)
			cmds.parent(l_all_sub_ctrl.groups[-1], r_all_sub_ctrl.groups[-1], self.get_control_group())

			if self.create_center_control:
				cmds.pointConstraint(l_all_sub_ctrl.last_node, r_all_sub_ctrl.last_node, sub_ctrls[-1].groups[-1], mo=1)
				cmds.parent(sub_ctrls[-1].groups[-1], self.get_control_group())

		if self.create_nurbs_surface:
			surf = self.get_guide_node(self.format_name("brow", node_type="nurbsSurface"))
			surf = cmds.duplicate(surf)[0]
			cmds.parent(surf, self.noxform_group)
			constraintslib.matrix_constraint(self.get_rig_group(), surf)

			for ctrl, off_ctrl, jnt in zip(ctrls + sub_ctrls, off_ctrls + off_sub_ctrls, jnts + sub_jnts):
				self.connect_joint_to_surface(surf, ctrl, off_ctrl, jnt)

		else:
			for ctrl, jnt in zip(off_ctrls + off_sub_ctrls, jnts + sub_jnts):
				constraintslib.matrix_constraint(ctrl.path, jnt)

		if self.create_sub_controls:
			for ctrl, s_ctrl in zip(ctrls + [l_all_ctrl, r_all_ctrl], sub_ctrls + [l_all_sub_ctrl, r_all_sub_ctrl]):
				cmds.addAttr(s_ctrl.path, ln="influence", min=0, max=1.0, dv=0.5, k=True)

				for attr in ["tx", "ty"]:
					attributeslib.connection.multiply_connection("{}.{}".format(ctrl.path, attr),
					                                             multiply_plug="{}.{}".format(s_ctrl.path, "influence"),
					                                             target_plug="{}.{}".format(s_ctrl.groups[-2], attr))

	def create_all_ctrl(self, name, side, colors, ctrls):
		"""
		Create al ctrl for each section.

		:param name:
		:param side:
		:param colors:
		:param ctrls:
		:return:
		"""
		name = self.format_name(name, side=side, node_type="animControl")
		all_ctrl = controlslib.create_control(name=name, color=colors[0], num_groups=3)

		transformslib.xform.match(ctrls[int(self.num_controls / 2)].groups[-1], all_ctrl.groups[-1], scale=True)
		cmds.delete(cmds.pointConstraint(ctrls, all_ctrl.groups[-1]))

		targets = [transformslib.xform.match_locator(c.path,
		                                             name=c.path + "_crv_link",
		                                             node_type="transform",
		                                             parent=c.path) for c in ctrls]

		geometrylib.curve.create_curve_link(targets, degree=1, parent=all_ctrl.path, replace_shapes=True)

		return all_ctrl

	def connect_joint_to_surface(self, surf, ctrl, off_ctrl, jnt):
		"""

		:param surf:
		:param ctrl:
		:param off_ctrl:
		:param jnt:
		:return:
		"""
		rvt_off_grp = cmds.createNode("transform", n=jnt + "_rivet_offset_GRP", p=jnt)
		rvt_grp = cmds.createNode("transform", n=jnt + "_rivet_GRP", p=rvt_off_grp)
		cmds.parent(rvt_off_grp, self.get_rig_group())

		rivetlib.create_surface_rivet(surf, rvt_off_grp, driver=ctrl.last_node, maintain_offset=True)
		cmds.connectAttr(ctrl.path + ".r", rvt_grp + ".r")
		cmds.connectAttr(ctrl.path + ".ro", rvt_grp + ".ro")
		cmds.connectAttr(ctrl.path + ".s", rvt_grp + ".s")

		constraintslib.matrix_constraint(ctrl.path, rvt_off_grp, translate=False, rotate=False, scale=True)
		constraintslib.matrix_constraint(rvt_grp, off_ctrl.groups[-1])
		constraintslib.matrix_constraint(off_ctrl.last_node, jnt)
