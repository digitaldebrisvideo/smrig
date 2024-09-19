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
log = logging.getLogger("smrig.partslib.cheek")


class Cheek(basepart.Basepart):
	"""
	cheek rig part module.
	"""

	BUILD_LAST = False

	def __init__(self, *guide_node, **options):
		super(Cheek, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_skull_JNT", value_required=True)
		self.register_option("numControls", "int", 3, min=2, rebuild_required=True)
		self.register_option("createSquintControls", "bool", True, rebuild_required=True)
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
	def create_squint_controls(self):
		"""

		:return:
		"""
		return self.options.get("createSquintControls").get("value")

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
		div = 2.0 / (self.num_controls - 1)
		ctrls, off_ctrls, plcs, jnts = [], [], [], []

		for idx in range(self.num_controls):
			plc = self.create_placer(["cheek", idx + 1])
			jnt = self.create_joint(["cheek", idx + 1], placer_driver=plc)
			ctrl = self.create_control(["cheek", idx + 1], shape="cube", color=self.primary_color,
			                           driver=jnt, create_offset_controls=False)

			off_ctrl = self.create_control(["cheek", "offset", idx + 1], scale=0.9,
			                               shape="sphere", color=self.secondary_color, driver=jnt)

			plcs.append(plc)
			jnts.append(jnt)
			ctrls.append(ctrl)
			off_ctrls.append(off_ctrl)

			cmds.xform(plc.path, t=[(div * idx) - 1, 0, 0])

			if self.create_sub_controls:
				plc = self.create_placer(["cheek", "lower", idx + 1])
				jnt = self.create_joint(["cheek", "lower", idx + 1], placer_driver=plc)
				ctrl = self.create_control(["cheek", "lower", idx + 1],
				                           shape="diamond",
				                           color=self.primary_color,
				                           driver=jnt, create_offset_controls=False)

				off_ctrl = self.create_control(["cheek", "lower", "offset", idx + 1],
				                               shape="sphere", scale=0.6,
				                               color=self.secondary_color,
				                               driver=jnt)

				plcs.append(plc)
				jnts.append(jnt)
				ctrls.append(ctrl)
				off_ctrls.append(off_ctrl)

				cmds.xform(plc.path, t=[(div * idx) - 1, -1, 0])

			if self.create_squint_controls:
				plc = self.create_placer(["cheek", "squint", idx + 1])
				jnt = self.create_joint(["cheek", "squint", idx + 1], placer_driver=plc)
				ctrl = self.create_control(["cheek", "squint", idx + 1],
				                           shape="sphere",
				                           color=self.primary_color,
				                           driver=jnt)

				off_ctrl = self.create_control(["cheek", "squint", "offset", idx + 1],
				                               shape="sphere", scale=0.6,
				                               color=self.secondary_color,
				                               driver=jnt)
				plcs.append(plc)
				jnts.append(jnt)
				ctrls.append(ctrl)
				off_ctrls.append(off_ctrl)

				cmds.xform(plc.path, t=[(div * idx) - 1, 1, 0])

		if self.create_nurbs_surface:
			surf = self.create_guide_surface("cheek")

			for plc, jnt in zip(plcs, jnts):
				cmds.delete(jnt + "_PRC")
				rivetlib.create_surface_rivet(surf, jnt, driver=plc.path, maintain_offset=True)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		ctrls, sub_ctrls, squint_ctrls = [], [], []
		off_ctrls, off_sub_ctrls, off_squint_ctrls = [], [], []
		jnts, sub_jnts, squint_jnts = [], [], []

		for idx in range(self.num_controls):
			jnts.append(self.format_name(["cheek", idx + 1], node_type="joint"))
			ctrls.append(self.format_name(["cheek", idx + 1], node_type="animControl"))
			off_ctrls.append(self.format_name(["cheek", "offset", idx + 1], node_type="animControl"))

			if self.create_sub_controls:
				sub_jnts.append(self.format_name(["cheek", "lower", idx + 1], node_type="joint"))
				sub_ctrls.append(self.format_name(["cheek", "lower", idx + 1], node_type="animControl"))
				off_sub_ctrls.append(self.format_name(["cheek", "lower", "offset", idx + 1], node_type="animControl"))

			if self.create_squint_controls:
				squint_jnts.append(self.format_name(["cheek", "squint", idx + 1], node_type="joint"))
				squint_ctrls.append(self.format_name(["cheek", "squint", idx + 1], node_type="animControl"))
				off_squint_ctrls.append(
					self.format_name(["cheek", "squint", "offset", idx + 1], node_type="animControl"))

		for i, ctrl in enumerate(ctrls):
			ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(sub_ctrls):
			sub_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(squint_ctrls):
			squint_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(off_ctrls):
			off_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(off_sub_ctrls):
			off_sub_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		for i, ctrl in enumerate(off_squint_ctrls):
			off_squint_ctrls[i] = self.create_control_from_guide(ctrl, scale=True)

		# create all ctrls
		all_ctrl = self.create_all_ctrl(["cheek", "all"], ctrls)
		all_sub_ctrl, all_squint_ctrl = None, None

		cmds.parent([c.groups[-1] for c in ctrls], all_ctrl.last_node)
		cmds.parent(all_ctrl.groups[-1], self.get_control_group())

		for ctrl, off_ctrl in zip(ctrls + sub_ctrls + squint_ctrls, off_ctrls + off_sub_ctrls + off_squint_ctrls):
			cmds.parent(off_ctrl.groups[-1], ctrl.last_node)

		if self.create_sub_controls:
			all_sub_ctrl = self.create_all_ctrl(["cheek", "lower", "all"], sub_ctrls)
			cmds.parent([c.groups[-1] for c in sub_ctrls], all_sub_ctrl.last_node)
			cmds.parent(all_sub_ctrl.groups[-1], self.get_control_group())

		if self.create_squint_controls:
			all_squint_ctrl = self.create_all_ctrl(["cheek", "squint", "all"], squint_ctrls)
			cmds.parent([c.groups[-1] for c in squint_ctrls], all_squint_ctrl.last_node)
			cmds.parent(all_squint_ctrl.groups[-1], self.get_control_group())

		if self.create_nurbs_surface:
			surf = self.get_guide_node(self.format_name("cheek", node_type="nurbsSurface"))
			surf = cmds.duplicate(surf)[0]
			cmds.parent(surf, self.noxform_group)
			constraintslib.matrix_constraint(self.get_rig_group(), surf)

			for ctrl, off_ctrl, jnt in zip(ctrls + sub_ctrls + squint_ctrls,
			                               off_ctrls + off_sub_ctrls + off_squint_ctrls,
			                               jnts + sub_jnts + squint_jnts):
				self.connect_joint_to_surface(surf, ctrl, off_ctrl, jnt)

		else:
			for ctrl, jnt in zip(off_ctrls + off_sub_ctrls + off_squint_ctrls, jnts + sub_jnts + squint_jnts):
				constraintslib.matrix_constraint(ctrl.path, jnt)

		if self.create_sub_controls:
			for ctrl, s_ctrl in zip(ctrls + [all_ctrl], sub_ctrls + [all_sub_ctrl]):
				cmds.addAttr(s_ctrl.path, ln="influence", min=0, max=1.0, dv=0.5, k=True)

				for attr in ["tx", "ty"]:
					attributeslib.connection.multiply_connection("{}.{}".format(ctrl.path, attr),
					                                             multiply_plug="{}.{}".format(s_ctrl.path, "influence"),
					                                             target_plug="{}.{}".format(s_ctrl.groups[-2], attr))

		if self.create_squint_controls:
			for ctrl, s_ctrl in zip(ctrls + [all_ctrl], squint_ctrls + [all_squint_ctrl]):
				cmds.addAttr(s_ctrl.path, ln="influence", min=0, max=1.0, dv=0, k=True)

				for attr in ["tx", "ty"]:
					attributeslib.connection.multiply_connection("{}.{}".format(ctrl.path, attr),
					                                             multiply_plug="{}.{}".format(s_ctrl.path, "influence"),
					                                             target_plug="{}.{}".format(s_ctrl.groups[-2], attr))

	def create_all_ctrl(self, name, ctrls):
		"""
		Create al ctrl for each section.

		:param name:
		:param ctrls:
		:return:
		"""
		name = self.format_name(name, node_type="animControl")
		all_ctrl = controlslib.create_control(name=name, color=self.primary_color, num_groups=3)

		transformslib.xform.match(ctrls[self.num_controls / 2].groups[-1], all_ctrl.groups[-1], scale=True)
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
