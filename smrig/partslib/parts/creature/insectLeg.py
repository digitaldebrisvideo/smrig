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
from smrig.lib import utilslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.insectLeg")


class InsectLeg(basepart.Basepart):
	"""
	insectLeg rig part module.
	"""

	BUILD_LAST = False

	def __init__(self, *guide_node, **options):
		super(InsectLeg, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("numMetatarsusJoints", "int", 1, min=1, rebuild_required=True)
		self.register_option("numTarsusJoints", "int", 1, min=1, rebuild_required=True)
		self.register_option("createTrochanterJoint", "bool", True, rebuild_required=True)
		self.register_option("orientTransToWorld", "bool", True)
		self.register_option("createSoftIK", "bool", True)

	@property
	def create_trochanter(self):
		"""

		:return:
		"""
		return self.options.get("createTrochanterJoint").get("value")

	@property
	def num_metatarsus_joints(self):
		"""

		:return:
		"""
		return self.options.get("numMetatarsusJoints").get("value")

	@property
	def num_tarsus_joints(self):
		"""

		:return:
		"""
		return self.options.get("numTarsusJoints").get("value")

	@property
	def create_soft_ik(self):
		"""

		:return:
		"""
		return self.options.get("createSoftIK").get("value")

	@property
	def orient_to_world(self):
		"""

		:return:
		"""
		return self.options.get("orientTransToWorld").get("value")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		plcs = [self.create_placer("coxa")]
		plcs.append(self.create_placer("trochanter"))
		plcs.append(self.create_placer("femur"))
		plcs.append(self.create_placer("tibia"))
		m_plcs = self.create_placers(["metatarsus"], num_placers=self.num_metatarsus_joints)
		t_plcs = self.create_placers(["tarsus"], num_placers=self.num_tarsus_joints)
		claw_plc = self.create_placer("claw")

		all_plcs = plcs + m_plcs + t_plcs + [claw_plc]

		cmds.xform(plcs[0], ws=True, t=[0.0, 0.0, 0.0], ro=[0.0, 0.0, 0.0])
		cmds.xform(plcs[1], ws=True, t=[1.0, -1.0, 0.0], ro=[0.0, 0.0, 0.0])
		cmds.xform(plcs[2], ws=True, t=[2.0, -1.0, 0.0], ro=[0.0, 0.0, 0.0])
		cmds.xform(plcs[3], ws=True, t=[5.0, 1.0, 0.0], ro=[0.0, 0.0, 0.0])
		cmds.xform(m_plcs[0], ws=True, t=[8.0, -1.0, 0.0], ro=[0.0, 0.0, 0.0])
		cmds.xform(t_plcs[0], ws=True, t=[9.0, -4.0, 0.0], ro=[0.0, 0.0, 0.0])
		cmds.xform(claw_plc, ws=True, t=[11.0, -6.0, 0.0], ro=[0.0, 0.0, 0.0])

		div = 1.0 / self.num_metatarsus_joints
		if self.num_metatarsus_joints > 1:
			for i, plc in enumerate(m_plcs[1:], 1):
				transformslib.xform.match_blend(m_plcs[0].path, t_plcs[0].path, plc, weight=div * i)

		div = 1.0 / self.num_tarsus_joints
		if self.num_tarsus_joints > 1:
			for i, plc in enumerate(t_plcs[1:], 1):
				transformslib.xform.match_blend(t_plcs[0].path, claw_plc.path, plc, weight=div * i)

		all_jnts = self.create_joint_chain("insectLegTMP",
		                                   use_placer_name=True,
		                                   placer_drivers=all_plcs,
		                                   num_joints=len(all_plcs),
		                                   constraints="pointConstraint")

		constraintslib.aim_constraint_chain(cmds.ls(all_plcs),
		                                    cmds.ls(all_jnts),
		                                    aim=[1, 0, 0],
		                                    up=[0, 0, 1],
		                                    wup=[0, 0, 1],
		                                    mirror_value=self.mirror_value)

		# Create FK ctrls -----------------------------------------------------------------

		self.create_control(["coxa", "fk"], shape="circle", color=self.primary_color, axis="x", driver=all_jnts[0])
		tr_ctrl = self.create_control(["trochanter", "fk"],
		                              shape="circle",
		                              color=self.primary_color,
		                              axis="x",
		                              driver=all_jnts[1])

		self.create_control(["femur", "fk"], shape="circle", color=self.primary_color, axis="x", driver=all_jnts[2])
		self.create_control(["tibia", "fk"], shape="circle", color=self.primary_color, axis="x", driver=all_jnts[3])

		num = 4 if self.create_trochanter else 3
		self.create_controls(["metatarsus", "fk"],
		                     num=self.num_metatarsus_joints,
		                     shape="circle",
		                     color=self.primary_color,
		                     axis="x",
		                     drivers=all_jnts[4:])

		self.create_controls(["tarsus", "fk"],
		                     num=self.num_tarsus_joints,
		                     shape="circle",
		                     color=self.primary_color,
		                     axis="x",
		                     drivers=all_jnts[4 + self.num_metatarsus_joints:])

		# create IK ctrls -------------------------------------------------------------------
		self.create_control(["leg", "base", "ik"], shape="prism", color=self.primary_color, axis="x",
		                    driver=all_jnts[0])

		self.create_control(["leg", "ik"],
		                    shape="cube",
		                    color=self.primary_color,
		                    driver=all_jnts[-1],
		                    num_offset_controls=1)

		self.create_control(["knee", "ik"],
		                    shape="sphere",
		                    color=self.primary_color,
		                    driver=all_jnts[2],
		                    create_offset_controls=False)

		self.create_control(["lower", "knee", "ik"],
		                    shape="sphere",
		                    color=self.primary_color,
		                    driver=all_jnts[-1],
		                    create_offset_controls=False)

		self.create_control(["leg", "settings"],
		                    shape="flag",
		                    color=self.detail_color,
		                    driver=all_jnts[-1],
		                    create_offset_controls=False,
		                    axis="z",
		                    scale=1)

		ctrl = self.create_control(["leg", "pv"],
		                           shape="cube",
		                           color=self.primary_color,
		                           driver=all_plcs[0],
		                           constraints="pointConstraint",
		                           create_offset_controls=False)

		cmds.xform(ctrl.groups[0], ws=1, t=[0, 10, 0])

		ctrl = self.create_control(["leg", "lower", "pv"],
		                           shape="cube",
		                           color=self.primary_color,
		                           driver=all_jnts[2],
		                           create_offset_controls=False)

		cmds.xform(ctrl.groups[0], a=1, t=[10, 0, 0])

		if not self.create_trochanter:
			cmds.select(all_jnts[1])
			mel.eval("RemoveJoint")

			cmds.delete(plcs[1].groups[-1], tr_ctrl.groups[-1])

		constraintslib.aim_constraint_chain(cmds.ls(all_plcs),
		                                    cmds.ls(all_jnts),
		                                    aim=[1, 0, 0],
		                                    up=[0, 0, 1],
		                                    wup=[0, 0, 1],
		                                    mirror_value=self.mirror_value)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""

		# Create FK ctrls ------------------------------------------------------------
		names = ["coxa", "trochanter", "femur", "tibia"]
		names = [self.format_name([n, "fk"], node_type="animControl") for n in names]
		fk_ctrls = [self.create_control_from_guide(n) for n in names if cmds.objExists(self.get_guide_node(n))]

		names = [["metatarsus", "fk", i + 1] for i in range(self.num_metatarsus_joints)]
		names = [self.format_name(n, node_type="animControl") for n in names]
		m_fk_ctrls = [self.create_control_from_guide(n) for n in names]

		names = [["tarsus", "fk", i + 1] for i in range(self.num_tarsus_joints)]
		names = [self.format_name(n, node_type="animControl") for n in names]
		t_fk_ctrls = [self.create_control_from_guide(n) for n in names]

		all_fk_ctrls = fk_ctrls + m_fk_ctrls + t_fk_ctrls
		for i, ctrl in enumerate(all_fk_ctrls[1:]):
			cmds.parent(ctrl.groups[-1], all_fk_ctrls[i].last_node)

		cmds.parent(all_fk_ctrls[0].groups[-1], self.get_control_group())

		# decalre joints --------------------------------------------------------------
		upper_jnts = [c.path.replace("CTL", "JNT").replace("_fk", "") for c in fk_ctrls]
		meta_jnts = [c.path.replace("CTL", "JNT").replace("_fk", "") for c in m_fk_ctrls]
		tarsus_jnts = [c.path.replace("CTL", "JNT").replace("_fk", "") for c in t_fk_ctrls]
		claw_jnt = self.format_name("claw", node_type="joint")

		# Create IK ctrls ------------------------------------------------------------
		name = self.format_name(["leg", "base", "ik"], node_type="animControl")
		leg_base_ik_ctrl = self.create_control_from_guide(name)

		name = self.format_name(["leg", "settings"], node_type="animControl")
		settings_ctrl = self.create_control_from_guide(name)

		name = self.format_name(["leg", "ik"], node_type="animControl")
		leg_ik_ctrl = self.create_control_from_guide(name)

		name = self.format_name(["knee", "ik"], node_type="animControl")
		knee_ik_ctrl = self.create_control_from_guide(name)

		name = self.format_name(["lower", "knee", "ik"], node_type="animControl")
		lo_knee_ik_ctrl = self.create_control_from_guide(name)

		name = self.format_name(["leg", "pv"], node_type="animControl")
		leg_pv_ctrl = self.create_control_from_guide(name, center_pivot_on_control=True)

		name = self.format_name(["leg", "lower", "pv"], node_type="animControl")
		leg_lo_pv_ctrl = self.create_control_from_guide(name, center_pivot_on_control=True)

		cmds.parent(leg_base_ik_ctrl.groups[-1],
		            leg_ik_ctrl.groups[-1],
		            knee_ik_ctrl.groups[-1],
		            lo_knee_ik_ctrl.groups[-1],
		            leg_pv_ctrl.groups[-1],
		            leg_lo_pv_ctrl.groups[-1],
		            settings_ctrl.groups[-1],
		            self.get_control_group())

		cmds.parent(leg_lo_pv_ctrl.groups[-1], knee_ik_ctrl.last_node)

		# constrain and orient controls -------------------------------------------------

		if self.orient_to_world:
			zero_grp = leg_ik_ctrl.groups[-1]
			parent_grp = leg_ik_ctrl.groups[0]
			cmds.parent(leg_ik_ctrl, w=1)
			tmp_par = selectionlib.get_parent(leg_ik_ctrl)

			cmds.xform(zero_grp, a=1, ro=[0, 180, 0] if self.mirror_value == -1 else [0, 0, 0])
			cmds.parent(leg_ik_ctrl, parent_grp)
			cmds.makeIdentity(leg_ik_ctrl, apply=1, r=1, n=0, pn=1)

			if tmp_par:
				cmds.delete(tmp_par)

		controlslib.create_animatable_pivot(leg_ik_ctrl)
		geometrylib.curve.create_curve_link([leg_pv_ctrl.path, upper_jnts[0]], parent=leg_pv_ctrl.path)
		geometrylib.curve.create_curve_link([leg_lo_pv_ctrl.path, upper_jnts[-1]], parent=leg_lo_pv_ctrl.path)

		# duplicate jointchain ---------------------------------------------------------

		prime_ik_joints = kinematicslib.joint.duplicate_chain(upper_jnts + meta_jnts + tarsus_jnts + [claw_jnt],
		                                                      search="JNT", replace="primary_ik_JNT")

		ik_joints = kinematicslib.joint.duplicate_chain(upper_jnts + meta_jnts + tarsus_jnts + [claw_jnt],
		                                                search="JNT", replace="ik_JNT")

		cmds.parent(prime_ik_joints[0], ik_joints[0], self.get_rig_group())

		for ik_jnt, jnt in zip(ik_joints, upper_jnts + meta_jnts + tarsus_jnts + [claw_jnt]):
			constraintslib.matrix_constraint(ik_jnt, jnt, maintain_offset=False)

		# constraint all fk ctrls to jnts ---------------------------------------------------------

		for ctrl, jnt in zip(fk_ctrls + m_fk_ctrls + t_fk_ctrls, upper_jnts + meta_jnts + tarsus_jnts):
			cmds.connectAttr(ctrl.path + ".r", jnt.replace("JNT", "primary_ik_JNT") + ".r")
			cmds.connectAttr(ctrl.path + ".ro", jnt.replace("JNT", "primary_ik_JNT") + ".ro")

			cmds.connectAttr(ctrl.path + ".r", jnt.replace("JNT", "ik_JNT") + ".r")
			cmds.connectAttr(ctrl.path + ".ro", jnt.replace("JNT", "ik_JNT") + ".ro")

		constraintslib.matrix_constraint(prime_ik_joints[0], leg_base_ik_ctrl.groups[0])
		constraintslib.matrix_constraint(leg_base_ik_ctrl.last_node, ik_joints[0], scale=False)

		# setup primary ik ---------------------------------------------------------

		cmds.addAttr(leg_ik_ctrl, ln="twist", k=1)

		leg_ik = kinematicslib.ik.create_ik_handle(prime_ik_joints[0], claw_jnt.replace("JNT", "primary_ik_JNT"))
		cmds.poleVectorConstraint(leg_pv_ctrl.last_node, leg_ik)

		twist_value = kinematicslib.ik.align_ik_twist(ik_joints[3], prime_ik_joints[3], leg_ik)

		leg_ik_grp = cmds.createNode("transform", n=leg_ik + "_GRP")
		cmds.parent(leg_ik_grp, leg_ik_ctrl.last_node)
		cmds.parent(leg_ik, leg_ik_grp)

		if self.mirror_value == 1:
			attributeslib.connection.add_connection("{}.twist".format(leg_ik_ctrl.path),
			                                        target_plug=leg_ik + ".twist",
			                                        add_value=twist_value)
		else:
			attributeslib.connection.add_connection(
				attributeslib.connection.negative_connection("{}.twist".format(leg_ik_ctrl.path)),
				target_plug=leg_ik + ".twist",
				add_value=twist_value)

		# setup secondary ik ---------------------------------------------------------

		num = 3 if self.create_trochanter else 2
		ik_num = 0 if self.create_trochanter else 1
		thigh_ik = kinematicslib.ik.create_ik_handle(ik_joints[ik_num], ik_joints[num])
		knee_ik = kinematicslib.ik.create_ik_handle(ik_joints[num], tarsus_jnts[0].replace("JNT", "ik_JNT"))
		tarsus_ik = kinematicslib.ik.create_ik_handle(tarsus_jnts[0].replace("JNT", "ik_JNT"),
		                                              claw_jnt.replace("JNT", "ik_JNT"))

		pv_grp = self.create_node("transform", ["leg", "up", "pv"], p=prime_ik_joints[1])
		dist = utilslib.distance.get(prime_ik_joints[3], ik_joints[-1])
		cmds.xform(pv_grp, a=1, t=[0, 0, dist * 3])

		cmds.poleVectorConstraint(pv_grp, thigh_ik)
		if self.create_trochanter:
			t_twist_value = kinematicslib.ik.align_ik_twist(ik_joints[1], prime_ik_joints[1], thigh_ik)
		else:
			t_twist_value = 0

		cmds.poleVectorConstraint(leg_lo_pv_ctrl, knee_ik)
		k_twist_value = kinematicslib.ik.align_ik_twist(ik_joints[5], prime_ik_joints[5], knee_ik)

		cmds.parent(thigh_ik, knee_ik_ctrl.last_node)
		cmds.parent(knee_ik, lo_knee_ik_ctrl.last_node)
		cmds.parent(tarsus_ik, claw_jnt.replace("JNT", "primary_ik_JNT"))

		constraintslib.matrix_constraint(prime_ik_joints[num - 1], knee_ik_ctrl.groups[-1])
		constraintslib.matrix_constraint(tarsus_jnts[0].replace("JNT", "primary_ik_JNT"), lo_knee_ik_ctrl.groups[-1])

		# setup secondary twist ---------------------------------------------------------

		cmds.addAttr(knee_ik_ctrl.path, ln="upperTwist", k=True)
		cmds.addAttr(knee_ik_ctrl.path, ln="lowerTwist", k=True)

		if self.mirror_value == 1:
			attributeslib.connection.add_connection("{}.upperTwist".format(knee_ik_ctrl.path),
			                                        target_plug=thigh_ik + ".twist",
			                                        add_value=t_twist_value)
		else:
			attributeslib.connection.add_connection(
				attributeslib.connection.negative_connection("{}.upperTwist".format(knee_ik_ctrl.path)),
				target_plug=thigh_ik + ".twist",
				add_value=t_twist_value)

		if self.mirror_value == 1:
			attributeslib.connection.add_connection("{}.lowerTwist".format(knee_ik_ctrl.path),
			                                        target_plug=knee_ik + ".twist",
			                                        add_value=k_twist_value)
		else:
			attributeslib.connection.add_connection(
				attributeslib.connection.negative_connection("{}.lowerTwist".format(knee_ik_ctrl.path)),
				target_plug=knee_ik + ".twist",
				add_value=k_twist_value)

		# create soft ik ---------------------------------------------------------

		soft_ik_grp = None
		if self.create_soft_ik:
			soft_ik_grp = kinematicslib.ik.create_soft_ik(leg_ik_ctrl.path,
			                                              prime_ik_joints,
			                                              [leg_ik],
			                                              self.get_rig_group(),
			                                              leg_ik_ctrl.last_node)

		# create ik switch ------------------------------------------------------

		constraintslib.matrix_constraint(claw_jnt, settings_ctrl.groups[-1])

		fk_controls = [fk_ctrls[0].path]
		ik_controls = [leg_ik_ctrl.path, leg_lo_pv_ctrl.path, leg_pv_ctrl.path, knee_ik_ctrl.path]
		kinematicslib.ik.create_fk_ik_switch(settings_ctrl.path,
		                                     [leg_ik, thigh_ik, knee_ik, tarsus_ik],
		                                     fk_controls,
		                                     ik_controls)

		# constrain
		# hide stuff ------------------------------------------------------

		cmds.hide(ik_joints[0], prime_ik_joints[0], leg_ik, thigh_ik, knee_ik, tarsus_ik)

		# lock stuff ------------------------------------------------------

		attributeslib.set_attributes(settings_ctrl.all_controls, ["t", "r", "s", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

		for ctrl in fk_ctrls + m_fk_ctrls + t_fk_ctrls:
			attributeslib.set_attributes(ctrl.all_controls, ["t", "s"], lock=True, keyable=False)

		attributeslib.set_attributes(leg_pv_ctrl.all_controls + leg_lo_pv_ctrl.all_controls,
		                             ["r", "s", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

		attributeslib.set_attributes(knee_ik_ctrl.all_controls + lo_knee_ik_ctrl.all_controls,
		                             ["t", "s"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)
		if self.create_trochanter:
			attributeslib.set_attributes(knee_ik_ctrl.all_controls,
			                             ["t"],
			                             lock=False,
			                             keyable=True,
			                             channel_box=False)

		attributeslib.set_attributes(leg_base_ik_ctrl.all_controls, ["t", "s"], lock=True, keyable=False)
		attributeslib.set_attributes(leg_ik_ctrl.all_controls, ["s"], lock=True, keyable=False)
		attributeslib.set_attributes(knee_ik_ctrl.all_controls, ["upperTwist"], lock=True, keyable=False)

		spc_obj = spaceslib.Space(leg_ik_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()
		spc_obj.set_options(default_value="world")

		spc_obj = spaceslib.Space(leg_pv_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.set_as_default()
