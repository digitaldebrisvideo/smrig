# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import geometrylib
from smrig.lib import kinematicslib
from smrig.lib import spaceslib
from smrig.lib import transformslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.eye")


class Eye(basepart.Basepart):
	"""
	eye rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Eye, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_skull_JNT", value_required=True)
		self.register_option("eyeAimControl", "parent_driver", "C_eyeAim_CTL", value_required=False)
		self.register_option("eyeBallCenterRefGeo", "selection", "")
		self.register_option("pupilCenterRefGeo", "selection", "")

	@property
	def eye_aim_control(self):
		return self.options.get("eyeAimControl").get("value")

	@property
	def eye_center_ref_geo(self):
		return self.find_stashed_nodes("eyeBallCenterRefGeo")

	@property
	def pupil_center_ref_geo(self):
		return self.find_stashed_nodes("pupilCenterRefGeo")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		placers = self.create_placer_chain("eye", num_placers=2)
		base_plc = self.create_placer(["eye", "base"])

		joints = self.create_joint_chain("eye",
		                                 num_joints=2,
		                                 placer_drivers=[p.path for p in placers],
		                                 constraints=["pointConstraint", "aimConstraint"],
		                                 up=[0, 1, 0],
		                                 wup=[0, 1, 0])

		kinematicslib.joint.distribute_chain(placers, [0, 0, 1])

		base_joint = self.create_joint(["eye", "base"], placer_driver=base_plc)
		cmds.xform(base_plc.path, r=1, t=[0, 0, -0.2])
		transformslib.xform.match(joints[0], base_plc.path, translate=False)

		cmds.parent(joints[0], base_joint)
		constraintslib.matrix_constraint(placers[0].last_node, base_joint)

		self.create_control(["eye", "squash"],
		                    shape="torso",
		                    color=self.secondary_color,
		                    axis="x",
		                    rotate_cvs=[90, 0, 0],
		                    driver=base_joint)

		self.create_control(["eye", "fk"],
		                    shape="cone",
		                    color=self.primary_color,
		                    axis="x",
		                    create_offset_controls=False,
		                    driver=joints[0])

		ctrl = self.create_control(["eye", "aim"],
		                           shape="circle",
		                           color=self.primary_color,
		                           axis="x",
		                           create_offset_controls=False,
		                           driver=base_joint)

		cmds.xform(ctrl.groups[0], r=1, t=[5, 0, 0])

		if self.eye_center_ref_geo:
			tmp = transformslib.xform.match_locator(self.eye_center_ref_geo)
			transformslib.xform.match(tmp, self.guide_group)
			cmds.delete(tmp)

		if self.pupil_center_ref_geo:
			tmp = transformslib.xform.match_locator(self.pupil_center_ref_geo)
			transformslib.xform.match(tmp, placers[-1].path)
			cmds.delete(tmp)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		base_jnt = self.format_name(["eye", "base"], node_type="joint")
		eye_jnt = self.format_name(["eye", 1], node_type="joint")
		eye_end_jnt = self.format_name(["eye", 2], node_type="joint")

		tmp = transformslib.xform.match_locator(eye_jnt)
		cmds.aimConstraint(eye_end_jnt, tmp, aim=[0, 0, 1], u=[0, 1, 0])

		fk_ctrl = self.create_control_from_guide(self.format_name(["eye", "fk"], node_type="animControl"),
		                                         translate=eye_jnt,
		                                         rotate=tmp,
		                                         scale=self.noxform_group)

		aim_ctrl = self.create_control_from_guide(self.format_name(["eye", "aim"], node_type="animControl"),
		                                          center_pivot_on_control=True,
		                                          rotate=self.noxform_group,
		                                          scale=self.noxform_group)

		squash_ctrl = self.create_control_from_guide(self.format_name(["eye", "squash"], node_type="animControl"))
		geometrylib.curve.create_curve_link([aim_ctrl.last_node, eye_jnt], parent=aim_ctrl.last_node)
		cmds.delete(tmp)

		# constrain joints
		cmds.aimConstraint(aim_ctrl.last_node,
		                   fk_ctrl.groups[-2],
		                   aim=[0, 0, 1],
		                   u=[0, 1, 0],
		                   wu=[0, 1, 0],
		                   wuo=fk_ctrl.groups[-1],
		                   wut="objectRotation",
		                   mo=True)

		constraintslib.matrix_constraint(squash_ctrl.last_node, base_jnt)
		constraintslib.matrix_constraint(fk_ctrl.last_node, eye_jnt)

		# parent stuff
		cmds.parent(fk_ctrl.groups[-1], squash_ctrl.last_node)
		cmds.parent(squash_ctrl.groups[-1], self.get_control_group("parent"))
		cmds.parent(aim_ctrl.groups[-1], self.get_control_group("eyeAimControl"))

		# lock stuff
		attributeslib.set_attributes(fk_ctrl.path, ["t", "s"], lock=True, keyable=False)
		attributeslib.set_attributes(aim_ctrl.path, ["r", "s", "ro"], lock=True, keyable=False, channel_box=False)

		spc_obj = spaceslib.Space(aim_ctrl.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.add_target(self.eye_aim_control, "aimControl")
		spc_obj.set_as_default()
