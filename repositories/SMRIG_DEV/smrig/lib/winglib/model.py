import os

from maya import cmds

from smrig.lib import geometrylib
from smrig.lib import naminglib
from smrig.lib import utilslib
from smrig.partslib import BIN_PATH

model_top_grp = "L_feathers_model_GRP"
jnt_top_grp = "L_feathers_joints_GRP"


def load_default_feather_geo():
	"""

	:return:
	"""
	return cmds.file(os.path.join(BIN_PATH, "default_feather_geo.mb"), rnn=True, i=True)


def build_single_feather(name, feather_geo=None, num_joints=8, offset=0.0, angle=0.0, joint_parent=None,
                         model_parent=None):
	"""
	Build a single feather geo with bound joints

	:param name:
	:param feather_geo:
	:param num_joints:
	:param offset:
	:param angle:
	:return:
	"""
	name = utilslib.conversion.as_list(name)

	if feather_geo:
		length = cmds.exactWorldBoundingBox(feather_geo, ii=1)[3]

		if offset:
			f_name = naminglib.format_name(name + ["feather", "up"], node_type="mesh")
			geos = cmds.duplicate(feather_geo, n=f_name)

			if angle:
				cmds.xform(geos, r=1, ro=[angle, 0, 0])
				cmds.makeIdentity(geos, apply=1, t=1, r=1, s=1, n=0, pn=1)

			cmds.xform(geos[0] + ".vtx[*]", r=1, t=[0, offset, 0])
			geos.append(cmds.duplicate(geos, n=naminglib.format_name(name + ["feather", "lo"], node_type="mesh"))[0])

			cmds.xform(geos[1], r=1, s=[1, -1, 1])
			cmds.makeIdentity(geos, apply=1, t=1, r=1, s=1, n=0, pn=1)

		else:
			f_name = naminglib.format_name(name + ["feather"], node_type="mesh")
			geos = cmds.duplicate(feather_geo, n=f_name)

			if angle:
				cmds.xform(geos, r=1, ro=[angle, 0, 0])
				cmds.makeIdentity(geos, apply=1, t=1, r=1, s=1, n=0, pn=1)

	else:
		geos = None
		length = 1.0

	cmds.select(cl=True)
	joints = [cmds.joint(name=naminglib.format_name(name + ["feather", i + 1], node_type="joint"))
	          for i in range(num_joints + 1)]

	cmds.xform(joints[1:], r=1, t=[length / num_joints, 0, 0])

	if joint_parent:
		cmds.parent(joints[0], joint_parent)

	if model_parent:
		cmds.parent(geos, model_parent)

	if geos:
		dr = max(min(length * 4, 10), 0.01) * (num_joints / 12.0)

		for g in geos:
			cmds.skinCluster(joints, g, tsb=True, n=g + "_SKN", bindMethod=0, normalizeWeights=1,
			                 weightDistribution=0, mi=5, omi=True, dr=dr, rui=True)

		return geos, joints

	else:
		return joints


def build_feather_section_geo(name,
                              base_crv,
                              tip_crv,
                              aim_crv=None,
                              feather_geo=None,
                              num_feathers=10,
                              num_joints=8,
                              offset=0,
                              angle=5.0):
	"""
	Build feather geo with bound joints along two curves

	:param name:
	:param base_crv:
	:param tip_crv:
	:param aim_crv:
	:param feather_geo:
	:param num_feathers:
	:param num_joints:
	:param offset:
	:param angle:
	:return:
	"""
	v0 = cmds.getAttr(base_crv + ".sy")
	cmds.setAttr(base_crv + ".sy", l=0)
	cmds.setAttr(base_crv + ".sy", 0)

	v1 = cmds.getAttr(tip_crv + ".sy")
	cmds.setAttr(tip_crv + ".sy", l=0)
	cmds.setAttr(tip_crv + ".sy", 0)

	v2 = None
	if aim_crv:
		v2 = cmds.getAttr(aim_crv + ".sy")
		cmds.setAttr(aim_crv + ".sy", l=0)
		cmds.setAttr(aim_crv + ".sy", 0)

	if not cmds.objExists(model_top_grp):
		cmds.createNode("transform", n=model_top_grp, p="guides_GRP")

	if not cmds.objExists(jnt_top_grp):
		cmds.createNode("transform", n=jnt_top_grp, p="guides_GRP")

	nname = naminglib.format_name(name + ["feathers", "model"], node_type="transform")
	model_grp = cmds.createNode("transform", n=nname, p=model_top_grp)

	nname = naminglib.format_name(name + ["feathers", "joints"], node_type="transform")
	jnt_grp = cmds.createNode("transform", n=nname, p=jnt_top_grp)

	# get distributed points on curve
	base_pts = geometrylib.curve.get_uniform_points_on_curve(base_crv, num_feathers)
	tip_pts = geometrylib.curve.get_uniform_points_on_curve(tip_crv, num_feathers)

	cmds.xform(jnt_grp, model_grp, ws=1, t=base_pts[0][:-1])

	if aim_crv:
		aim_pts = geometrylib.curve.get_uniform_points_on_curve(aim_crv, num_feathers)
	else:
		aim_pts = tip_pts

	# loop and build eah featherrig
	feather_geos = []
	feather_joints = []

	cmds.addAttr(model_grp, ln="thickness", k=1, dv=1)

	for i in range(num_feathers):
		geos, joints = build_single_feather(name + [i], feather_geo, num_joints, offset, angle, jnt_grp, model_grp)
		feather_geos.append(geos)
		feather_joints.append(joints)

		tmp = cmds.createNode("transform")
		cmds.xform(tmp, ws=True, t=tip_pts[i][:-1])
		cmds.xform(joints[0], ws=True, t=base_pts[i][:-1])

		length = utilslib.distance.get(tmp, joints[0])
		cmds.xform(tmp, ws=True, t=aim_pts[i][:-1])

		cmds.delete(cmds.aimConstraint(tmp, joints[0], aim=[1, 0, 0], u=[0, 1, 0], wut="scene"), tmp)
		cmds.xform(joints[1:], a=1, t=[length / num_joints, 0, 0])

		cmds.connectAttr(model_grp + ".thickness", joints[0] + ".sz")
		for j in joints:
			cmds.setAttr(j + ".segmentScaleCompensate", 0)

	cmds.setAttr(base_crv + ".sy", v0)
	cmds.setAttr(tip_crv + ".sy", v1)
	if v2 is not None:
		cmds.setAttr(aim_crv + ".sy", v2)

	return feather_geos, feather_joints
