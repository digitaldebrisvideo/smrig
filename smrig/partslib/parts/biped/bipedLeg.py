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
from smrig.lib import transformslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.bipedArm")


class BipedLeg(basepart.Basepart):
	"""
	bipedLeg rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(BipedLeg, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_hip_JNT", value_required=True)
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
	def thigh_joints(self):
		return [self.format_name(["thigh", i + 1], node_type="joint") for i in range(self.num_twist_joints + 1)]

	@property
	def knee_joints(self):
		return [self.format_name(["knee", i + 1], node_type="joint") for i in
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
		thigh_placer = self.create_placer("thigh1")
		knee_placer = self.create_placer("knee1")
		ankle_placer = self.create_placer("ankle")

		cmds.xform(knee_placer.groups[-1], t=[0, -3, 1])
		cmds.xform(ankle_placer.groups[-1], t=[0, -6, 0])

		# create joints
		thigh_joints = self.create_joint_chain("thigh", num_joints=self.num_twist_joints + 1)
		knee_joints = self.create_joint_chain("knee", num_joints=self.num_twist_joints + 1)
		ankle_joint = self.create_joint("ankle", placer_driver=ankle_placer, constraints="pointConstraint")

		cmds.parent(knee_joints[0], thigh_joints[-1])
		cmds.parent(ankle_joint, knee_joints[-1])

		# constrain joints
		cmds.pointConstraint(thigh_placer.path, thigh_joints[0])
		cmds.pointConstraint(knee_placer.path, knee_joints[0])

		cmds.aimConstraint(knee_placer.path,
		                   thigh_joints[0],
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, self.mirror_value],
		                   wut="object",
		                   wuo=ankle_placer.path)

		cmds.aimConstraint(ankle_placer.path,
		                   knee_joints[0],
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, self.mirror_value],
		                   wut="object",
		                   wuo=thigh_placer.path)

		if self.num_twist_joints:
			for i, twist_jnt in enumerate(thigh_joints[1:], 1):
				div = 1.0 / (self.num_twist_joints + 1)
				cmds.pointConstraint(thigh_placer.path, twist_jnt, weight=1.0 - (div * i))
				cmds.pointConstraint(knee_placer.path, twist_jnt, weight=(div * i))

			for i, twist_jnt in enumerate(knee_joints[1:], 1):
				div = 1.0 / (self.num_twist_joints + 1)
				cmds.pointConstraint(knee_placer.path, twist_jnt, weight=1.0 - (div * i))
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
		                    driver=knee_joints[0],
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

		cmds.xform(pv_ctrl.groups[0], a=1, t=[0, 0, 10])
		cmds.pointConstraint(thigh_joints[0], ankle_joint, pv_ctrl.groups[-1])

		cmds.aimConstraint(ankle_joint,
		                   pv_ctrl.groups[-1],
		                   aim=[1, 0, 0],
		                   u=[0, 0, 1],
		                   wut="object",
		                   wuo=knee_placer)

		attributeslib.set_attributes(pv_ctrl.path, ["ty"], lock=True, keyable=False)
		cmds.xform(ctrl.groups[0], a=1, ro=[180, 0, -90])

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		thigh_joints = self.thigh_joints
		knee_joints = self.knee_joints

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

		knee_fk_ctrl = self.create_control_from_guide(self.format_name(["knee", "fk"],
		                                                               node_type="animControl"))

		ankle_fk_ctrl = self.create_control_from_guide(self.format_name(["ankle", "fk"],
		                                                                node_type="animControl"))

		geometrylib.curve.create_curve_link([leg_pv_ctrl.path, knee_joints[0]], parent=leg_pv_ctrl.path)

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

		constraintslib.matrix_constraint(ankle_joint, settings_ctrl.path, maintain_offset=True)

		# parent controls
		cmds.parent(knee_fk_ctrl.groups[-1], thigh_fk_ctrl.last_node)
		cmds.parent(ankle_fk_ctrl.groups[-1], knee_fk_ctrl.last_node)

		cmds.parent(leg_ik_ctrl.groups[-1],
		            leg_pv_ctrl.groups[-1],
		            thigh_fk_ctrl.groups[-1],
		            settings_ctrl.path,
		            self.get_control_group())

		# animatable pivoits
		controlslib.create_animatable_pivot(leg_ik_ctrl)

		# create ik chain
		ik_joints = [
			cmds.duplicate(thigh_joints[0], n=self.format_name(["leg", "ik"],
			                                                   node_type="joint"), po=1)[0],

			cmds.duplicate(knee_joints[0], n=self.format_name(["knee", "ik"],
			                                                  node_type="joint"), po=1)[0],

			cmds.duplicate(ankle_joint, n=self.format_name(["ankle", "ik"],
			                                               node_type="joint"), po=1)[0],

		]

		for i in range(1, len(ik_joints)):
			cmds.parent(ik_joints[i], ik_joints[i - 1])

		cmds.parent(ik_joints[0], self.get_rig_group())

		# connect fk rotations
		cmds.connectAttr(thigh_fk_ctrl.path + ".r", ik_joints[0] + ".r")
		cmds.connectAttr(knee_fk_ctrl.path + ".r", ik_joints[1] + ".r")

		cmds.connectAttr(thigh_fk_ctrl.path + ".ro", ik_joints[0] + ".ro")
		cmds.connectAttr(knee_fk_ctrl.path + ".ro", ik_joints[1] + ".ro")
		cmds.connectAttr(ankle_fk_ctrl.path + ".ro", ik_joints[2] + ".ro")

		constraintslib.matrix_constraint(leg_ik_ctrl.last_node, ik_joints[2], maintain_offset=True,
		                                 translate=False,
		                                 rotate=True,
		                                 scale=False)

		end_joint_rotate_bcl = cmds.createNode("blendColors")
		cnn = cmds.listConnections(ik_joints[2] + ".r", p=True)

		cmds.connectAttr(ankle_fk_ctrl.path + ".r", end_joint_rotate_bcl + ".color2")
		cmds.connectAttr(cnn[0], end_joint_rotate_bcl + ".color1")
		cmds.connectAttr(end_joint_rotate_bcl + ".output", ik_joints[2] + ".r", f=True)

		# create ik handles
		leg_ik = kinematicslib.ik.create_ik_handle(ik_joints[0], ik_joints[2])
		cmds.poleVectorConstraint(leg_pv_ctrl.last_node, leg_ik)

		leg_ik_grp = cmds.createNode("transform", n=leg_ik + "_GRP")
		cmds.parent(leg_ik, leg_ik_grp)
		cmds.parent(leg_ik_grp, leg_ik_ctrl.last_node)

		cmds.addAttr(leg_ik_ctrl, ln="twist", k=1)
		if self.mirror_value == 1:
			cmds.connectAttr("{}.twist".format(leg_ik_ctrl.path), leg_ik + ".twist")
		else:
			attributeslib.connection.negative_connection("{}.twist".format(leg_ik_ctrl.path), leg_ik + ".twist")

		# create switch
		fk_controls = [thigh_fk_ctrl.path]
		ik_controls = [leg_ik_ctrl.path, leg_pv_ctrl.path]
		kinematicslib.ik.create_fk_ik_switch(settings_ctrl.path, [leg_ik], fk_controls, ik_controls)
		cmds.connectAttr(settings_ctrl.path + ".ikBlend", end_joint_rotate_bcl + ".blender")

		# twist
		if self.num_twist_joints:
			kinematicslib.joint_twist.upper_twist(self.get_rig_group(), ik_joints[0:2], self.thigh_joints)
			kinematicslib.joint_twist.lower_twist(ik_joints[1:3], self.knee_joints)

		else:
			constraintslib.matrix_constraint(ik_joints[0], self.thigh_joints[0], maintain_offset=True)
			constraintslib.matrix_constraint(ik_joints[1], self.knee_joints[0], maintain_offset=True)

		constraintslib.matrix_constraint(ik_joints[2], ankle_joint, maintain_offset=True)

		# create soft ik
		soft_ik_grp = None
		if self.create_soft_ik:
			soft_ik_grp = kinematicslib.ik.create_soft_ik(leg_ik_ctrl.path,
			                                              ik_joints,
			                                              [leg_ik],
			                                              self.get_rig_group(),
			                                              leg_ik_ctrl.last_node)

		if self.create_stretch:
			kinematicslib.stretch.biped_stretch(ik_ctrl=leg_ik_ctrl.path,
			                                    pv_ctrl=leg_pv_ctrl.path,
			                                    switch_ctrl=settings_ctrl.path,
			                                    fk_ctrls=[thigh_fk_ctrl.path, knee_fk_ctrl.path, ankle_fk_ctrl.path],
			                                    ik_joints=ik_joints[:3],
			                                    ik_handles=[leg_ik],
			                                    start_parent=self.get_rig_group(),
			                                    end_parent=leg_ik_ctrl.last_node,
			                                    soft_ik_grp=soft_ik_grp)

			# stretch twist joints
			if self.num_twist_joints:
				div = 1.0 / (self.num_twist_joints + 1)
				up_plug = attributeslib.connection.multiply_connection(ik_joints[1] + ".tx", multiply_value=div)
				lo_plug = attributeslib.connection.multiply_connection(ik_joints[2] + ".tx", multiply_value=div)

				for jnt in thigh_joints[1:]:
					cmds.connectAttr(up_plug, jnt + ".tx")

				for jnt in knee_joints[1:]:
					cmds.connectAttr(lo_plug, jnt + ".tx")

		# create foot aim PV space node
		pv_space_grp = self.create_node("transform", name="pv_space", p=self.get_rig_group())
		aim = self.create_node("transform", name="pv_aim", p=self.get_rig_group())
		wup = self.create_node("transform", name="pv_up", p=self.get_rig_group())

		transformslib.xform.match(ik_joints[0], [pv_space_grp, aim], rotate=False)
		transformslib.xform.match(leg_ik_ctrl.last_node, wup, rotate=False)
		cmds.xform(aim, r=1, t=[0, abs(cmds.getAttr(ik_joints[1] + ".tx")), 0])
		cmds.parent(wup, leg_ik_ctrl.last_node)

		cmds.aimConstraint(aim, pv_space_grp, aim=[0, 1, 0], u=[1, 0, 0], wu=[1, 0, 0], wut="objectRotation", wuo=wup)

		# hide stuff
		cmds.hide(leg_ik, ik_joints[0])

		# lock stuff
		attributeslib.set_attributes(settings_ctrl.all_controls, ["t", "r", "s", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(thigh_fk_ctrl.all_controls +
		                             knee_fk_ctrl.all_controls +
		                             ankle_fk_ctrl.all_controls, ["t", "s"], lock=True, keyable=False)

		attributeslib.set_attributes(leg_pv_ctrl.all_controls, ["r", "s", "ro"], lock=True, keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(leg_ik_ctrl.all_controls, ["s"], lock=True, keyable=False)

		spc_obj = spaceslib.Space(leg_ik_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_options(default_value="world")
		spc_obj.set_as_default()

		spc_obj = spaceslib.Space(leg_pv_ctrl.path)
		spc_obj.add_target(pv_space_grp, "footAlign")
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_options(default_value="footAlign")
		spc_obj.set_as_default()
