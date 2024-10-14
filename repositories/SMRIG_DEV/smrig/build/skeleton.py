import logging

import maya.cmds as cmds
from smrig import env
from smrig import partslib
from smrig.lib import decoratorslib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.lib.constantlib import GUIDE_GRP

log = logging.getLogger("smrig.build.skeleton")

SIDE_MAPPER = {
	"C": 0,
	"Center": 0,
	"L": 1,
	"Left": 1,
	"R": 2,
	"Right": 2,
}

TYPE_MAPPER = {"ankle": 4,
               "ball": 5,
               "chest": 6,
               "head": 8,
               "hip": 1,
               "index_finger": 19,
               "forearm": 11,
               "knee": 3,
               "middle_finger": 20,
               "neck": 7,
               "pinky_finger": 22,
               "ring_finger": 21,
               "shoulder": 9,
               "spine": 6,
               "thumb_finger": 14,
               "_arm": 10,
               "thigh": 2,
               "root": 18,
               "wrist": 12}


@decoratorslib.undoable
def build(suffix=None, stash_guides=True):
	"""
	build skeleton from guides.

	:param str/None suffix:
	:param bool stash_guides: Put guides into statshed namespace
	:return:
	"""
	if stash_guides:
		utilslib.scene.stash_nodes(GUIDE_GRP, hierarchy=True)

	joint_suffix = env.prefs.get_suffix("joint")
	suffix = suffix if suffix else joint_suffix
	guide_groups = partslib.common.utils.get_guides_in_scene()
	parent_data = []
	joints = []

	all_part_objs = []

	for guide_group in guide_groups:
		part = partslib.part(guide_group)
		all_part_objs.append(part)

		options = eval(cmds.getAttr("{}.options".format(guide_group)))
		parent_drivers = [[k, v.get("value").replace(joint_suffix, suffix)]
		                  for k, v in options.items() if v.get("data_type") == "parent_driver"]

		stashed_joints = selectionlib.get_children(part.guide_joint_group, all_descendents=True, types=["joint"])
		part_joint_names = [j.split(":")[-1].replace(joint_suffix, suffix) for j in stashed_joints]
		part_joints = [cmds.createNode("joint", n=n) for n in part_joint_names]
		joints.extend(part_joints)

		for stashed_joint, joint in zip(stashed_joints, part_joints):
			transformslib.xform.match(stashed_joint, joint)

			parent = selectionlib.get_parent(stashed_joint)
			parent = parent if cmds.nodeType(parent) == "joint" else parent_drivers[0][1] if parent_drivers else None
			parent_data.append((joint, parent.split(":")[-1] if parent else None))

	for joint, parent in parent_data:
		if parent and cmds.objExists(parent.replace(joint_suffix, suffix)):
			cmds.parent(joint, parent.replace(joint_suffix, suffix))

	for part in all_part_objs:
		try:
			part.parent_skeleton()

		except:
			pass

	joints = selectionlib.sort_by_hierarchy(joints)
	cmds.makeIdentity(joints, apply=1, t=1, r=1, s=1, n=0, pn=1)

	for joint in joints:
		cmds.setAttr("{}.segmentScaleCompensate".format(joint), 0)
		label(joint)

	cmds.hide(cmds.ls(GUIDE_GRP, "*:" + GUIDE_GRP, guide_groups, ["*:{}".format(g) for g in guide_groups]))
	cmds.select(joints[0])

	return joints


def label(joint):
	"""
	Set the label on a joint using its name. The side will be stripped from
	the name and attempted to find either C, R or L. If the side cannot be
	determined a warning message is displayed and the side will be defaulted
	to C with the entire name used as the other type. If a side can be
	found its omitted from the other name. This will help with mirroring skin
	weights.

	:param str joint:
	"""
	split = joint.split("_") if joint.count("_") else [None, joint]
	side = split[0]
	name = joint
	side_index = SIDE_MAPPER.get(side)

	type_index = 18
	for token, idx in TYPE_MAPPER.items():
		if token in joint:
			type_index = idx
			break

	# validate name
	if side_index is None:
		side_index = 0
		name = joint
		log.warning("Unable to find side in joint '{}', default to 'C'.".format(joint))

	# set values
	cmds.setAttr("{}.side".format(joint), side_index)
	cmds.setAttr("{}.type".format(joint), type_index)
	cmds.setAttr("{}.otherType".format(joint), name, type="string")
