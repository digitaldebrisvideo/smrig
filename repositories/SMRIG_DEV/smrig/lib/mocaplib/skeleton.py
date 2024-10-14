import maya.cmds as cmds
import maya.mel as mel

from smrig import env
from smrig.build import skeleton
from smrig.lib import utilslib


def build_mocap_skeleton(fingers=True,
                         num_torso_joints=2,
                         num_neck_joints=1,
                         num_arm_joints=1,
                         num_leg_joints=1,
                         suffix=None):
	"""
	Build a mocap skeleton.

	:param bool fingers:
	:param int num_torso_joints:
	:param int num_neck_joints:
	:param int num_arm_joints:
	:param int num_leg_joints:
	:param str suffix:
	:return: Mocap skeleton hierarchy
	:rtype: list
	"""
	joint_suffix = env.prefs.get_suffix("joint")
	suffix = suffix if suffix else joint_suffix

	all_joints = skeleton.build(suffix=suffix)

	joints = cmds.ls("C_root_{}".format(suffix),
	                 "C_hip_{}".format(suffix),
	                 "C_chest_{}".format(suffix),
	                 "C_head_{}".format(suffix),
	                 "?_shoulder_{}".format(suffix),
	                 "?_wrist_{}".format(suffix),
	                 "?_ankle_{}".format(suffix),
	                 "?_ball_{}".format(suffix), type='joint')

	torso_joints = cmds.ls("C_spine*_{}".format(suffix))
	joints.extend([l[0] for l in utilslib.conversion.split_list(torso_joints, num_torso_joints)])

	neck_joints = cmds.ls("C_neck*_{}".format(suffix))
	joints.extend([l[0] for l in utilslib.conversion.split_list(neck_joints, num_neck_joints)])

	for side in ["L", "R"]:
		arm_joints = cmds.ls("{}_arm*_{}".format(side, suffix))
		joints.extend([l[0] for l in utilslib.conversion.split_list(arm_joints, num_arm_joints)])

		forearm_joints = cmds.ls("{}_forearm*_{}".format(side, suffix))
		joints.extend([l[0] for l in utilslib.conversion.split_list(forearm_joints, num_arm_joints)])

		thigh_joints = cmds.ls("{}_thigh*_{}".format(side, suffix))
		joints.extend([l[0] for l in utilslib.conversion.split_list(thigh_joints, num_leg_joints)])

		knee_joints = cmds.ls("{}_knee*_{}".format(side, suffix))
		joints.extend([l[0] for l in utilslib.conversion.split_list(knee_joints, num_leg_joints)])

		if fingers:
			joints.extend(cmds.ls("{}_thumb_finger_fk*_{}".format(side, suffix), type="joint")[:-1])
			joints.extend(cmds.ls("{}_index_finger_fk*_{}".format(side, suffix), type="joint")[:-1])
			joints.extend(cmds.ls("{}_middle_finger_fk*_{}".format(side, suffix), type="joint")[:-1])
			joints.extend(cmds.ls("{}_ring_finger_fk*_{}".format(side, suffix), type="joint")[:-1])
			joints.extend(cmds.ls("{}_pinky_finger_fk*_{}".format(side, suffix), type="joint")[:-1])

	cmds.select([j for j in all_joints if j not in joints])
	mel.eval('RemoveJoint')

	return joints
