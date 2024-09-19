# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import geometrylib
from smrig.lib import kinematicslib
from smrig.lib import nodeslib
from smrig.lib import rivetlib
from smrig.lib import spaceslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.neck")


class Neck(basepart.Basepart):
	"""
	spine rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Neck, self).__init__(*guide_node, **options)
		self.register_option("side", "string", "C")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_chest_JNT", value_required=True)
		self.register_option("numJoints", "int", 6, min=1, rebuild_required=True)
		self.register_option("numMidControls", "int", 2, min=1, rebuild_required=True)
		self.register_option("createJaw", "bool", True)

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
		joints = [self.format_name(["neck", i + 1], node_type="joint") for i in range(self.num_joints)]
		joints.append(self.format_name("head", node_type="joint"))
		return joints

	@property
	def create_jaw(self):
		"""

		:return:
		"""
		return self.options.get("createJaw").get("value")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		height = 3.0

		# create neck placers
		spline_placers = self.create_placers(["neck", "spline"],
		                                     num_placers=self.num_mid_controls + 2,
		                                     display_handle=True)

		skull_placer = self.create_placer("skull")
		cmds.parent(skull_placer.groups[-1], spline_placers[-1].path)

		kinematicslib.joint.distribute_chain([p.groups[-1] for p in spline_placers], xform=[0, height, 0])
		cmds.xform(skull_placer.groups[-1], ws=1, t=[0, height + 1, 0])

		div = 1.0 / (len(spline_placers[1:-1]) + 1)
		for i, placer in enumerate(spline_placers[1:-1], 1):
			cmds.pointConstraint(spline_placers[0].path, placer.groups[-1], weight=1.0 - (div * i))
			cmds.pointConstraint(spline_placers[-1].path, placer.groups[-1], weight=div * i)

		# create joints
		joints = self.create_joint_chain("neck", num_joints=self.num_joints)
		joints.append(self.create_joint("head"))
		skull_jnt = self.create_joint("skull")

		cmds.parent(skull_jnt, joints[-1])
		cmds.parent(joints[-1], joints[-2])
		cmds.xform(joints[1:], a=1, t=[0, height / (self.num_joints), 0])

		cmds.joint(joints[0], e=1, oj="xzy", secondaryAxisOrient="zup", ch=1, zso=1)
		cmds.setAttr(skull_jnt + ".jo", 0, 0, 0)
		cmds.parentConstraint(skull_placer.path, skull_jnt, n=skull_jnt + "_PRC")

		# create spline curve
		curve = self.format_name("neck", node_type="nurbsCurve")
		curve = geometrylib.curve.create_curve_link([p.path for p in spline_placers], curve, degree=3)

		# create spline ik
		ik_handle = kinematicslib.ik.create_spline_ik_handle(joints[0], joints[-1], curve=curve)
		cmds.parent(ik_handle[0], self.guide_noxform_group)
		cmds.parent(ik_handle[1], self.guide_geometry_group)

		scale_attribute = self.guide_scale_attribute
		kinematicslib.stretch.create_ik_spline_stretch(ik_handle[1], joints, world_scale_atrtibute=scale_attribute)
		cmds.setAttr("{}.it".format(ik_handle[1]), 0)

		cmds.orientConstraint(spline_placers[-1].path, joints[-1], mo=1)

		# create controls
		head_ctrl = self.create_control("head",
		                                driver=joints[-1],
		                                shape="barrel",
		                                color=self.primary_color,
		                                constraints="pointConstraint",
		                                num_offset_controls=1)

		self.create_control(["neck", "base"],
		                    driver=joints[0],
		                    shape="torso",
		                    scale=-1,
		                    color=self.primary_color,
		                    constraints="pointConstraint",
		                    num_offset_controls=0)

		self.create_controls(["neck", "tangent"],
		                     shape="circle",
		                     constraints="pointConstraint",
		                     color=self.secondary_color,
		                     num=self.num_mid_controls,
		                     drivers=[p.path for p in spline_placers[1:-1]])

		self.create_control("skull",
		                    driver=skull_jnt,
		                    shape="lollipop",
		                    scale=2,
		                    color=self.secondary_color,
		                    constraints="parentConstraint",
		                    num_offset_controls=0)

		cmds.orientConstraint(joints[-1], head_ctrl.groups[-1], mo=1)

		if self.create_jaw:
			jaw_placer = self.create_placer("jaw")
			jaw_end_placer = self.create_placer(["jaw", "end"])

			jaw_joint = self.create_joint("jaw",
			                              constraints="pointConstraint",
			                              placer_driver=jaw_placer.path)

			jaw_end_joint = self.create_joint(["jaw", "end"],
			                                  constraints="pointConstraint",
			                                  placer_driver=jaw_end_placer.path)

			cmds.parent(jaw_end_joint, jaw_joint)
			cmds.parent(jaw_joint, joints[-1])

			cmds.parent(jaw_end_placer.groups[-1], jaw_placer.path)
			cmds.parent(jaw_placer.groups[-1], spline_placers[-1].path)
			cmds.xform(jaw_placer.groups[-1], jaw_end_placer.groups[-1], a=1, t=[0, 0, 1])

			jaw_ctrl = self.create_control("jaw",
			                               driver=jaw_joint,
			                               shape="lollipop",
			                               scale=2,
			                               axis="z",
			                               color=self.secondary_color,
			                               constraints="pointConstraint",
			                               num_offset_controls=0)

			cmds.aimConstraint(jaw_end_placer.path,
			                   jaw_joint,
			                   n=jaw_joint + "_AC",
			                   aim=[1, 0, 0],
			                   u=[0, 1, 0],
			                   wu=[-1, 0, 0],
			                   wut="objectRotation",
			                   wuo=jaw_placer.path)

			cmds.orientConstraint(jaw_joint, jaw_ctrl.groups[-1], mo=1)

		cmds.rename(spline_placers[0], self.format_name(["neck", 1], node_type="jointPlacer"))
		cmds.rename(spline_placers[-1], self.format_name("head", node_type="jointPlacer"))

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""

		neck_base = self.format_name(["neck", "base"], node_type="animControl")
		neck_base = self.create_control_from_guide(neck_base, num_groups=2, animatable_pivot=True)
		cmds.parent(neck_base.groups[-1], self.get_control_group())

		head_ctrl = self.format_name("head", node_type="animControl")
		head_ctrl = self.create_control_from_guide(head_ctrl, num_groups=2, animatable_pivot=True)
		cmds.parent(head_ctrl.groups[-1], neck_base.last_node)

		skull_ctrl = self.format_name("skull", node_type="animControl")
		skull_ctrl = self.create_control_from_guide(skull_ctrl, num_groups=1)
		cmds.parent(skull_ctrl.groups[-1], head_ctrl.last_node)

		if self.create_jaw:
			jaw_ctrl = self.format_name("jaw", node_type="animControl")
			jaw_ctrl = self.create_control_from_guide(jaw_ctrl, num_groups=1)
			cmds.parent(jaw_ctrl.groups[-1], head_ctrl.last_node)

			jaw_jnt = self.format_name("jaw", node_type="joint")
			constraintslib.matrix_constraint(jaw_ctrl.last_node, jaw_jnt, scale=True)
			constraintslib.matrix_constraint(self.joints[-1], jaw_ctrl.groups[-1], scale=True)

		names = [self.format_name(["neck", "tangent", i + 1], node_type="animControl")
		         for i in range(self.num_mid_controls)]

		neck_tangent_ctrls = self.create_controls_from_guide(names, num_groups=2)
		cmds.parent(neck_tangent_ctrls[0].groups[-1], neck_base.last_node)
		cmds.parent(neck_tangent_ctrls[-1].groups[-1], head_ctrl.last_node)

		if self.num_mid_controls > 2:
			mid_tanget_ctrl_groups = [c.groups[-1] for c in neck_tangent_ctrls[1:-1]]
			cmds.parent(mid_tanget_ctrl_groups, self.get_control_group())

			# create mid ctrl spline and rivets
			ct_spline_drivers = [neck_base.last_node,
			                     neck_tangent_ctrls[0].groups[-1],
			                     neck_tangent_ctrls[-1].groups[-1],
			                     head_ctrl.last_node]

			surf = self.format_name("spine", node_type="nurbsSurface")
			surf = geometrylib.nurbs.create_surface_link(ct_spline_drivers, surf, degree=2, parent=self.noxform_group)
			rivetlib.create_surface_rivet(surf, mid_tanget_ctrl_groups)

		# create mid ctrls
		spline_drivers = [neck_base.last_node] + [c.last_node for c in neck_tangent_ctrls] + [head_ctrl.last_node]

		# create curve
		curve = self.format_name("spine", node_type="nurbsCurve")
		curve = geometrylib.curve.create_curve_link(spline_drivers, curve, degree=3)

		# create spline ik
		children = cmds.listRelatives(self.joints[-1]) or []
		if children:
			cmds.parent(children, w=1)

		ik_handle = kinematicslib.ik.create_spline_ik_handle(self.joints[0], self.joints[-1], curve=curve)

		# create twist
		start_loc, end_loc = kinematicslib.ik.create_advanced_twist_locators(ik_handle[0])
		cmds.parent(start_loc, neck_base.last_node)
		cmds.parent(end_loc, head_ctrl.last_node)

		# create stretch
		kinematicslib.stretch.create_ik_spline_stretch(ik_handle[1],
		                                               self.joints,
		                                               control=head_ctrl.path,
		                                               world_scale_atrtibute=self.rig_scale_attribute,
		                                               default_stretch_value=0)

		# connect hip and chest joint rotation
		skull_jnt = self.format_name("skull", node_type="joint")
		constraintslib.matrix_constraint(head_ctrl.last_node, self.joints[-1], translate=False, scale=True)
		constraintslib.matrix_constraint(self.joints[-1], skull_ctrl.groups[-1], scale=True, maintain_offset=True)

		cmds.parent(ik_handle, self.noxform_group)

		if children:
			cmds.parent(children, self.joints[-1])

		constraintslib.matrix_constraint(skull_ctrl.last_node, skull_jnt, maintain_offset=True)

		# uniform scale
		for ctrl in [head_ctrl] + head_ctrl.offset_controls:
			nodeslib.display.create_uniform_scale_link(ctrl.path)

		# lock attrs
		attributeslib.set_attributes([start_loc, end_loc], ["t", "r", "s", "v"], lock=True, keyable=False)
		attributeslib.set_attributes(neck_base.all_controls, ["s"],
		                             lock=True,
		                             keyable=False)

		for ctrl in neck_tangent_ctrls:
			attributeslib.set_attributes(ctrl.all_controls, ["r", "s", "ro"], lock=True, channel_box=False,
			                             keyable=False)

		spc_obj = spaceslib.Space(head_ctrl.path)
		spc_obj.add_target(neck_base.last_node, "neckBase")
		spc_obj.add_target(self.parent, self.parent.replace("C_", "").replace("_JNT", ""))
		spc_obj.set_as_default()
