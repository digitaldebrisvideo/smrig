import maya.cmds as cmds
from maya import OpenMaya as OpenMaya


def get(src_node=None, dst_node=None):
	"""

	:param src_node:
	:param dst_node:
	:return:
	"""
	if not src_node or not dst_node:
		src_node, dst_node = cmds.ls(sl=1)[0:2]

	if type(src_node) is not list:
		src_node = cmds.xform(src_node, q=1, ws=1, t=1)

	if type(dst_node) is not list:
		dst_node = cmds.xform(dst_node, q=1, ws=1, t=1)

	v1 = OpenMaya.MVector(src_node[0], src_node[1], src_node[2])
	v2 = OpenMaya.MVector(dst_node[0], dst_node[1], dst_node[2])
	return OpenMaya.MVector(v2 - v1).length()


def create_reader(start, end, chain_length=None, stretch=False, squash=True):
	"""
	Create distance reader node

	:param start:
	:param end:
	:param chain_length:
	:param stretch:
	:param squash
	:return:
	"""
	dst = "{}_{}_DST".format(start, end)
	dst = cmds.createNode("transform", p=start, n=dst)
	dst_shape = cmds.createNode("distanceDimShape", n=dst + "Shape", p=dst)

	s_mtx = cmds.createNode("decomposeMatrix")
	e_mtx = cmds.createNode("decomposeMatrix")

	cmds.connectAttr(start + ".worldMatrix", s_mtx + ".inputMatrix")
	cmds.connectAttr(end + ".worldMatrix", e_mtx + ".inputMatrix")

	cmds.connectAttr(s_mtx + ".outputTranslate", dst_shape + ".startPoint")
	cmds.connectAttr(e_mtx + ".outputTranslate", dst_shape + ".endPoint")
	cmds.setAttr(s_mtx + ".ihi", 0)
	cmds.setAttr(e_mtx + ".ihi", 0)

	cmds.addAttr(dst, ln="origDistance", k=1)
	cmds.addAttr(dst, ln="worldDistance", k=1)
	cmds.addAttr(dst, ln="localDistance", k=1)

	# Set init distance and world distance
	init_v = cmds.getAttr(dst_shape + ".distance")
	cmds.setAttr(dst + ".origDistance", init_v)
	cmds.connectAttr(dst_shape + ".distance", dst + ".worldDistance")

	# connect local distance
	md = cmds.createNode("multiplyDivide")
	cmds.connectAttr(dst_shape + ".distance", md + ".i1x")
	cmds.connectAttr(s_mtx + ".outputScaleX", md + ".i2x")
	cmds.connectAttr(md + ".ox", dst + ".localDistance")
	cmds.setAttr(md + ".operation", 2)
	cmds.setAttr(md + ".ihi", 0)

	if stretch:
		chain_length = chain_length if chain_length else init_v
		cmds.addAttr(dst, ln="stretch", min=0, max=1, dv=1, k=1)
		cmds.addAttr(dst, ln="stretchFactor", k=1)
		cmds.addAttr(dst, ln="inverseStretchFactor", k=1)
		cmds.addAttr(dst, ln="jointChainLength", k=1, dv=chain_length)

		# Create stretch factor
		clamp = cmds.createNode("clamp")
		cmds.setAttr(clamp + ".minR", 0.0001)
		cmds.setAttr(clamp + ".maxR", 100000000)

		if not squash:
			cmds.connectAttr(dst + ".jointChainLength", clamp + ".minR")

		md = cmds.createNode("multiplyDivide")
		cmds.connectAttr(dst + ".localDistance", clamp + ".inputR")
		cmds.connectAttr(clamp + ".outputR", md + ".i1x")
		cmds.connectAttr(dst + ".jointChainLength", md + ".i2x")
		cmds.setAttr(md + ".operation", 2)
		cmds.setAttr(md + ".ihi", 0)

		bta = cmds.createNode("blendTwoAttr")
		cmds.connectAttr(dst + ".stretch", bta + ".attributesBlender")
		cmds.connectAttr(md + ".ox", bta + ".input[1]")
		cmds.setAttr(bta + ".input[0]", 1.0)

		cmds.connectAttr(bta + ".output", dst + ".stretchFactor")

		# Create inverse stretch factor
		md = cmds.createNode("multiplyDivide")
		cmds.connectAttr(dst + ".stretchFactor", md + ".i2x")
		cmds.connectAttr(md + ".ox", dst + ".inverseStretchFactor")
		cmds.setAttr(md + ".i1x", 1.0)
		cmds.setAttr(md + ".operation", 2)
		cmds.setAttr(md + ".ihi", 0)

	for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
		cmds.setAttr("{}.{}".format(dst, attr), keyable=False, lock=True)

	for attr in ["origDistance", "stretchFactor", "inverseStretchFactor", "worldDistance", "localDistance"]:
		if cmds.objExists("{}.{}".format(dst, attr)):
			cmds.setAttr("{}.{}".format(dst, attr), keyable=True, lock=True)

	cmds.hide(dst_shape)
	cmds.select(dst)

	return dst
