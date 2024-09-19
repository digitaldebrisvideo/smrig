# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import geometrylib
from smrig.lib import kinematicslib
from smrig.lib import rivetlib
from smrig.lib import spaceslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.spine")


class Spine(basepart.Basepart):
	"""
	spine rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Spine, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_cog_JNT", value_required=True)
		self.register_option("numJoints", "int", 12, min=1, rebuild_required=True)
		self.register_option("numMidControls", "int", 2, min=2, rebuild_required=True)

	@property
	def parent(self):
		"""

		:return:
		"""
		return self.options.get("parent").get("value")

	@property
	def num_mid_controls(self):
		"""

		:return:
		"""
		return self.options.get("numMidControls").get("value")

	@property
	def num_joints(self):
		"""

		:return:
		"""
		return self.options.get("numJoints").get("value")

	@property
	def joints(self):
		"""

		:return:
		"""
		joints = [self.format_name(["spine", i + 1], node_type="joint") for i in range(self.num_joints)]
		joints.append(self.format_name("chest", node_type="joint"))
		joints.insert(0, self.format_name("hip", node_type="joint"))
		return joints

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		height = 5.0

		# create spline placers
		spline_placers = self.create_placers(["spine", "spline"],
		                                     num_placers=self.num_mid_controls + 2,
		                                     display_handle=True)

		kinematicslib.joint.distribute_chain([p.groups[-1] for p in spline_placers], xform=[0, height, 0])

		div = 1.0 / (len(spline_placers[1:-1]) + 1)
		for i, placer in enumerate(spline_placers[1:-1], 1):
			cmds.pointConstraint(spline_placers[0].path, placer.groups[-1], weight=1.0 - (div * i))
			cmds.pointConstraint(spline_placers[-1].path, placer.groups[-1], weight=div * i)

		div = height / (self.num_joints + 1)
		cmds.xform(spline_placers[0].groups[-1], r=1, t=[0, div, 0])

		# create joints
		hip_placer = self.create_placer("hip")
		cmds.parent(hip_placer.groups[-1], spline_placers[0].path)

		joints = self.create_joint_chain("spine", num_joints=self.num_joints)
		joints.insert(0, self.create_joint("hip", placer_driver=hip_placer))
		joints.append(self.create_joint("chest"))

		cmds.parent(joints[1], joints[0])
		cmds.parent(joints[-1], joints[-2])

		cmds.xform(joints[1:], a=1, t=[0, div, 0])
		cmds.joint(joints[0], e=1, oj="xzy", secondaryAxisOrient="zup", ch=1, zso=1)
		cmds.setAttr(joints[-1] + ".jo", 0, 0, 0)

		# create curve
		curve = self.format_name("spine", node_type="nurbsCurve")
		curve = geometrylib.curve.create_curve_link([p.path for p in spline_placers], curve, degree=3)

		# create spline ik
		ik_handle = kinematicslib.ik.create_spline_ik_handle(joints[1], joints[-1], curve=curve)
		cmds.parent(ik_handle, self.guide_noxform_group)

		scale_attribute = self.guide_scale_attribute
		kinematicslib.stretch.create_ik_spline_stretch(ik_handle[1], joints[1:], world_scale_atrtibute=scale_attribute)

		# create controls
		self.create_control("chest",
		                    driver=joints[-1],
		                    shape="torso",
		                    color=self.primary_color,
		                    constraints="pointConstraint",
		                    num_offset_controls=1)

		self.create_control("hip",
		                    driver=joints[1],
		                    shape="torso",
		                    scale=-1,
		                    num_offset_controls=1,
		                    color=self.primary_color,
		                    constraints="pointConstraint")

		self.create_control(["hip", "tangent"],
		                    shape="circle",
		                    color=self.secondary_color,
		                    constraints="pointConstraint",
		                    driver=spline_placers[1].path)

		self.create_control(["chest", "tangent"],
		                    shape="circle",
		                    color=self.secondary_color,
		                    constraints="pointConstraint",
		                    create_offset_controls=False,
		                    driver=spline_placers[-2].path)

		if self.num_mid_controls > 2:
			self.create_controls(["torso", "tangent"],
			                     shape="circle",
			                     constraints="pointConstraint",
			                     create_offset_controls=False,
			                     color=self.secondary_color,
			                     num=self.num_mid_controls - 2,
			                     drivers=[p.path for p in spline_placers[2:-2]])

		cmds.rename(spline_placers[0], self.format_name(["spine", 1], node_type="jointPlacer"))
		cmds.rename(spline_placers[-1], self.format_name("chest", node_type="jointPlacer"))

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		chest_ctrl = self.format_name("chest", node_type="animControl")
		chest_ctrl = self.create_control_from_guide(chest_ctrl, num_groups=2, animatable_pivot=True)
		cmds.parent(chest_ctrl.groups[-1], self.get_control_group())

		hip_ctrl = self.format_name("hip", node_type="animControl")
		hip_ctrl = self.create_control_from_guide(hip_ctrl, num_groups=2, animatable_pivot=True)
		cmds.parent(hip_ctrl.groups[-1], self.get_control_group())

		chest_tangent_ctrl = self.format_name(["chest", "tangent"], node_type="animControl")
		chest_tangent_ctrl = self.create_control_from_guide(name=chest_tangent_ctrl, num_groups=2)
		cmds.parent(chest_tangent_ctrl.groups[-1], chest_ctrl.last_node)

		hip_tangent_ctrl = self.format_name(["hip", "tangent"], node_type="animControl")
		hip_tangent_ctrl = self.create_control_from_guide(hip_tangent_ctrl, num_groups=2)
		cmds.parent(hip_tangent_ctrl.groups[-1], hip_ctrl.last_node)

		# create mid ctrls
		spline_drivers = [hip_ctrl.last_node, hip_tangent_ctrl.last_node]
		if self.num_mid_controls > 2:
			mid_torso_ctrls = [self.format_name(["torso", "tangent", i + 1], node_type="animControl")
			                   for i in range(self.num_mid_controls - 2)]

			mid_torso_ctrls = self.create_controls_from_guide(mid_torso_ctrls, num_groups=2)
			cmds.parent([c.groups[-1] for c in mid_torso_ctrls], self.get_control_group())
			spline_drivers.extend([c.last_node for c in mid_torso_ctrls])

			for ctrl in mid_torso_ctrls:
				attributeslib.set_attributes(ctrl.all_controls, ["r", "s", "ro"], lock=True, keyable=False)

			# create mid ctrls
			ct_spline_drivers = [hip_ctrl.last_node,
			                     hip_tangent_ctrl.groups[-1],
			                     chest_tangent_ctrl.groups[-1],
			                     chest_ctrl.last_node]

			surf = self.format_name("spine", node_type="nurbsSurface")
			surf = geometrylib.nurbs.create_surface_link(ct_spline_drivers, surf, degree=2, parent=self.noxform_group)
			rivetlib.create_surface_rivet(surf, [c.groups[-1] for c in mid_torso_ctrls])

		spline_drivers.extend([chest_tangent_ctrl.last_node, chest_ctrl.last_node])

		# create curve
		curve = self.format_name("spine", node_type="nurbsCurve")
		curve = geometrylib.curve.create_curve_link(spline_drivers, curve, degree=3)

		# create spline ik
		# create spline ik
		children = cmds.listRelatives(self.joints[-1]) or []
		if children:
			cmds.parent(children, w=1)

		ik_handle = kinematicslib.ik.create_spline_ik_handle(self.joints[1], self.joints[-1], curve=curve)

		# create twist
		start_loc, end_loc = kinematicslib.ik.create_advanced_twist_locators(ik_handle[0])
		cmds.parent(start_loc, hip_ctrl.last_node)
		cmds.parent(end_loc, chest_ctrl.last_node)

		# create stretch
		kinematicslib.stretch.create_ik_spline_stretch(ik_handle[1],
		                                               self.joints[1:],
		                                               control=chest_ctrl.path,
		                                               world_scale_atrtibute=self.rig_scale_attribute,
		                                               default_stretch_value=0)
		# connect hip and chest joint rotation
		constraintslib.matrix_constraint(hip_ctrl.last_node, self.joints[0], scale=False)
		constraintslib.matrix_constraint(chest_ctrl.last_node, self.joints[-1], translate=False, scale=False)
		cmds.parent(ik_handle, self.noxform_group)

		if children:
			cmds.parent(children, self.joints[-1])

		# lock attrs
		attributeslib.set_attributes([start_loc, end_loc], ["t", "r", "s", "v"], lock=True, keyable=False)
		attributeslib.set_attributes(chest_ctrl.all_controls, ["s"], lock=True, keyable=False)
		attributeslib.set_attributes(hip_ctrl.all_controls, ["s"], lock=True, keyable=False)
		attributeslib.set_attributes(chest_tangent_ctrl.all_controls, ["r", "s", "ro"], lock=True, keyable=False)
		attributeslib.set_attributes(hip_tangent_ctrl.all_controls, ["r", "s", "ro"], lock=True, keyable=False)

		# spaces
		spc_obj = spaceslib.Space(chest_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()

		spc_obj = spaceslib.Space(hip_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()
