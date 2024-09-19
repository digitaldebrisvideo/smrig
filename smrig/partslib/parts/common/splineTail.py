# -*- smrig: part  -*-

# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import geometrylib
from smrig.lib import kinematicslib
from smrig.lib import rivetlib
from smrig.lib import spaceslib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.splineChain")


class SplineTail(basepart.Basepart):
	"""
	splineChain rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(SplineTail, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "myChain", value_required=True)
		self.register_option("parent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("numControls", "int", 8, min=4, value_required=True, rebuild_required=True)
		self.register_option("numFkOffsetControls", "int", 15, min=-1, value_required=False, rebuild_required=True)
		self.register_option("numJoints", "int", 30, min=2, value_required=True, rebuild_required=True)
		self.register_option("stretchMode", "enum", "nonUniform", enum="nonUniform:squash")
		self.register_option("squashModeStableAxis", "enum", "Y", enum="Y:Z")
		self.register_option("preserveVolume", "bool", True)
		self.register_option("createScaleControls", "bool", True)
		self.register_option("createSpaces", "bool", True)

	@property
	def stretch_mode(self):
		"""

		:return:
		"""
		return self.options.get("stretchMode").get("value")

	@property
	def stable_axis(self):
		"""

		:return:
		"""
		return self.options.get("squashModeStableAxis").get("value")

	@property
	def create_scale(self):
		"""

		:return:
		"""
		return self.options.get("createScaleControls").get("value")

	@property
	def preserve_volume(self):
		"""

		:return:
		"""
		return self.options.get("preserveVolume").get("value")

	@property
	def num_controls(self):
		"""

		:return:
		"""
		return self.options.get("numControls").get("value")

	@property
	def num_fk_offset_controls(self):
		"""

		:return:
		"""
		return self.options.get("numFkOffsetControls").get("value")

	@property
	def num_joints(self):
		"""

		:return:
		"""
		return self.options.get("numJoints").get("value")

	@property
	def create_spaces(self):
		"""

		:return:
		"""
		return self.options.get("createSpaces").get("value")

	@property
	def controls(self):
		"""

		:return:
		"""
		return [self.format_name(["", i + 1], node_type="animControl") for i in range(self.num_controls)]

	@property
	def fk_offset_controls(self):
		"""

		:return:
		"""
		return [self.format_name(["fk", "offset", i + 1], node_type="animControl") for i in
		        range(self.num_fk_offset_controls)]

	@property
	def joints(self):
		"""

		:return:
		"""
		return [self.format_name(["", i + 1], node_type="joint") for i in range(self.num_joints)]

	@property
	def parent(self):
		"""
		:return:
		"""
		return self.options.get("parent").get("value")

	def build_guide(self):
		"""
		:return:
		"""

		height = 10.0

		# create spline placers
		spline_placers = self.create_placers(["", "spline"],
		                                     num_placers=self.num_controls,
		                                     display_handle=True)

		kinematicslib.joint.distribute_chain([p.groups[-1] for p in spline_placers], xform=[0, 0, -height])

		# create joints
		joints = self.create_joint_chain("", num_joints=self.num_joints)

		cmds.xform(joints[1:], a=1, t=[0, 0, -(height / (self.num_joints - 1))])
		cmds.joint(joints[0], e=1, oj="xzy", secondaryAxisOrient="zup", ch=1, zso=1)
		cmds.setAttr(joints[-1] + ".jo", 0, 0, 0)

		# create curve
		curve = self.format_name("", node_type="nurbsCurve")
		curve = geometrylib.curve.create_curve_link([p.path for p in spline_placers], curve, degree=3)

		# create spline ik
		ik_handle = kinematicslib.ik.create_spline_ik_handle(joints[0], joints[-1], curve=curve)
		cmds.parent(ik_handle, self.guide_noxform_group)

		scale_attribute = self.guide_scale_attribute
		kinematicslib.stretch.create_ik_spline_stretch(ik_handle[1], joints, world_scale_atrtibute=scale_attribute)

		# create ctrls
		self.create_controls("",
		                     num=self.num_controls,
		                     drivers=spline_placers,
		                     color=self.primary_color,
		                     axis="z",
		                     num_offset_controls=1,
		                     shape="square")

		# create fk offset ctrls
		num_fk_offsets = self.num_joints if self.num_fk_offset_controls == -1 else self.num_fk_offset_controls
		if num_fk_offsets:
			fk_driver_joints = joints[-num_fk_offsets:]

			self.create_controls(["fk", "offset"],
			                     num=num_fk_offsets,
			                     drivers=fk_driver_joints,
			                     color=self.secondary_color,
			                     axis="y",
			                     create_offset_controls=False,
			                     shape="lollipop")

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		joints = self.joints
		controls = self.create_control_chain_from_guide(self.controls, num_groups=2)
		fk_offset_controls = self.create_control_chain_from_guide(self.fk_offset_controls, num_groups=2)

		# create spline nodes oriented based on joint
		spline_drivers = []
		for ctrl in controls:
			grp = cmds.createNode("transform", p=ctrl.last_node, n=ctrl.last_node + "_spline_GRP")
			transformslib.xform.match(get_closest_joint(grp, joints), grp, translate=False, scale=False)
			spline_drivers.append(grp)

		# create curve
		curve = self.format_name("", node_type="nurbsCurve")
		curve = geometrylib.curve.create_curve_link(spline_drivers, curve, degree=3)

		# create surface
		surf = self.format_name("", node_type="nurbsSurface")
		surf = geometrylib.nurbs.create_surface_link(spline_drivers,
		                                             surf,
		                                             axis="z",
		                                             degree=3,
		                                             parent=self.noxform_group)

		# create ik chain
		ik_joints = kinematicslib.joint.duplicate_chain(joints)

		cmds.parent(ik_joints[0], self.get_rig_group())

		ik_handle, curve = kinematicslib.ik.create_spline_ik_handle(ik_joints[0], ik_joints[-1], curve=curve)
		cmds.parent(curve, self.noxform_group)

		# connect non uniform stretch
		if self.stretch_mode == "nonUniform":
			non_uniform_ik_joints = kinematicslib.stretch.create_nonuniform_stretch_nodes(curve,
			                                                                              ik_joints,
			                                                                              mirror_value=self.mirror_value)
		else:
			non_uniform_ik_joints = None

		kinematicslib.stretch.create_ik_spline_stretch(curve,
		                                               ik_joints,
		                                               control=controls[0].path,
		                                               world_scale_atrtibute=self.rig_scale_attribute,
		                                               default_stretch_value=0,
		                                               non_uniform_joints=non_uniform_ik_joints)

		# constrain non fk ctrl joints to ik joints and normal constrain to surf
		for i, joint in enumerate(joints[:-self.num_fk_offset_controls]):
			constraintslib.matrix_constraint(ik_joints[i], joint, translate=True, rotate=False, scale=False)
			rivetlib.create_surface_rivet(surf, joint, driver=ik_joints[i], translate=False, rotate=True)

		# create fk offset group nodes
		fk_offset_nodes = [cmds.createNode("transform", p=g.groups[-1], n=g.groups[-1] + "_fk_offset_GRP") for g in
		                   fk_offset_controls]

		for i, node in enumerate(fk_offset_nodes[1:], 1):
			cmds.parent(node, fk_offset_nodes[i - 1])

		cmds.parent(controls[0].groups[-1],
		            fk_offset_controls[0].groups[-1],
		            fk_offset_nodes[0],
		            self.get_control_group())

		# rivet and constraint fk group nodes
		driven_ik_joints = ik_joints[self.num_joints - self.num_fk_offset_controls:]
		driven_joints = joints[self.num_joints - self.num_fk_offset_controls:]

		aim_up_grp = self.create_node("transform", name=["aim", "ups"], parent=self.get_rig_group())

		for i, ctrl in enumerate(fk_offset_controls):
			ik_joint = driven_ik_joints[i]
			upv = cmds.duplicate(fk_offset_nodes[i], n=fk_offset_nodes[i] + "_upv", po=True)[0]
			cmds.parent(upv, aim_up_grp)

			constraintslib.matrix_constraint(ik_joint,
			                                 fk_offset_nodes[i],
			                                 translate=True,
			                                 rotate=False,
			                                 scale=False)

			if self.stretch_mode == "squash" and i < len(fk_offset_controls[:-1]):
				rivetlib.create_surface_rivet(surf,
				                              upv,
				                              driver=ik_joint,
				                              translate=True,
				                              rotate=True)

				stable = [0, 0, 1] if self.stable_axis == "Y" else [0, 1, 0]
				cmds.aimConstraint(ik_joints[i + 1],
				                   fk_offset_nodes[i],
				                   aim=[self.mirror_value, 0, 0],
				                   u=stable,
				                   wu=stable,
				                   wuo=upv,
				                   mo=True,
				                   wut="objectRotation")
			else:
				rivetlib.create_surface_rivet(surf,
				                              fk_offset_nodes[i],
				                              driver=ik_joint,
				                              translate=False,
				                              rotate=True)

			constraintslib.matrix_constraint(ctrl.last_node,
			                                 driven_joints[i],
			                                 translate=True,
			                                 rotate=True,
			                                 scale=False)

			cmds.connectAttr(fk_offset_nodes[i] + ".t", ctrl.groups[-1] + ".t")
			cmds.connectAttr(fk_offset_nodes[i] + ".r", ctrl.groups[-1] + ".r")

		# distributed scale
		if self.create_scale:
			kinematicslib.scale.create_ramp_scale([c.path for c in controls], joints)

		# hide and lock stuff
		cmds.parent(ik_handle, self.noxform_group)
		cmds.hide(ik_joints[0], ik_handle)

		for control in controls + fk_offset_controls:
			attributeslib.set_attributes(control.all_controls, ["s"], lock=True, keyable=False)

		# remove last shape fk offset ctrl shape
		cmds.delete(fk_offset_controls[-1].shapes)
		attributeslib.set_attributes(fk_offset_controls[-1].path, ["t", "r", "s"], lock=True, keyable=False)

		# create spaces
		if self.create_spaces:
			for i, control in enumerate(controls):
				spc_obj = spaceslib.Space(control.path)

				if i > 0:
					spc_obj.add_target(controls[i - 1].path, "parentControl")
					spc_obj.add_target(self.parent, "parent")
				else:
					spc_obj.add_target(self.parent, "parent")

				spc_obj.set_as_default()


def get_closest_joint(node, joints):
	"""

	:param node:
	:param joints:
	:return:
	"""
	distances = {utilslib.distance.get(node, j): j for j in joints}
	key_list = list(distances.keys())
	key_list.sort()

	return distances.get(key_list[0])
