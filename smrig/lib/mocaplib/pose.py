import os

import maya.cmds as cmds

from smrig.lib import iolib
from smrig.lib import pathlib
from smrig.lib import selectionlib
from smrig.lib import utilslib

ARM_LABELS = ["Collar", "Shoulder", "Elbow", "Hand"]
LEG_LABELS = ["Hip", "Knee", "Foot", "Toe"]
TORSO_LABELS = ["world", "Root", "Spine", "Neck", "Head"]
HAND_LABELS = ["Thumb", "Index Finger", "Middle Finger", "Ring Finger", "Pinky Finger"]


def write_poses_to_file(asset=None, pose_names=None):
	"""
	This seems to be nessecary for ingesting as the poses are cleared when we get mocap from vendors

	:return:
	"""

	asset = asset if asset else env.get_asset()
	pose_names = pose_names if pose_names else ["t_pose", "a_pose"]

	path = os.path.join(env.get_rigbuild_path(asset), "data", "mocap")
	file_path = os.path.join(path, "mocap_poses.json")

	attr_data = {}
	for name in pose_names:
		attrs = cmds.ls("*.{}Translate".format(name), "*.{}Rotate".format(name))
		for attr in attrs:
			attr_data[attr] = cmds.getAttr(attr)[0]

	label_attrs = cmds.ls("*JNT.side", "*JNT.type", "*JNT.otherType")
	for attr in label_attrs:
		attr_data[attr] = cmds.getAttr(attr)

	pathlib.make_dirs(path)
	iolib.json.write(file_path, attr_data)


def load_poses_from_file(asset=None):
	"""
	Load poses and jointlabel information from file.

	:param asset:
	:return:
	"""
	asset = asset if asset else env.get_asset()
	path = os.path.join(env.get_rigbuild_path(asset), "data", "mocap")
	file_path = os.path.join(path, "mocap_poses.json")
	attr_data = iolib.json.read(file_path)

	for attr, value in attr_data.items():
		if cmds.objExists(attr):
			if "otherType" in attr:
				cmds.setAttr(attr, value, type="string")
			else:
				if isinstance(value, int):
					cmds.setAttr(attr, value)
				else:
					cmds.setAttr(attr, *value)


def create_tpose_from_labels(namespace=None, freeze_joints=True, descriptor=None):
	"""
	:param str namespace:
	:param bool freeze_joints:
	:param str/ None descriptor:
	:return:
	"""

	def get_world_xforms(joints):
		"""
		:param list joints:
		:return:
		"""
		return [cmds.xform(j, q=True, ws=True, ro=True) for j in joints]

	def set_world_xforms(joints, poses):
		"""
		:param list joints:
		:param list poses:
		:return:
		"""
		for joint, pose in zip(joints, poses):
			cmds.xform(joint, ws=1, ro=pose)

	def create_t_pose(joints, orientation, freeze_joints):
		"""
		:param list joints:
		:param list orientation:
		:param bool freeze_joints:
		:return:
		"""
		poses = get_world_xforms(joints)
		cmds.xform(joints, ws=1, ro=orientation)
		record_pose(joints, "t_pose")

		if freeze_joints:
			cmds.makeIdentity(joints, apply=1, t=False, r=freeze_joints, s=False, n=False, pn=False)
			record_pose(joints, "t_pose")

		set_world_xforms(joints, poses)
		record_pose(joints, "a_pose")
		set_pose("t_pose")

	descriptor = descriptor if descriptor else ""

	# Left arm
	joints = get_joints_by_label("Left", ARM_LABELS[1:], namespace=namespace, descriptor=descriptor)
	create_t_pose(joints, [0, 0, 0], freeze_joints)

	# left hand
	for label in HAND_LABELS:
		joints = get_joints_by_label("Left", [label], namespace=namespace, descriptor=descriptor)
		record_pose([joints[0]], "t_pose")
		record_pose([joints[0]], "a_pose")

	# Right arm
	joints = get_joints_by_label("Right", ARM_LABELS[1:], namespace=namespace, descriptor=descriptor)
	create_t_pose(joints, [0, 180, 180], freeze_joints)

	# right hand
	for label in HAND_LABELS:
		joints = get_joints_by_label("Right", [label], namespace=namespace, descriptor=descriptor)
		record_pose([joints[0]], "t_pose")
		record_pose([joints[0]], "a_pose")

	# Left leg
	joints = get_joints_by_label("Left", LEG_LABELS[0:2], namespace=namespace, descriptor=descriptor)
	create_t_pose(joints, [180, 0, -90], freeze_joints)

	# Right leg
	joints = get_joints_by_label("Right", LEG_LABELS[0:2], namespace=namespace, descriptor=descriptor)
	create_t_pose(joints, [0, 0, 90], freeze_joints)

	# Left foot
	ankle = get_joints_by_label("Left", LEG_LABELS[2], namespace=namespace, descriptor=descriptor)
	create_t_pose(ankle, [180, -cmds.getAttr("{}.joy".format(ankle[0])), -90], freeze_joints)

	toe = get_joints_by_label("Left", LEG_LABELS[3], namespace=namespace, descriptor=descriptor)
	create_t_pose(toe, [180, -90, -90], freeze_joints)

	# Right foot
	ankle = get_joints_by_label("Right", LEG_LABELS[2], namespace=namespace, descriptor=descriptor)
	create_t_pose(ankle, [0, cmds.getAttr("{}.joy".format(ankle[0])), 90], freeze_joints)

	toe = get_joints_by_label("Right", LEG_LABELS[3], namespace=namespace, descriptor=descriptor)
	create_t_pose(toe, [180, 90, -90], freeze_joints)

	# record pose for head neck and spine
	set_pose("a_pose")

	record_pose(get_joints_by_label("Center", TORSO_LABELS[:2], namespace=namespace, descriptor=descriptor), "t_pose",
	            translate=True)
	record_pose(get_joints_by_label("Center", TORSO_LABELS[:2], namespace=namespace, descriptor=descriptor), "a_pose",
	            translate=True)
	record_pose(get_joints_by_label("Center", TORSO_LABELS, namespace=namespace, descriptor=descriptor), "t_pose")
	record_pose(get_joints_by_label("Center", TORSO_LABELS, namespace=namespace, descriptor=descriptor), "a_pose")

	# record pose for clavicles
	record_pose(get_joints_by_label(["Left", "Right"], ARM_LABELS[0], namespace=namespace, descriptor=descriptor),
	            "t_pose")
	record_pose(get_joints_by_label(["Left", "Right"], ARM_LABELS[0], namespace=namespace, descriptor=descriptor),
	            "a_pose")


def get_joints_by_label(sides, labels, namespace=None, descriptor=""):
	"""
	Get joints with given side and labels.

	:param str/list sides:
	:param str/list labels:
	:param str/None namespace:
	:param str/None descriptor:
	:return: Joints
	:rtype: list
	"""
	namespace = "{}:*".format(namespace) if namespace else ":*"

	result = []
	for side in utilslib.conversion.as_list(sides):
		for label in utilslib.conversion.as_list(labels):
			joints = [j for j in cmds.ls(namespace, type="joint") if descriptor in j]
			joints = [j for j in joints if cmds.getAttr("{}.side".format(j), asString=True) == side]
			joints = [j for j in joints
			          if cmds.getAttr("{}.type".format(j), asString=True) == label
			          or cmds.getAttr("{}.otherType".format(j)) == label]

			result.extend(selectionlib.sort_by_hierarchy(joints))

	return result


def record_pose(joints, pose_name, translate=False, rotate=True):
	"""
	Record current absolute values to pose attribute

	:param list joints:
	:param str pose_name:
	:param bool translate:
	:param bool rotate:
	:return:
	"""
	attrs = []
	if translate:
		attrs.append("Translate")
	if rotate:
		attrs.append("Rotate")

	for joint in joints:
		for attr in attrs:
			attr_name = "{}{}".format(pose_name, attr)

			if not cmds.objExists("{}.{}".format(joint, attr_name)):
				cmds.addAttr(joint, ln="{}".format(attr_name), at="float3")
				cmds.addAttr(joint, ln="{}X".format(attr_name), at="float", parent="{}".format(attr_name))
				cmds.addAttr(joint, ln="{}Y".format(attr_name), at="float", parent="{}".format(attr_name))
				cmds.addAttr(joint, ln="{}Z".format(attr_name), at="float", parent="{}".format(attr_name))

			if attr == "Translate":
				cmds.setAttr("{}.{}".format(joint, attr_name), *cmds.xform(joint, a=True, q=True, t=True))

			if attr == "Rotate":
				cmds.setAttr("{}.{}".format(joint, attr_name), *cmds.xform(joint, a=True, q=True, ro=True))


def set_pose(pose_name, namespace=None, suffix=None):
	"""
	Set pose.

	:param str pose_name:
	:param str/None namespace:
	:param str/None suffix:
	:return:
	"""
	suffix = suffix if suffix else ""
	namespace = "{}:".format(namespace) if namespace else ""

	for attr in ["Translate", "Rotate"]:
		joints = [j for j in cmds.ls("{}*.{}{}".format(namespace, pose_name, attr)) if suffix in j]
		for joint in joints:
			cmds.setAttr("{}.{}".format(joint.split(".")[0], attr.lower()), *cmds.getAttr(joint)[0])
