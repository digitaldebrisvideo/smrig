from maya import cmds

from smrig import dataio
from smrig import partslib
from smrig.lib import attributeslib
from smrig.lib import selectionlib

model_top_grp = "L_feathers_model_GRP"
jnt_top_grp = "L_feathers_joints_GRP"

tail_model_top_grp = "L_tail_feathers_model_GRP"
tail_jnt_top_grp = "L_tail_feathers_joints_GRP"


def build_wing_guides():
	"""
	Build wing feather geo, joints and skinClusters for selected guide.

	:param guide_node:
	:return:
	"""
	delete_model()
	delete_joints()

	guide_nodes = partslib.utils.get_guides_in_scene("wing")
	results = []
	for node in guide_nodes:
		part_obj = partslib.part(node)
		if part_obj.side.startswith("L"):
			part_obj.build_wing_geo()
			results.append(part_obj)

	return results


def build_tail_guides():
	"""
	Build wing feather geo, joints and skinClusters for selected guide.

	:param guide_node:
	:return:
	"""
	delete_tail_model()
	delete_tail_joints()

	guide_nodes = partslib.utils.get_guides_in_scene("birdTail")
	results = []
	for node in guide_nodes:
		part_obj = partslib.part(node)
		if part_obj.side.startswith("C"):
			part_obj.build_wing_geo()
			results.append(part_obj)

	return results


def delete_model():
	"""

	:return:
	"""
	if cmds.objExists(model_top_grp):
		cmds.delete(model_top_grp)


def delete_joints():
	"""

	:return:
	"""
	if cmds.objExists(jnt_top_grp):
		cmds.delete(jnt_top_grp)


def delete_tail_model():
	"""

	:return:
	"""
	if cmds.objExists(tail_model_top_grp):
		cmds.delete(tail_model_top_grp)


def delete_tail_joints():
	"""

	:return:
	"""
	if cmds.objExists(tail_jnt_top_grp):
		cmds.delete(tail_jnt_top_grp)


def clean_model_weights(part_objs):
	"""
	Finalize the wing geo and joints

	:param part_objs:
	:return:
	"""
	for part_obj in part_objs:
		part_obj.finalize_wing_geo()


def mirror_wing_guides():
	"""

	:return:
	"""
	m_hi = cmds.duplicate(model_top_grp, rc=True)
	j_hi = cmds.duplicate(jnt_top_grp, rc=True)

	cmds.setAttr(m_hi[0] + ".sx", -1)
	cmds.setAttr(j_hi[0] + ".sx", -1)

	attributeslib.set_attributes(m_hi + j_hi, ["t", "r", "s"], lock=False, keyable=True)
	cmds.makeIdentity(m_hi[0], j_hi[0], apply=1, t=1, r=1, s=1, n=0, pn=1)

	mirrored_model_hi = [cmds.rename(n, n[:-1].replace("L", "R", 1)) for n in m_hi]
	joints_model_hi = [cmds.rename(n, n[:-1].replace("L", "R", 1)) for n in j_hi]

	for geo in mirrored_model_hi:
		lgeo = geo.replace("R", "L", 1)
		if not cmds.objExists(lgeo):
			continue

		scls = dataio.utils.get_deformers(lgeo, "skinCluster")

		if scls:
			rinfs = [n.replace("L", "R", 1) for n in cmds.skinCluster(scls, q=1, inf=1)]
			rscls = cmds.skinCluster(rinfs, geo, tsb=True, n=geo + "_SKN")

			cmds.copySkinWeights(ss=scls[0],
			                     ds=rscls[0],
			                     mirrorMode="YZ",
			                     surfaceAssociation="closestPoint",
			                     influenceAssociation="oneToOne")


def save_feather_weights_to_asset():
	"""
	Quick weights export.

	:return:
	"""
	nodes = cmds.ls("?" + model_top_grp[1:])
	hierarchy = selectionlib.get_children(nodes, all_descendents=True)
	for geo in hierarchy:
		scls = dataio.utils.get_deformers(geo, "skinCluster")
		if scls:
			dataio.save_to_asset("skinCluster", node=scls[0])


def finalize_model_and_joints():
	"""
	Duplicates and freezes geo and joints, parents for proper export.
	NOTE: youll need to parent the model whereever it needsto go, yourself.

	:return:
	"""
	top_grp = cmds.createNode("transform", n="feathers_model_GRP")

	nodes = cmds.ls("?" + model_top_grp[1:])

	# clean model
	hierarchy = selectionlib.get_children(nodes, all_descendents=True)
	attributeslib.set_attributes(hierarchy, ["t", "r", "s", "v"], lock=False, keyable=True)
	cmds.delete(hierarchy, ch=True)

	cmds.parent(nodes, top_grp)
	cmds.makeIdentity(top_grp, apply=1, t=1, r=1, s=1, n=0, pn=1)
	cmds.xform(hierarchy, piv=[0, 0, 0])

	# clean joints
	nodes = cmds.ls("?" + jnt_top_grp[1:])
	hierarchy = selectionlib.get_children(nodes, all_descendents=True)
	attributeslib.set_attributes(hierarchy, ["t", "r", "s", "v", "radius"], lock=False, keyable=True)
	snodes = selectionlib.get_children(nodes)
	top_jnts = selectionlib.get_children(snodes)

	attributeslib.connection.break_connections(top_jnts, "sz")
	cmds.makeIdentity(nodes, apply=1, t=1, r=1, s=1, n=0, pn=1)

	for topj in top_jnts:
		cmds.joint(topj, e=True, oj="xyz", secondaryAxisOrient="yup", ch=True, zso=True)
