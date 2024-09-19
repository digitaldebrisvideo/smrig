# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import rivetlib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.eyeLid")

upper_loop_default = [[-3.0, 0.0, 0.0],
                      [-2.484, 0.546, 0.0],
                      [-1.519, 1.718, 0.0],
                      [-0.052, 1.975, 0.0],
                      [1.493, 1.744, 0.0],
                      [2.587, 0.924, 0.0],
                      [3.0, 0.0, 0.0]]

lower_loop_default = [[-3.0, 0.0, 0.0],
                      [-2.484, -0.297, 0.0],
                      [-1.519, -0.935, 0.0],
                      [-0.052, -1.075, 0.0],
                      [1.493, -0.949, 0.0],
                      [2.587, -0.503, 0.0],
                      [3.0, 0.0, 0.0]]


class EyeLid(basepart.Basepart):
	"""
	eyeLid rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(EyeLid, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "L_eye_base_JNT", value_required=True)
		self.register_option("eyeJoint", "parent_driver", "L_eye1_JNT", value_required=True)
		self.register_option("eyeControl", "attribute_driver", "L_eye_fk_CTL", value_required=True)
		self.register_option("numControls", "int", 3, min=3, value_required=True, rebuild_required=True)
		self.register_option("numJoints", "int", -1, min=-1, value_required=True, rebuild_required=True)
		self.register_option("upperLidEdgeLoopRef", "selection", "")
		self.register_option("lowerLidEdgeLoopRef", "selection", "")

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
	def stashed_eye_joint(self):
		parent = self.options.get("eyeJoint").get("value")
		return parent if cmds.objExists(parent) else self.get_guide_node(self.options.get("eyeJoint").get("value"))

	@property
	def eye_control(self):
		"""

		:return:
		"""
		return self.options.get("eyeControl").get("value")

	@property
	def eye_joint(self):
		"""

		:return:
		"""
		return self.options.get("eyeJoint").get("value")

	@property
	def upper_edge_loop(self):
		return self.find_stashed_nodes("upperLidEdgeLoopRef")

	@property
	def lower_edge_loop(self):
		return self.find_stashed_nodes("lowerLidEdgeLoopRef")

	@property
	def up_joints(self):
		return [self.format_name(["lid", "upper", i + 1], node_type="joint") for i in range(self.num_joints)]

	@property
	def lo_joints(self):
		return [self.format_name(["lid", "lower", i + 1], node_type="joint") for i in range(self.num_joints)]

	@property
	def up_controls(self):
		return [self.format_name(["lid", "upper", i + 1], node_type="animControl") for i in range(self.num_controls)]

	@property
	def lo_controls(self):
		return [self.format_name(["lid", "lower", i + 1], node_type="animControl") for i in range(self.num_controls)]

	@property
	def lid_aim_base(self):
		return self.format_name(["lid", "aim", "pivot"], node_type="jointPlacer")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		if self.upper_edge_loop and self.lower_edge_loop:
			up_crv = geometrylib.curve.create_curve_from_edges(self.upper_edge_loop, self.format_name("up_edge_tmp"))
			lo_crv = geometrylib.curve.create_curve_from_edges(self.lower_edge_loop, self.format_name("lo_edge_tmp"))

			geometrylib.curve.set_curve_direction(up_crv, direction=self.mirror_value)
			geometrylib.curve.set_curve_direction(lo_crv, direction=self.mirror_value)

		else:
			up_crv = geometrylib.curve.create_curve_from_points(upper_loop_default, self.format_name("up_edge_tmp"))
			lo_crv = geometrylib.curve.create_curve_from_points(lower_loop_default, self.format_name("lo_edge_tmp"))

			cmds.parent(up_crv, lo_crv, self.guide_geometry_group)

		if self.stashed_eye_joint and cmds.objExists(self.stashed_eye_joint):
			transformslib.xform.match(self.stashed_eye_joint, self.guide_group, rotate=False)

		if self.num_joints == -1:
			num_joints = len(cmds.ls(up_crv + ".cv[*]", fl=1))

		else:
			num_joints = self.num_joints if self.num_joints > 2 else 3

		up_joint_positions = [p[:-1] for p in geometrylib.curve.get_uniform_points_on_curve(up_crv, num_joints + 2)]
		lo_joint_positions = [p[:-1] for p in geometrylib.curve.get_uniform_points_on_curve(lo_crv, num_joints + 2)]

		# create joints and placers
		aim_piv_plc = self.create_placer(["lid", "aim", "pivot"])

		up_placers = self.create_placers(["lid", "upper"], num_placers=num_joints)
		lo_placers = self.create_placers(["lid", "lower"], num_placers=num_joints)

		self.create_joints(["lid", "upper"], num_joints=num_joints, placer_drivers=up_placers)
		self.create_joints(["lid", "lower"], num_joints=num_joints, placer_drivers=lo_placers)

		up_placers.insert(0, self.create_placer(["lid", "inner"]))
		up_placers.append(self.create_placer(["lid", "outter"]))

		self.create_joint(["lid", "inner"], placer_driver=up_placers[0])
		self.create_joint(["lid", "outter"], placer_driver=up_placers[-1])

		for pos, plc in zip(up_joint_positions, up_placers):
			cmds.xform(plc.path, ws=True, t=pos)

		for pos, plc in zip(lo_joint_positions[1:-1], lo_placers):
			cmds.xform(plc.path, ws=True, t=pos)

		# aim constraint placers
		for plc in up_placers + lo_placers:
			cmds.delete(cmds.aimConstraint(self.guide_group, plc.path, aim=[-self.mirror_value, 0, 0]))

		# create controls
		up_ctrl_positions = geometrylib.curve.get_uniform_points_on_curve(up_crv, self.num_controls + 2)
		lo_ctrl_positions = geometrylib.curve.get_uniform_points_on_curve(lo_crv, self.num_controls + 2)

		up_controls = self.create_controls(["lid", "upper"],
		                                   num=self.num_controls,
		                                   shape="cube",
		                                   color=self.secondary_color,
		                                   scale=0.25,
		                                   create_offset_controls=False)

		lo_controls = self.create_controls(["lid", "lower"],
		                                   num=self.num_controls,
		                                   shape="cube",
		                                   color=self.secondary_color,
		                                   scale=0.25,
		                                   create_offset_controls=False)

		up_controls.insert(0, self.create_control(["lid", "inner"],
		                                          shape="cube",
		                                          color=self.secondary_color,
		                                          scale=0.25,
		                                          create_offset_controls=False))

		up_controls.append(self.create_control(["lid", "outter"],
		                                       shape="cube",
		                                       color=self.secondary_color,
		                                       scale=0.25,
		                                       create_offset_controls=False))

		for pos, ctrl in zip(up_ctrl_positions, up_controls):
			cmds.xform(ctrl.groups[0], ws=True, t=pos[:-1])

		for pos, ctrl in zip(lo_ctrl_positions[1:-1], lo_controls):
			cmds.xform(ctrl.groups[0], ws=True, t=pos[:-1])

		for ctrl in up_controls + lo_controls:
			tmp = transformslib.xform.match_locator(ctrl.path)
			cmds.xform(tmp, r=1, t=[0, 10, 0])

			cmds.delete(cmds.aimConstraint(tmp,
			                               ctrl.groups[0],
			                               aim=[0, 1, 0],
			                               u=[-self.mirror_value, 0, 0],
			                               wuo=self.guide_group,
			                               wut="object"), tmp)

		if self.stashed_eye_joint:
			transformslib.xform.match(self.stashed_eye_joint, aim_piv_plc.path, rotate=False)

		cmds.delete(up_crv, lo_crv)
		self.update_options(numJoints=num_joints)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		base_node = cmds.createNode("transform", name=self.format_name(["lid", "base"], node_type="transform"),
		                            p=self.get_rig_group("parent"))
		cmds.delete(cmds.pointConstraint(self.get_guide_node(self.lid_aim_base), base_node))
		attr_control_group = self.get_attribute_driver_group("eyeControl")

		up_joints = self.up_joints
		lo_joints = self.lo_joints
		in_joint = self.format_name(["lid", "inner"], node_type="joint")
		out_joint = self.format_name(["lid", "outter"], node_type="joint")

		# add attribtues
		cmds.addAttr(attr_control_group, ln="blink", min=-1, max=1, k=1)
		cmds.addAttr(attr_control_group, ln="upperBlink", min=-1, max=1, k=1)
		cmds.addAttr(attr_control_group, ln="lowerBlink", min=-1, max=1, k=1)
		cmds.addAttr(attr_control_group, ln="blinkLineBias", min=0, max=1, dv=0.2, k=1)
		cmds.addAttr(attr_control_group, ln="eyeInfluence", min=0, max=1, dv=0.2, k=1)

		# cmds.addAttr(attr_control_group, ln="upperBlinkOutput", min=-1, max=1, k=1)
		# cmds.addAttr(attr_control_group, ln="lowerBlinkOutput", min=-1, max=1, k=1)

		# create ctrls
		up_ctrls = [self.create_control_from_guide(c, center_pivot_on_control=False) for c in self.up_controls]
		lo_ctrls = [self.create_control_from_guide(c, center_pivot_on_control=False) for c in self.lo_controls]

		in_ctrl = self.create_control_from_guide(self.format_name(["lid", "inner"], node_type="animControl"),
		                                         center_pivot_on_control=False)

		out_ctrl = self.create_control_from_guide(self.format_name(["lid", "outter"], node_type="animControl"),
		                                          center_pivot_on_control=False)

		# up all ctrl
		up_center_ctrls, idx = utilslib.conversion.get_middle(up_ctrls)
		up_all_ctrl = controlslib.create_control(self.format_name(["lid", "upper"], node_type="animControl"),
		                                         color=up_center_ctrls[0].color)

		cmds.setAttr(up_all_ctrl.groups[-1] + ".s", *cmds.getAttr(up_center_ctrls[0].groups[-1] + ".s")[0])
		cmds.setAttr(up_all_ctrl.groups[-1] + ".r", *cmds.getAttr(up_center_ctrls[0].groups[-1] + ".r")[0])
		cmds.delete(cmds.pointConstraint(up_center_ctrls, up_all_ctrl.groups[-1]))

		targets = [c.path for c in [in_ctrl] + up_ctrls + [out_ctrl]]
		target_locs = [transformslib.xform.match_locator(t,
		                                                 name=t + "_LOC",
		                                                 parent=t,
		                                                 node_type="transform") for t in targets]

		geometrylib.curve.create_curve_link(target_locs,
		                                    parent=up_all_ctrl.path,
		                                    replace_shapes=True,
		                                    display_type="normal")

		cmds.parent([c.groups[-1] for c in up_ctrls], up_all_ctrl.last_node)

		# lo all ctrl
		lo_center_ctrls, idx = utilslib.conversion.get_middle(lo_ctrls)
		lo_all_ctrl = controlslib.create_control(self.format_name(["lid", "lower"], node_type="animControl"),
		                                         color=lo_center_ctrls[0].color)

		cmds.setAttr(lo_all_ctrl.groups[-1] + ".s", *cmds.getAttr(lo_center_ctrls[0].groups[-1] + ".s")[0])
		cmds.setAttr(lo_all_ctrl.groups[-1] + ".r", *cmds.getAttr(lo_center_ctrls[0].groups[-1] + ".r")[0])
		cmds.delete(cmds.pointConstraint(lo_center_ctrls, lo_all_ctrl.groups[-1]))

		targets = [c.path for c in [in_ctrl] + lo_ctrls + [out_ctrl]]
		target_locs = [transformslib.xform.match_locator(t,
		                                                 name=t + "_LOC#",
		                                                 parent=t,
		                                                 node_type="transform") for t in targets]

		geometrylib.curve.create_curve_link(target_locs,
		                                    parent=lo_all_ctrl.path,
		                                    replace_shapes=True,
		                                    display_type="normal")

		cmds.parent([c.groups[-1] for c in lo_ctrls], lo_all_ctrl.last_node)

		# ---------------------------------------------------------------------------------------

		# create curves for blink follow
		points = [c.path for c in [in_ctrl] + up_ctrls + [out_ctrl]]
		name = self.format_name(["lid", "upper", "driver"], node_type="nurbsCurve")
		up_driver_crv = geometrylib.curve.create_curve_link(points, name=name, degree=1)

		points = [in_joint] + up_joints + [out_joint]
		name = self.format_name(["lid", "upper"], node_type="nurbsCurve")
		up_crv = geometrylib.curve.create_curve_from_points(points, name=name, degree=1)
		up_crv = geometrylib.curve.rebuild_curve(up_crv, spans=self.num_controls + 2)

		cmds.parent(up_driver_crv, up_crv, self.noxform_group)

		wire = cmds.wire(up_crv, w=up_driver_crv)
		base = cmds.listConnections(wire[0] + ".baseWire")

		constraintslib.matrix_constraint(self.get_rig_group(), up_crv)
		constraintslib.matrix_constraint(self.get_rig_group(), base[0])

		cmds.setAttr(wire[0] + ".dropoffDistance[0]", 100000000)

		# lower
		points = [c.path for c in [in_ctrl] + lo_ctrls + [out_ctrl]]
		name = self.format_name(["lid", "lower", "driver"], node_type="nurbsCurve")
		lo_driver_crv = geometrylib.curve.create_curve_link(points, name=name, degree=1)

		points = [in_joint] + lo_joints + [out_joint]
		name = self.format_name(["lid", "lower"], node_type="nurbsCurve")
		lo_crv = geometrylib.curve.create_curve_from_points(points, name=name, degree=1)
		lo_crv = geometrylib.curve.rebuild_curve(lo_crv, spans=self.num_controls + 2)

		cmds.parent(lo_driver_crv, lo_crv, self.noxform_group)

		wire = cmds.wire(lo_crv, w=lo_driver_crv)
		base = cmds.listConnections(wire[0] + ".baseWire")

		constraintslib.matrix_constraint(self.get_rig_group(), lo_crv)
		constraintslib.matrix_constraint(self.get_rig_group(), base[0])
		cmds.setAttr(wire[0] + ".dropoffDistance[0]", 100000000)

		# blink curve
		blink_crv = cmds.duplicate(up_crv, n=self.format_name(["lid", "vlink"], node_type="nurbsCurve"))[0]

		avc = cmds.createNode("avgCurves")
		cmds.connectAttr(up_crv + ".worldSpace", avc + ".inputCurve1")
		cmds.connectAttr(lo_crv + ".worldSpace", avc + ".inputCurve2")
		cmds.connectAttr(avc + ".outputCurve", blink_crv + ".create")
		cmds.setAttr(avc + ".automaticWeight", 0)

		cmds.connectAttr(attr_control_group + ".blinkLineBias", avc + ".weight1")
		attributeslib.connection.reverse_connection(attr_control_group + ".blinkLineBias", avc + ".weight2")

		# ---------------------------------------------------------------------------------------

		# upper eye joint rivets
		joints = [in_joint] + up_joints + [out_joint]

		open_locs = [transformslib.xform.match_locator(j,
		                                               name=j + "_open_GRP",
		                                               node_type="transform",
		                                               parent=self.get_rig_group("parent")) for j in joints]

		closed_locs = [transformslib.xform.match_locator(j,
		                                                 name=j + "_closed_GRP",
		                                                 node_type="transform",
		                                                 parent=self.get_rig_group("parent")) for j in joints]

		aim_locs = [transformslib.xform.match_locator(base_node,
		                                              name=j + "_aim_GRP",
		                                              node_type="transform",
		                                              parent=base_node) for j in joints]

		driver_locs = [transformslib.xform.match_locator(j,
		                                                 name=j + "_driver_GRP",
		                                                 node_type="transform",
		                                                 parent=base_node) for j in joints]

		open_rivets = rivetlib.create_curve_rivet(up_crv, open_locs)
		closed_rivets = rivetlib.create_curve_rivet(blink_crv, closed_locs, maintain_offset=False)

		for orivet, crivet in zip(open_rivets, closed_rivets):
			cmds.setAttr(crivet + ".parameter", cmds.getAttr(orivet + ".parameter"))

		up_blink_adl = cmds.createNode("addDoubleLinear")
		cmds.connectAttr(attr_control_group + ".blink", up_blink_adl + ".input1")
		cmds.connectAttr(attr_control_group + ".upperBlink", up_blink_adl + ".input2")

		clamp = cmds.createNode("clamp")
		cmds.connectAttr(up_blink_adl + ".o", clamp + ".inputR")
		# cmds.connectAttr(clamp + ".outputR", attr_control_group + ".upperBlinkOutput")
		cmds.setAttr(clamp + ".minR", -1)
		cmds.setAttr(clamp + ".maxR", 1)

		rev = attributeslib.connection.reverse_connection(clamp + ".outputR")

		for aim_loc, open_loc, closed_loc, drv, joint in zip(aim_locs, open_locs, closed_locs, driver_locs, joints):
			ac = cmds.aimConstraint(open_loc,
			                        closed_loc,
			                        aim_loc,
			                        aim=[0, 0, 1],
			                        u=[0, 1, 0],
			                        wu=[0, 1, 0],
			                        wuo=base_node,
			                        wut="objectRotation")[0]

			cmds.connectAttr(clamp + ".outputR", ac + ".w1")
			cmds.connectAttr(rev, ac + ".w0")
			cmds.parent(drv, aim_loc)

			constraintslib.matrix_constraint(drv, joint, maintain_offset=True, scale=False)

		# lower eye joint rivets
		joints = lo_joints

		open_locs = [transformslib.xform.match_locator(j,
		                                               name=j + "_open_GRP",
		                                               node_type="transform",
		                                               parent=self.get_rig_group("parent")) for j in joints]

		closed_locs = [transformslib.xform.match_locator(j,
		                                                 name=j + "_closed_GRP",
		                                                 node_type="transform",
		                                                 parent=self.get_rig_group("parent")) for j in joints]

		aim_locs = [transformslib.xform.match_locator(base_node,
		                                              name=j + "_aim_GRP",
		                                              node_type="transform",
		                                              parent=base_node) for j in joints]

		driver_locs = [transformslib.xform.match_locator(j,
		                                                 name=j + "_driver_GRP",
		                                                 node_type="transform",
		                                                 parent=base_node) for j in joints]

		open_rivets = rivetlib.create_curve_rivet(lo_crv, open_locs)
		closed_rivets = rivetlib.create_curve_rivet(blink_crv, closed_locs, maintain_offset=False)

		for orivet, crivet in zip(open_rivets, closed_rivets):
			cmds.setAttr(crivet + ".parameter", cmds.getAttr(orivet + ".parameter"))

		lo_blink_adl = cmds.createNode("addDoubleLinear")
		cmds.connectAttr(attr_control_group + ".blink", lo_blink_adl + ".input1")
		cmds.connectAttr(attr_control_group + ".lowerBlink", lo_blink_adl + ".input2")

		clamp = cmds.createNode("clamp")
		cmds.connectAttr(lo_blink_adl + ".o", clamp + ".inputR")
		# cmds.connectAttr(clamp + ".outputR", attr_control_group + ".lowerBlinkOutput")

		cmds.setAttr(clamp + ".minR", -1)
		cmds.setAttr(clamp + ".maxR", 1)

		rev = attributeslib.connection.reverse_connection(clamp + ".outputR")

		for aim_loc, open_loc, closed_loc, drv, joint in zip(aim_locs, open_locs, closed_locs, driver_locs, joints):
			ac = cmds.aimConstraint(open_loc,
			                        closed_loc,
			                        aim_loc,
			                        aim=[0, 0, 1],
			                        u=[0, 1, 0],
			                        wu=[0, 1, 0],
			                        wuo=base_node,
			                        wut="objectRotation")[0]

			cmds.connectAttr(clamp + ".outputR", ac + ".w1")
			cmds.connectAttr(rev, ac + ".w0")
			cmds.parent(drv, aim_loc)

			constraintslib.matrix_constraint(drv, joint, maintain_offset=True, scale=False)

		# ---------------------------------------------------------------------------------------

		# create eye influence
		oc = cmds.orientConstraint(self.get_rig_group("parent"), self.get_rig_group("eyeJoint"), base_node)[0]
		cmds.setAttr(oc + ".interpType", 2)

		cmds.connectAttr(attr_control_group + ".eyeInfluence", oc + ".w1")
		attributeslib.connection.reverse_connection(attr_control_group + ".eyeInfluence", oc + ".w0")

		constraintslib.matrix_constraint(base_node, up_all_ctrl.groups[-1], scale=False)
		constraintslib.matrix_constraint(base_node, lo_all_ctrl.groups[-1], scale=False)

		# ---------------------------------------------------------------------------------------

		# parent stuff
		cmds.parent(in_ctrl.groups[-1], out_ctrl.groups[-1], self.get_control_group("parent"))
		cmds.parent(up_all_ctrl.groups[-1], lo_all_ctrl.groups[-1], self.get_control_group("parent"))

		# lock stuff
		attributeslib.set_attributes(up_all_ctrl.all_controls, ["s", "v"], lock=True, keyable=False)
		attributeslib.set_attributes(lo_all_ctrl.all_controls, ["s", "v"], lock=True, keyable=False)

		attributeslib.set_attributes([c.path for c in [in_ctrl, out_ctrl] + up_ctrls + lo_ctrls],
		                             ["r", "s", "v", "ro"],
		                             channel_box=False,
		                             lock=True,
		                             keyable=False)

		# hide stuff
		cmds.hide(up_crv, lo_crv, blink_crv, up_driver_crv, lo_driver_crv)
