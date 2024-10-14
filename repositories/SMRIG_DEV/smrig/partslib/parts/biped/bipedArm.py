# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import kinematicslib
from smrig.lib import selectionlib
from smrig.lib import spaceslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.bipedArm")


class BipedArm(basepart.Basepart):
	"""
	bipedArm rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(BipedArm, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "L_shoulder_JNT", value_required=True)
		self.register_option("numTwistJoints", "int", 4, min=0, rebuild_required=True)

		self.register_option("createSoftIK", "bool", True)
		self.register_option("createStretch", "bool", True)
		self.register_option("createBendy", "bool", True)

	@property
	def parent(self):
		return self.options.get("parent").get("value")

	@property
	def num_twist_joints(self):
		return self.options.get("numTwistJoints").get("value")

	@property
	def create_soft_ik(self):
		return self.options.get("createSoftIK").get("value")

	@property
	def create_stretch(self):
		return self.options.get("createBendy").get("value")

	@property
	def arm_joints(self):
		return [self.format_name(["arm", i + 1], node_type="joint") for i in range(self.num_twist_joints + 1)]

	@property
	def forearm_joints(self):
		return [self.format_name(["forearm", i + 1], node_type="joint") for i in
		        range(self.num_twist_joints + 1)]

	@property
	def foot_part_required_nodes(self):
		"""
		This method returns all required nodes to build a foot part


		:return:
		"""
		return [self.format_name(["wrist", "ik"], node_type="joint"),
		        self.format_name("wrist", node_type="joint"),
		        controlslib.Control(self.format_name(["arm", "ik"], node_type="animControl")),
		        controlslib.Control(self.format_name(["wrist", "fk"], node_type="animControl")),
		        controlslib.Control(self.format_name(["arm", "settings"], node_type="animControl"))]

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		arm_placer = self.create_placer(["arm", 1])
		forearm_placer = self.create_placer(["forearm", 1])
		wrist_placer = self.create_placer("wrist")
		knuckle_placer = self.create_placer("knuckle")

		cmds.xform(forearm_placer.groups[-1], t=[3, 0, -1])
		cmds.xform(wrist_placer.groups[-1], t=[6, 0, 0])
		cmds.xform(knuckle_placer.groups[-1], t=[7, 0, 0])

		cmds.pointConstraint(wrist_placer.path, knuckle_placer.groups[-1])
		cmds.xform(knuckle_placer.groups[-2], t=[1, 0, 0])

		# create joints
		arm_joints = self.create_joint_chain("arm", num_joints=self.num_twist_joints + 1)
		forearm_joints = self.create_joint_chain("forearm", num_joints=self.num_twist_joints + 1)
		wrist_joint = self.create_joint("wrist", placer_driver=wrist_placer, constraints="pointConstraint")
		knuckle_joint = self.create_joint("knuckle", placer_driver=knuckle_placer, constraints="pointConstraint")

		cmds.parent(forearm_joints[0], arm_joints[-1])
		cmds.parent(wrist_joint, forearm_joints[-1])
		cmds.parent(knuckle_joint, wrist_joint)

		# constrain joints
		cmds.pointConstraint(arm_placer.path, arm_joints[0])
		cmds.pointConstraint(forearm_placer.path, forearm_joints[0])

		cmds.aimConstraint(forearm_placer.path,
		                   arm_joints[0],
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, self.mirror_value],
		                   wut="object",
		                   wuo=wrist_placer.path)

		cmds.aimConstraint(wrist_placer.path,
		                   forearm_joints[0],
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, self.mirror_value],
		                   wut="object",
		                   wuo=arm_placer.path)

		cmds.aimConstraint(knuckle_placer,
		                   wrist_joint,
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 1, 0],
		                   wu=[0, 1, 0],
		                   wut="objectRotation",
		                   wuo=wrist_placer)

		if self.num_twist_joints:
			for i, twist_jnt in enumerate(arm_joints[1:], 1):
				div = 1.0 / (self.num_twist_joints + 1)
				cmds.pointConstraint(arm_placer.path, twist_jnt, weight=1.0 - (div * i))
				cmds.pointConstraint(forearm_placer.path, twist_jnt, weight=(div * i))

			for i, twist_jnt in enumerate(forearm_joints[1:], 1):
				div = 1.0 / (self.num_twist_joints + 1)
				cmds.pointConstraint(forearm_placer.path, twist_jnt, weight=1.0 - (div * i))
				cmds.pointConstraint(wrist_placer.path, twist_jnt, weight=(div * i))

		# fk controls
		self.create_control(["arm", "fk"],
		                    shape="circle",
		                    color=self.primary_color,
		                    driver=arm_joints[0],
		                    axis="x")

		self.create_control(["forearm", "fk"],
		                    shape="circle",
		                    color=self.primary_color,
		                    driver=forearm_joints[0],
		                    axis="x")

		self.create_control(["wrist", "fk"],
		                    shape="circle",
		                    color=self.primary_color,
		                    driver=wrist_joint,
		                    axis="x")

		# ik controls
		self.create_control(["arm", "ik"],
		                    shape="cube",
		                    color=self.primary_color,
		                    driver=wrist_joint,
		                    num_offset_controls=1,
		                    scale=0.75,
		                    axis="x")

		self.create_control(["knuckle", "ik"],
		                    shape="lollipop",
		                    color=self.secondary_color,
		                    driver=knuckle_joint,
		                    create_offset_controls=False,
		                    axis="y")

		self.create_control(["arm", "settings"],
		                    shape="flag",
		                    color=self.detail_color,
		                    driver=wrist_joint,
		                    create_offset_controls=False,
		                    axis="y")

		pv_ctrl = self.create_control(["arm", "pv"],
		                              shape="cube",
		                              color=self.primary_color,
		                              create_offset_controls=False,
		                              locked_pivot_attrs=["r", "s"],
		                              axis="z",
		                              scale=0.25)

		cmds.xform(pv_ctrl.groups[0], a=1, t=[0, 0, -10])
		cmds.pointConstraint(arm_joints[0], wrist_joint, pv_ctrl.groups[-1])

		cmds.aimConstraint(wrist_joint,
		                   pv_ctrl.groups[-1],
		                   aim=[1, 0, 0],
		                   u=[0, 0, -1],
		                   wut="object",
		                   wuo=forearm_placer)

		attributeslib.set_attributes(pv_ctrl.path, ["ty"], lock=True, keyable=False)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		arm_joints = self.arm_joints
		forearm_joints = self.forearm_joints

		wrist_joint = self.format_name("wrist", node_type="joint")
		knuckle_joint = self.format_name("knuckle", node_type="joint")

		arm_ik_ctrl = self.create_control_from_guide(self.format_name(["arm", "ik"],
		                                                              node_type="animControl"), node_type="joint")

		arm_pv_ctrl = self.create_control_from_guide(self.format_name(["arm", "pv"],
		                                                              node_type="animControl"),
		                                             center_pivot_on_control=True)

		knuckle_ik_ctrl = self.create_control_from_guide(self.format_name(["knuckle", "ik"],
		                                                                  node_type="animControl"))

		settings_ctrl = self.create_control_from_guide(self.format_name(["arm", "settings"],
		                                                                node_type="animControl"), num_groups=0)

		arm_fk_ctrl = self.create_control_from_guide(self.format_name(["arm", "fk"],
		                                                              node_type="animControl"))

		forearm_fk_ctrl = self.create_control_from_guide(self.format_name(["forearm", "fk"],
		                                                                  node_type="animControl"))

		wrist_fk_ctrl = self.create_control_from_guide(self.format_name(["wrist", "fk"],
		                                                                node_type="animControl"))

		geometrylib.curve.create_curve_link([arm_pv_ctrl.path, forearm_joints[0]], parent=arm_pv_ctrl.path)

		# constrain and orient controls
		zero_grp = arm_ik_ctrl.groups[-1]
		parent_grp = arm_ik_ctrl.groups[0]

		cmds.parent(arm_ik_ctrl, w=1)
		tmp_par = selectionlib.get_parent(arm_ik_ctrl)

		cmds.xform(zero_grp, a=1, ro=[0, 180, 0] if self.mirror_value == -1 else [0, 0, 0])
		cmds.parent(arm_ik_ctrl, parent_grp)
		cmds.makeIdentity(arm_ik_ctrl, apply=1, r=1, n=0, pn=1)

		if tmp_par:
			cmds.delete(tmp_par)

		cmds.xform(arm_pv_ctrl.groups[-1], ws=1, ro=cmds.xform(arm_ik_ctrl.groups[-1], q=1, ws=1, ro=1))
		cmds.xform(arm_pv_ctrl.groups[-1], a=1, s=cmds.xform(arm_ik_ctrl.groups[-1], q=1, r=1, s=1))

		constraintslib.matrix_constraint(wrist_joint, settings_ctrl.path, maintain_offset=True)

		# parent controls
		cmds.parent(forearm_fk_ctrl.groups[-1], arm_fk_ctrl.last_node)
		cmds.parent(wrist_fk_ctrl.groups[-1], forearm_fk_ctrl.last_node)
		cmds.parent(knuckle_ik_ctrl.groups[-1], arm_ik_ctrl.last_node)

		cmds.parent(arm_ik_ctrl.groups[-1],
		            arm_pv_ctrl.groups[-1],
		            arm_fk_ctrl.groups[-1],
		            settings_ctrl.path,
		            self.get_control_group())

		# animatable pivoits
		controlslib.create_animatable_pivot(arm_ik_ctrl)
		controlslib.create_animatable_pivot(knuckle_ik_ctrl)

		# create ik chain
		ik_joints = [
			cmds.duplicate(arm_joints[0], n=self.format_name(["arm", "ik"],
			                                                 node_type="joint"), po=1)[0],

			cmds.duplicate(forearm_joints[0], n=self.format_name(["forearm", "ik"],
			                                                     node_type="joint"), po=1)[0],

			cmds.duplicate(wrist_joint, n=self.format_name(["wrist", "ik"],
			                                               node_type="joint"), po=1)[0],

			cmds.duplicate(knuckle_joint, n=self.format_name(["knuckle", "ik"],
			                                                 node_type="joint"), po=1)[0]
		]
		ori_joints = [
			cmds.duplicate(arm_joints[0], n=self.format_name(["arm", "ori"],
			                                                 node_type="joint"), po=1)[0],

			cmds.duplicate(forearm_joints[0], n=self.format_name(["forearm", "ori"],
			                                                     node_type="joint"), po=1)[0],

			cmds.duplicate(wrist_joint, n=self.format_name(["wrist", "ori"],
			                                               node_type="joint"), po=1)[0],

			cmds.duplicate(knuckle_joint, n=self.format_name(["knuckle", "ori"],
			                                                 node_type="joint"), po=1)[0]
		]
		for i in range(1, len(ik_joints)):
			cmds.parent(ik_joints[i], ik_joints[i - 1])

		for i in range(1, len(ori_joints)):
			cmds.parent(ori_joints[i], ori_joints[i - 1])

		cmds.parent(ik_joints[0], ori_joints[0], self.get_rig_group())

		# connect fk rotations
		cmds.orientConstraint(arm_fk_ctrl.path, ik_joints[0], mo=True)
		cmds.connectAttr(forearm_fk_ctrl.path + ".r", ik_joints[1] + ".r")
		cmds.connectAttr(wrist_fk_ctrl.path + ".r", ik_joints[2] + ".r")

		cmds.connectAttr(arm_fk_ctrl.path + ".ro", ik_joints[0] + ".ro")
		cmds.connectAttr(forearm_fk_ctrl.path + ".ro", ik_joints[1] + ".ro")
		cmds.connectAttr(wrist_fk_ctrl.path + ".ro", ik_joints[2] + ".ro")

		cmds.orientConstraint(arm_fk_ctrl.path, ori_joints[0], mo=True)
		cmds.connectAttr(forearm_fk_ctrl.path + ".r", ori_joints[1] + ".r")
		cmds.connectAttr(wrist_fk_ctrl.path + ".r", ori_joints[2] + ".r")

		cmds.connectAttr(arm_fk_ctrl.path + ".ro", ori_joints[0] + ".ro")
		cmds.connectAttr(forearm_fk_ctrl.path + ".ro", ori_joints[1] + ".ro")
		cmds.connectAttr(wrist_fk_ctrl.path + ".ro", ori_joints[2] + ".ro")

		# create ik handles
		ori_ik = kinematicslib.ik.create_ik_handle(ori_joints[0], ori_joints[2])
		arm_ik = kinematicslib.ik.create_ik_handle(ik_joints[0], ik_joints[2])
		wrist_ik = kinematicslib.ik.create_ik_handle(ik_joints[2], ik_joints[3])
		cmds.poleVectorConstraint(arm_pv_ctrl.last_node, arm_ik)
		cmds.poleVectorConstraint(arm_pv_ctrl.last_node, ori_ik)
		cmds.parent(arm_ik, wrist_ik, knuckle_ik_ctrl.last_node)
		cmds.parent(ori_ik, wrist_ik, arm_ik_ctrl)

		cmds.addAttr(arm_ik_ctrl, ln="twist", k=1)

		if self.mirror_value == 1:
			cmds.connectAttr("{}.twist".format(arm_ik_ctrl.path), arm_ik + ".twist")
		else:
			attributeslib.connection.negative_connection("{}.twist".format(arm_ik_ctrl.path), arm_ik + ".twist")

		# create switch
		fk_controls = [arm_fk_ctrl.path]
		ik_controls = [arm_ik_ctrl.path, arm_pv_ctrl.path]
		kinematicslib.ik.create_fk_ik_switch(settings_ctrl.path, [arm_ik, wrist_ik], fk_controls, ik_controls)

		# twist
		if self.num_twist_joints:
			kinematicslib.joint_twist.upper_twist(self.get_rig_group(), ik_joints[0:1], self.arm_joints)
			kinematicslib.joint_twist.lower_twist(ik_joints[1:3], self.forearm_joints)

		else:
			constraintslib.matrix_constraint(ik_joints[0], self.arm_joints[0], maintain_offset=True)
			constraintslib.matrix_constraint(ik_joints[1], self.forearm_joints[0], maintain_offset=True)

		constraintslib.matrix_constraint(ik_joints[2], wrist_joint, maintain_offset=True)

		oc = cmds.orientConstraint(wrist_joint, knuckle_ik_ctrl.groups[-1], knuckle_joint, mo=True)[0]
		attributeslib.connection.reverse_connection(settings_ctrl.path + ".ikBlend", oc + ".w0")
		cmds.connectAttr(settings_ctrl.path + ".ikBlend", oc + ".w1")
		cmds.setAttr(oc + ".interpType", 2)

		attributeslib.connection.break_connections(self.forearm_joints[0], ["t", "r"])
		cmds.parentConstraint(ik_joints[1], self.forearm_joints[0], mo=1)

		# create soft ik
		soft_ik_grp = None
		if self.create_soft_ik:
			soft_ik_grp = kinematicslib.ik.create_soft_ik(arm_ik_ctrl.path,
			                                              ik_joints[:-1],
			                                              [arm_ik, wrist_ik],
			                                              self.get_rig_group(),
			                                              knuckle_ik_ctrl.last_node)

		if self.create_stretch:
			kinematicslib.stretch.biped_stretch(ik_ctrl=arm_ik_ctrl.path,
			                                    pv_ctrl=arm_pv_ctrl.path,
			                                    switch_ctrl=settings_ctrl.path,
			                                    fk_ctrls=[arm_fk_ctrl.path, forearm_fk_ctrl.path, wrist_fk_ctrl.path],
			                                    ik_joints=ik_joints[:3],
			                                    ik_handles=[arm_ik, wrist_ik],
			                                    start_parent=self.get_rig_group(),
			                                    end_parent=knuckle_ik_ctrl.last_node,
			                                    soft_ik_grp=soft_ik_grp)

			# stretch twist joints
			if self.num_twist_joints:
				div = 1.0 / (self.num_twist_joints + 1)
				up_plug = attributeslib.connection.multiply_connection(ik_joints[1] + ".tx", multiply_value=div)
				lo_plug = attributeslib.connection.multiply_connection(ik_joints[2] + ".tx", multiply_value=div)

				for jnt in arm_joints[1:]:
					cmds.connectAttr(up_plug, jnt + ".tx")

				for jnt in forearm_joints[1:]:
					cmds.connectAttr(lo_plug, jnt + ".tx")

		# create wrist blend
		grp = cmds.group(arm_ik_ctrl.offset_controls[0], n=arm_ik_ctrl.path + "_ori_GRP")
		cmds.xform(grp, piv=[0, 0, 0])

		follow_grp = cmds.duplicate(grp, po=1, n=ori_joints[1] + "_ori_follow_GRP")[0]
		follow = cmds.duplicate(grp, po=1, n=ori_joints[1] + "_ori_follow")[0]

		cmds.parent(follow, follow_grp)
		cmds.parent(follow_grp, ori_joints[1])

		oc = cmds.orientConstraint(arm_ik_ctrl.path, follow, grp, mo=True)

		cmds.addAttr(arm_ik_ctrl.path, ln="wristOrient", min=0, max=1, k=1)
		cmds.connectAttr(arm_ik_ctrl.path + ".wristOrient", oc[0] + ".w1")
		attributeslib.connection.reverse_connection(arm_ik_ctrl.path + ".wristOrient", oc[0] + ".w0")

		# hide stuff
		cmds.hide(arm_ik, wrist_ik, ik_joints[0])

		# lock stuff
		attributeslib.set_attributes(settings_ctrl.all_controls + [grp, ori_ik], ["t", "r", "s", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(arm_fk_ctrl.all_controls +
		                             forearm_fk_ctrl.all_controls +
		                             wrist_fk_ctrl.all_controls, ["t", "s"], lock=True, keyable=False)

		attributeslib.set_attributes(arm_pv_ctrl.all_controls, ["r", "s", "ro"], lock=True, keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(arm_ik_ctrl.all_controls + knuckle_ik_ctrl.all_controls, ["s"], lock=True,
		                             keyable=False)

		spc_obj = spaceslib.Space(arm_ik_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()

		spc_obj = spaceslib.Space(arm_fk_ctrl.path)
		spc_obj.set_options(translate=False)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()
