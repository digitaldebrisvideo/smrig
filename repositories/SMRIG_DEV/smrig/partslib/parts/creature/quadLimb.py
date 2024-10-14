# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
import maya.mel as mel
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import kinematicslib
from smrig.lib import selectionlib
from smrig.lib import spaceslib
from smrig.lib import transformslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.quadLeg")

mel.eval("ikSpringSolver")


class QuadLimb(basepart.Basepart):
	"""
	quadLeg rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(QuadLimb, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "rear")
		self.register_option("parent", "parent_driver", "C_hip_JNT", value_required=True)
		self.register_option("numTwistJoints", "int", 4, min=0, rebuild_required=True)

		self.register_option("createSoftIK", "bool", True)
		self.register_option("createStretch", "bool", True)
		self.register_option("createBendy", "bool", True)
		self.register_option("limbStyle", "enum", "quadLeg", enum="quadLeg:quadArm")

	@property
	def parent(self):
		"""
		:return:
		"""
		return self.options.get("parent").get("value")

	@property
	def limb_style(self):
		"""
		:return:
		"""
		return self.options.get("limbStyle").get("value")

	@property
	def num_twist_joints(self):
		"""
		:return:
		"""
		return self.options.get("numTwistJoints").get("value")

	@property
	def create_soft_ik(self):
		"""
		:return:
		"""
		return self.options.get("createSoftIK").get("value")

	@property
	def create_stretch(self):
		"""
		:return:
		"""
		return self.options.get("createBendy").get("value")

	@property
	def thigh_joints(self):
		"""
		:return:
		"""
		return [self.format_name(["thigh", i + 1], node_type="joint") for i in range(self.num_twist_joints + 1)]

	@property
	def lo_knee_joints(self):
		"""
		:return:
		"""
		return [self.format_name(["knee", "lower", i + 1], node_type="joint") for i in
		        range(self.num_twist_joints + 1)]

	@property
	def foot_part_required_nodes(self):
		"""
		This method returns all required nodes to build a foot part


		:return:
		"""
		return [self.format_name(["ankle", "ik"], node_type="joint"),
		        self.format_name("ankle", node_type="joint"),
		        controlslib.Control(self.format_name(["leg", "ik"], node_type="animControl")),
		        controlslib.Control(self.format_name(["ankle", "fk"], node_type="animControl")),
		        controlslib.Control(self.format_name(["leg", "settings"], node_type="animControl"))]

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		thigh_placer = self.create_placer(["thigh", 1])
		up_knee_placer = self.create_placer("knee")
		lo_knee_placer = self.create_placer(["knee", "lower", 1])
		ankle_placer = self.create_placer("ankle")

		cmds.xform(up_knee_placer.groups[-1], t=[0, -2, 1])
		cmds.xform(lo_knee_placer.groups[-1], t=[0, -4, -1])
		cmds.xform(ankle_placer.groups[-1], t=[0, -6, 0])

		# create joints
		thigh_joints = self.create_joint_chain("thigh", num_joints=self.num_twist_joints + 1)
		up_knee_joint = self.create_joint("knee", placer_driver=up_knee_placer, constraints="pointConstraint")
		lo_knee_joints = self.create_joint_chain(["knee", "lower"], num_joints=self.num_twist_joints + 1)
		ankle_joint = self.create_joint("ankle", placer_driver=ankle_placer, constraints="pointConstraint")

		cmds.parent(up_knee_joint, thigh_joints[-1])
		cmds.parent(lo_knee_joints[0], up_knee_joint)
		cmds.parent(ankle_joint, lo_knee_joints[-1])

		# constrain joints
		cmds.pointConstraint(thigh_placer.path, thigh_joints[0])
		cmds.pointConstraint(lo_knee_placer.path, lo_knee_joints[0])

		cmds.aimConstraint(up_knee_placer.path,
		                   thigh_joints[0],
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, self.mirror_value],
		                   wut="object",
		                   wuo=ankle_placer.path)

		cmds.aimConstraint(ankle_placer.path,
		                   lo_knee_joints[0],
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, -self.mirror_value],
		                   wut="object",
		                   wuo=thigh_placer.path)

		cmds.aimConstraint(lo_knee_placer.path,
		                   up_knee_joint,
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, self.mirror_value],
		                   wut="object",
		                   wuo=thigh_placer.path)

		if self.num_twist_joints:
			for i, twist_jnt in enumerate(thigh_joints[1:], 1):
				div = 1.0 / (self.num_twist_joints + 1)
				cmds.pointConstraint(thigh_placer.path, twist_jnt, weight=1.0 - (div * i))
				cmds.pointConstraint(up_knee_placer.path, twist_jnt, weight=(div * i))

			for i, twist_jnt in enumerate(lo_knee_joints[1:], 1):
				div = 1.0 / (self.num_twist_joints + 1)
				cmds.pointConstraint(lo_knee_placer.path, twist_jnt, weight=1.0 - (div * i))
				cmds.pointConstraint(ankle_placer.path, twist_jnt, weight=(div * i))

		# fk controls
		self.create_control(["thigh", "fk"],
		                    shape="circle",
		                    color=self.primary_color,
		                    driver=thigh_joints[0],
		                    axis="x")

		self.create_control(["knee", "fk"],
		                    shape="circle",
		                    color=self.primary_color,
		                    driver=up_knee_joint,
		                    axis="x")

		self.create_control(["knee", "lower", "fk"],
		                    shape="circle",
		                    color=self.primary_color,
		                    driver=lo_knee_joints[0],
		                    axis="x")

		self.create_control(["ankle", "fk"],
		                    shape="circle",
		                    color=self.primary_color,
		                    driver=ankle_joint,
		                    axis="x")

		# ik controls
		ctrl = self.create_control(["leg", "ik"],
		                           shape="cube",
		                           color=self.primary_color,
		                           driver=ankle_joint,
		                           num_offset_controls=1,
		                           scale=0.75,
		                           axis="x")

		self.create_control(["leg", "settings"],
		                    shape="flag",
		                    color=self.detail_color,
		                    driver=ankle_joint,
		                    create_offset_controls=False,
		                    axis="y",
		                    scale=-1)

		pv_ctrl = self.create_control(["leg", "pv"],
		                              shape="cube",
		                              color=self.primary_color,
		                              create_offset_controls=False,
		                              locked_pivot_attrs=["r", "s"],
		                              axis="z",
		                              scale=0.25)

		self.create_control(["knee", "lower", "ik"],
		                    shape="cube",
		                    color=self.secondary_color,
		                    create_offset_controls=False,
		                    driver=lo_knee_joints[0],
		                    scale=0.25)

		cmds.xform(pv_ctrl.groups[0], a=1, t=[0, 0, 10])
		cmds.pointConstraint(thigh_joints[0], ankle_joint, pv_ctrl.groups[-1])

		cmds.aimConstraint(ankle_joint,
		                   pv_ctrl.groups[-1],
		                   aim=[1, 0, 0],
		                   u=[0, 0, 1],
		                   wut="object",
		                   wuo=up_knee_placer)

		attributeslib.set_attributes(pv_ctrl.path, ["ty"], lock=True, keyable=False)
		cmds.xform(ctrl.groups[0], a=1, ro=[180, 0, -90])

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		thigh_joints = self.thigh_joints
		lo_knee_joints = self.lo_knee_joints
		up_knee_joint = self.format_name("knee", node_type="joint")
		ankle_joint = self.format_name("ankle", node_type="joint")

		leg_ik_ctrl = self.create_control_from_guide(self.format_name(["leg", "ik"],
		                                                              node_type="animControl"), node_type="joint")

		leg_pv_ctrl = self.create_control_from_guide(self.format_name(["leg", "pv"],
		                                                              node_type="animControl"),
		                                             center_pivot_on_control=True)

		settings_ctrl = self.create_control_from_guide(self.format_name(["leg", "settings"],
		                                                                node_type="animControl"), num_groups=0)

		thigh_fk_ctrl = self.create_control_from_guide(self.format_name(["thigh", "fk"],
		                                                                node_type="animControl"))

		up_knee_fk_ctrl = self.create_control_from_guide(self.format_name(["knee", "fk"],
		                                                                  node_type="animControl"))

		lo_knee_fk_ctrl = self.create_control_from_guide(self.format_name(["knee", "lower", "fk"],
		                                                                  node_type="animControl"))

		lo_knee_ik_ctrl = self.create_control_from_guide(self.format_name(["knee", "lower", "ik"],
		                                                                  node_type="animControl"),
		                                                 translate=ankle_joint, rotate=ankle_joint)

		ankle_fk_ctrl = self.create_control_from_guide(self.format_name(["ankle", "fk"],
		                                                                node_type="animControl"))

		geometrylib.curve.create_curve_link([leg_pv_ctrl.path, up_knee_joint], parent=leg_pv_ctrl.path)

		# constrain and orient controls
		zero_grp = leg_ik_ctrl.groups[-1]
		parent_grp = leg_ik_ctrl.groups[0]
		cmds.parent(leg_ik_ctrl, w=1)
		tmp_par = selectionlib.get_parent(leg_ik_ctrl)
		cmds.xform(zero_grp, a=1, ro=[0, 180, 0] if self.mirror_value == -1 else [0, 0, 0])
		cmds.parent(leg_ik_ctrl, parent_grp)
		cmds.makeIdentity(leg_ik_ctrl, apply=1, r=1, n=0, pn=1)

		if tmp_par:
			cmds.delete(tmp_par)

		cmds.xform(leg_pv_ctrl.groups[-1], ws=1, ro=cmds.xform(leg_ik_ctrl.groups[-1], q=1, ws=1, ro=1))
		cmds.xform(leg_pv_ctrl.groups[-1], a=1, s=cmds.xform(leg_ik_ctrl.groups[-1], q=1, r=1, s=1))

		zero_grp = lo_knee_ik_ctrl.groups[-1]
		offset_grp = lo_knee_ik_ctrl.groups[0]
		cmds.parent(lo_knee_ik_ctrl, w=1)
		transformslib.xform.match(leg_ik_ctrl.path, zero_grp)
		cmds.parent(lo_knee_ik_ctrl, offset_grp)
		cmds.makeIdentity(lo_knee_ik_ctrl, apply=1, r=1, n=0, pn=1)

		constraintslib.matrix_constraint(ankle_joint, settings_ctrl.path, maintain_offset=True)

		# parent controls
		cmds.parent(up_knee_fk_ctrl.groups[-1], thigh_fk_ctrl.last_node)
		cmds.parent(lo_knee_fk_ctrl.groups[-1], up_knee_fk_ctrl.last_node)
		cmds.parent(ankle_fk_ctrl.groups[-1], lo_knee_fk_ctrl.last_node)

		cmds.parent(leg_ik_ctrl.groups[-1],
		            lo_knee_ik_ctrl.groups[-1],
		            leg_pv_ctrl.groups[-1],
		            thigh_fk_ctrl.groups[-1],
		            settings_ctrl.path,
		            self.get_control_group())

		# animatable pivoits
		controlslib.create_animatable_pivot(leg_ik_ctrl)

		# add attrs
		cmds.addAttr(leg_ik_ctrl, ln="springBias", k=1, min=-1, max=1)
		cmds.addAttr(leg_ik_ctrl, ln="twist", k=1)
		cmds.addAttr(leg_ik_ctrl, ln="thighTwist", k=1)

		# create ik chain
		prime_ik_joints = [
			cmds.duplicate(thigh_joints[0], n=self.format_name(["leg", "prime", "ik"], node_type="joint"), po=1)[0],
			cmds.duplicate(up_knee_joint, n=self.format_name(["knee", "prime", "ik"], node_type="joint"), po=1)[0],
			cmds.duplicate(lo_knee_joints[0], n=self.format_name(["knee", "lower", "prime", "ik"], node_type="joint"),
			               po=1)[0],
			cmds.duplicate(ankle_joint, n=self.format_name(["ankle", "prime", "ik"], node_type="joint"), po=1)[0],

		]

		ik_joints = [
			cmds.duplicate(thigh_joints[0], n=self.format_name(["leg", "ik"], node_type="joint"), po=1)[0],
			cmds.duplicate(up_knee_joint, n=self.format_name(["knee", "ik"], node_type="joint"), po=1)[0],
			cmds.duplicate(lo_knee_joints[0], n=self.format_name(["knee", "lower", "ik"], node_type="joint"), po=1)[0],
			cmds.duplicate(ankle_joint, n=self.format_name(["ankle", "ik"], node_type="joint"), po=1)[0],

		]

		for i in range(1, len(prime_ik_joints)):
			cmds.parent(prime_ik_joints[i], prime_ik_joints[i - 1])

		for i in range(1, len(ik_joints)):
			cmds.parent(ik_joints[i], ik_joints[i - 1])

		cmds.parent(ik_joints[0], self.get_rig_group())
		cmds.parent(prime_ik_joints[0], self.noxform_group)

		# connect fk rotations
		cmds.connectAttr(thigh_fk_ctrl.last_node + ".r", ik_joints[0] + ".r")
		cmds.connectAttr(up_knee_fk_ctrl.last_node + ".r", ik_joints[1] + ".r")
		cmds.connectAttr(lo_knee_fk_ctrl.last_node + ".r", ik_joints[2] + ".r")

		cmds.connectAttr(thigh_fk_ctrl.last_node + ".ro", ik_joints[0] + ".ro")
		cmds.connectAttr(up_knee_fk_ctrl.last_node + ".ro", ik_joints[1] + ".ro")
		cmds.connectAttr(lo_knee_fk_ctrl.last_node + ".ro", ik_joints[2] + ".ro")
		cmds.connectAttr(ankle_fk_ctrl.last_node + ".ro", ik_joints[3] + ".ro")

		constraintslib.matrix_constraint(thigh_fk_ctrl.last_node, prime_ik_joints[0], maintain_offset=True)
		cmds.connectAttr(up_knee_fk_ctrl.last_node + ".r", prime_ik_joints[1] + ".r")
		cmds.connectAttr(lo_knee_fk_ctrl.last_node + ".r", prime_ik_joints[2] + ".r")

		constraintslib.matrix_constraint(leg_ik_ctrl.last_node,
		                                 ik_joints[3],
		                                 maintain_offset=True,
		                                 translate=False,
		                                 rotate=True,
		                                 scale=False)

		end_joint_rotate_bcl = cmds.createNode("blendColors")
		cnn = cmds.listConnections(ik_joints[3] + ".r", p=True)

		cmds.connectAttr(ankle_fk_ctrl.path + ".r", end_joint_rotate_bcl + ".color2")
		cmds.connectAttr(cnn[0], end_joint_rotate_bcl + ".color1")
		cmds.connectAttr(end_joint_rotate_bcl + ".output", ik_joints[3] + ".r", f=True)

		# create prime ik handle
		leg_ik = kinematicslib.ik.create_ik_handle(prime_ik_joints[0], prime_ik_joints[3], solver="Spring")
		cmds.poleVectorConstraint(leg_pv_ctrl.last_node, leg_ik)

		twist_value = kinematicslib.ik.align_ik_twist(ik_joints[1], prime_ik_joints[1], leg_ik)

		leg_ik_grp = cmds.createNode("transform", n=leg_ik + "_GRP")
		cmds.parent(leg_ik, leg_ik_grp)
		cmds.parent(leg_ik_grp, leg_ik_ctrl.last_node)

		if self.mirror_value == 1:
			attributeslib.connection.add_connection("{}.twist".format(leg_ik_ctrl.path),
			                                        target_plug=leg_ik + ".twist",
			                                        add_value=twist_value)
		else:
			attributeslib.connection.add_connection(
				attributeslib.connection.negative_connection("{}.twist".format(leg_ik_ctrl.path)),
				target_plug=leg_ik + ".twist",
				add_value=twist_value)

		# SDK spring bias
		cmds.setDrivenKeyframe("{}.springAngleBias[0].springAngleBias_FloatValue".format(leg_ik),
		                       cd=leg_ik_ctrl.path + ".springBias", dv=-1, v=0)
		cmds.setDrivenKeyframe("{}.springAngleBias[0].springAngleBias_FloatValue".format(leg_ik),
		                       cd=leg_ik_ctrl.path + ".springBias", dv=1, v=1)
		cmds.setDrivenKeyframe("{}.springAngleBias[1].springAngleBias_FloatValue".format(leg_ik),
		                       cd=leg_ik_ctrl.path + ".springBias", dv=-1, v=1)
		cmds.setDrivenKeyframe("{}.springAngleBias[1].springAngleBias_FloatValue".format(leg_ik),
		                       cd=leg_ik_ctrl.path + ".springBias", dv=1, v=0)

		# create ik handles
		thigh_ik = kinematicslib.ik.create_ik_handle(ik_joints[0], ik_joints[2], solver="RP")
		knee_ik = kinematicslib.ik.create_ik_handle(ik_joints[2], ik_joints[3], solver="SC")

		# pole vector
		lo_pv_node = self.create_node("transform", ["knee", "lower", "pv"], p=prime_ik_joints[0])
		cmds.xform(lo_pv_node, a=1, t=[0, cmds.getAttr(prime_ik_joints[1] + ".tx") * 2, 0])

		cmds.poleVectorConstraint(lo_pv_node, thigh_ik)
		twist_value = kinematicslib.ik.align_ik_twist(prime_ik_joints[1], ik_joints[1], thigh_ik)

		# connect twist thigh
		if self.mirror_value == 1:
			attributeslib.connection.add_connection("{}.thighTwist".format(leg_ik_ctrl.path),
			                                        target_plug=thigh_ik + ".twist",
			                                        add_value=twist_value)
		else:
			attributeslib.connection.add_connection(
				attributeslib.connection.negative_connection("{}.thighTwist".format(leg_ik_ctrl.path)),
				target_plug=thigh_ik + ".twist",
				add_value=twist_value)

		thigh_ik_grp = cmds.createNode("transform", n=thigh_ik + "_GRP")
		cmds.parent(thigh_ik, thigh_ik_grp)

		knee_ik_grp = cmds.createNode("transform", n=knee_ik + "_GRP")
		cmds.parent(knee_ik, knee_ik_grp)

		cmds.parent(thigh_ik_grp, lo_knee_ik_ctrl.last_node)
		cmds.parent(knee_ik_grp, prime_ik_joints[3])

		# connect lo knee ik ctrl
		constraintslib.matrix_constraint(prime_ik_joints[-1],
		                                 lo_knee_ik_ctrl.groups[-1],
		                                 maintain_offset=True)

		attributeslib.connection.add_connection(prime_ik_joints[-1] + ".tx",
		                                        add_value=-cmds.getAttr(prime_ik_joints[-1] + ".tx"),
		                                        target_plug=lo_knee_ik_ctrl.groups[1] + ".ty")

		attributeslib.connection.negative_connection(lo_knee_ik_ctrl.groups[1] + ".ty",
		                                             lo_knee_ik_ctrl.path + ".rotatePivotY")
		attributeslib.connection.negative_connection(lo_knee_ik_ctrl.groups[1] + ".ty",
		                                             lo_knee_ik_ctrl.path + ".scalePivotY")

		# create switch
		fk_controls = [thigh_fk_ctrl.path]
		ik_controls = [leg_ik_ctrl.path, leg_pv_ctrl.path, lo_knee_ik_ctrl.path]
		kinematicslib.ik.create_fk_ik_switch(settings_ctrl.path, [leg_ik, thigh_ik, knee_ik], fk_controls, ik_controls)
		cmds.connectAttr(settings_ctrl.path + ".ikBlend", end_joint_rotate_bcl + ".blender")

		# twist
		if self.num_twist_joints:
			kinematicslib.joint_twist.upper_twist(self.get_rig_group(), ik_joints[0:2], self.thigh_joints)
			kinematicslib.joint_twist.lower_twist(ik_joints[2:4], self.lo_knee_joints)

		else:
			constraintslib.matrix_constraint(ik_joints[0], self.thigh_joints[0], maintain_offset=True)
			constraintslib.matrix_constraint(ik_joints[2], self.lo_knee_joints[0], maintain_offset=True)

		constraintslib.matrix_constraint(ik_joints[3], ankle_joint, maintain_offset=True)
		constraintslib.matrix_constraint(ik_joints[1], up_knee_joint, maintain_offset=True)

		# create soft ik
		soft_ik_grp = None
		if self.create_soft_ik:
			soft_ik_grp = kinematicslib.ik.create_soft_ik(leg_ik_ctrl.path,
			                                              prime_ik_joints,
			                                              [leg_ik],
			                                              self.get_rig_group(),
			                                              leg_ik_ctrl.last_node)

		if self.create_stretch:
			kinematicslib.stretch.quadruped_stretch(ik_ctrl=leg_ik_ctrl.path,
			                                        switch_ctrl=settings_ctrl.path,
			                                        fk_ctrls=[thigh_fk_ctrl.path,
			                                                  up_knee_fk_ctrl.path,
			                                                  lo_knee_fk_ctrl.path,
			                                                  ankle_fk_ctrl.path],
			                                        ik_joints=prime_ik_joints,
			                                        ik_handles=[leg_ik],
			                                        start_parent=self.get_rig_group(),
			                                        end_parent=leg_ik_ctrl.last_node,
			                                        soft_ik_grp=soft_ik_grp)

			# stretch twist joints
			cmds.connectAttr(prime_ik_joints[1] + ".tx", ik_joints[1] + ".tx")
			cmds.connectAttr(prime_ik_joints[2] + ".tx", ik_joints[2] + ".tx")
			cmds.connectAttr(prime_ik_joints[3] + ".tx", ik_joints[3] + ".tx")

			if self.num_twist_joints:
				div = 1.0 / (self.num_twist_joints + 1)
				up_plug = attributeslib.connection.multiply_connection(ik_joints[1] + ".tx", multiply_value=div)
				lo_plug = attributeslib.connection.multiply_connection(ik_joints[3] + ".tx", multiply_value=div)

				for jnt in thigh_joints[1:] + [up_knee_joint]:
					cmds.connectAttr(up_plug, jnt + ".tx")

				for jnt in lo_knee_joints[1:]:
					cmds.connectAttr(lo_plug, jnt + ".tx")

			else:
				cmds.connectAttr(prime_ik_joints[2] + ".tx", up_knee_joint + ".tx")
				cmds.connectAttr(prime_ik_joints[3] + ".tx", up_knee_joint + ".tx")

		# set quad arm mode
		if self.limb_style == "quadArm":
			cmds.setAttr(leg_ik_ctrl.path + ".springBias", 1)
		else:
			cmds.setAttr(leg_ik_ctrl.path + ".springBias", -0.5)

		# hide stuff
		cmds.hide(leg_ik, ik_joints[0], prime_ik_joints[0], thigh_ik, knee_ik)

		# lock stuff
		attributeslib.set_attributes(settings_ctrl.all_controls, ["t", "r", "s", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(thigh_fk_ctrl.all_controls +
		                             lo_knee_ik_ctrl.all_controls +
		                             up_knee_fk_ctrl.all_controls +
		                             lo_knee_fk_ctrl.all_controls +
		                             ankle_fk_ctrl.all_controls, ["t", "s"], lock=True, keyable=False)

		attributeslib.set_attributes(leg_pv_ctrl.all_controls, ["r", "s", "ro"], lock=True, keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(leg_ik_ctrl.all_controls, ["s"], lock=True, keyable=False)

		spc_obj = spaceslib.Space(leg_ik_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()
		spc_obj.set_options(default_value="world")

		spc_obj = spaceslib.Space(leg_pv_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()
