import math

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import sys

if sys.version_info[0] < 3:
    string_types = (str, unicode)
else:
    string_types = (str,)

from smrig.lib import api2lib as apilib
from smrig.lib import attributeslib

AXIS = "XYZ"
ROTATION_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
ROTATION_MIRROR = [[1, -1, -1], [-1, 1, -1], [-1, -1, 1]]
TRANSFORM_ATTRIBUTES = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "shearXY", "shearXZ", "shearYZ"]


def mirror_node(source, target=None, translate=False, rotate=False, scale=True, mirror=None):
	"""
	Mirror the provided target node from the provided source node using provided mirrorpart plane. If no mirrorpart
	plane is provided the function will exit.

	:source str: Source node
	:param target str: Target node
	:param bool translate: mirrorpart translates.
	:param bool rotate: mirrorpart rotates.
	:param bool scale: mirrorpart scales.
	:param str/None mirror: "x", "y", "z" or None
		:rtype: None
	"""
	target = target if target else source

	if not mirror:
		return

	if translate:
		xforms = cmds.xform(source, q=1, t=1, ws=1)
		result = mirror_translation(xforms, mirror=mirror)
		cmds.xform(target, ws=1, t=result)

	cmds.xform(target, ws=1, ro=cmds.xform(source, q=1, ws=1, ro=1))

	if rotate:
		rotate_order = cmds.getAttr(source + ".rotateOrder")
		xforms = cmds.xform(source, q=1, ro=1, ws=1)
		result = mirror_rotation(xforms, rotate_order=rotate_order, mirror=mirror)
		cmds.xform(target, ws=1, ro=result)

	cmds.xform(target, a=1, s=cmds.xform(source, q=1, r=1, s=1))

	if scale:
		dup_node = cmds.duplicate(source, po=1)[0]
		world_grp = cmds.createNode("transform")

		attributeslib.set_attributes(dup_node, TRANSFORM_ATTRIBUTES, lock=False, keyable=True)
		parent = cmds.listRelatives(target, parent=True)
		dup_node = cmds.parent(dup_node, world_grp)[0]
		cmds.setAttr("{}.s{}".format(world_grp, mirror.lower()), -1)

		if parent:
			dup_node = cmds.parent(dup_node, parent)[0]
		else:
			dup_node = cmds.parent(dup_node, w=True)[0]

		for attr in TRANSFORM_ATTRIBUTES:
			try:
				cmds.setAttr("{}.{}".format(target, attr), cmds.getAttr("{}.{}".format(dup_node, attr)))
			except:
				pass

		cmds.delete(world_grp, dup_node)


def mirror_translation(translate, mirror=None):
	"""
	Mirror the provided translation using provided mirrorpart plane. If no mirrorpart
	plane is provided the original translation will be returned.

	:param list translate:
	:param str/None mirror: "x", "y", "z" or None
	:return: Mirrored translation
	:rtype: list
	"""
	if mirror is None:
		return translate

	mirror_index = AXIS.index(mirror.upper())
	mirror_translate = translate[:]
	mirror_translate[mirror_index] = translate[mirror_index] * -1

	return mirror_translate


def mirror_rotation(rotate, rotate_order="xyz", mirror=None):
	"""
	Mirror the provided rotation using the provided mirrorpart plane. The provided
	rotation is an euler rotation so the rotation order must be provided to.
	If not mirrorpart plane is provided the original rotation will be returned.

	:param list rotate:
	:param int/str rotate_order: "xyz", "yzx", "zxy", "xzy", "yxz" or "zyx"
	:param str/None mirror: "x", "y", "z" or None
	:return: Mirrored Rotation
	:rtype: list
	"""
	if mirror is None:
		return rotate

	if isinstance(rotate_order, string_types):
		rotate_order = ROTATION_ORDERS.index(rotate_order)

	# get mirrorpart mapper
	mirror_index = AXIS.index(mirror.upper())
	mirror_values = ROTATION_MIRROR[mirror_index]
	scale_values = [mirror_value * -1 for mirror_value in mirror_values]

	# get rotation matrix
	euler = OpenMaya.MVector([math.radians(v) for v in rotate])
	euler = OpenMaya.MEulerRotation(euler, rotate_order)
	matrix = euler.asMatrix()

	# mirrorpart behaviour
	for i, mirror_multiplier in enumerate(mirror_values):
		# get vector
		vector = apilib.matrix.get_row(matrix, row=i)

		# scale vector, the orient multiplier ensures that rotation matrix
		# maintains a right handed orientation system. Not doing this would
		# result in a negative scale if the matrix is converted into
		# transformations.
		orient_multiplier = -1 if i == mirror_index else 1
		for j, scale_multiplier in enumerate(scale_values):
			vector[j] = vector[j] * scale_multiplier * orient_multiplier

		# multiply vector
		apilib.matrix.set_row(matrix, vector * mirror_multiplier, row=i)

	# get mirrored euler rotation
	mirror_matrix = OpenMaya.MTransformationMatrix(matrix)
	mirror_rotation = mirror_matrix.rotation()
	mirror_rotation.reorderIt(rotate_order)
	mirror_rotation = mirror_rotation.asVector()

	return [math.degrees(v) for v in mirror_rotation]


def create_mirror_link(source, target, mirror=None, translate=True, rotate=True, scale=False):
	"""
	Create a mirrorpart link between the source and the target. The mirrored
	rotation link is created in local space. Meaning that any parenting will
	have to be handled with care.

	:param str source:
	:param str target:
	:param str/None mirror: "x", "y", "z" or None
	:param bool translate:
	:param bool rotate:
	:param bool scale:
	"""
	if translate:
		create_mirror_translate_link(source, target, mirror)

	if rotate:
		create_mirror_rotate_link(source, target, mirror)

	if scale:
		attributes = cmds.attributeQuery("scale", node=target, listChildren=True)
		locked_attributes = attributeslib.get_locked_attributes(target, "translate")

		if len(locked_attributes) == 3:
			return

		for attribute in attributes:
			if attribute in locked_attributes:
				continue

			cmds.connectAttr("{}.{}".format(source, attribute), "{}.{}".format(target, attribute))


def create_mirror_translate_link(source, target, mirror=None):
	"""
	Create a translate mirrorpart link between the source and the target. The
	mirroring is handled in local space.

	:param str source:
	:param str target:
	:param str/None mirror: "x", "y", "z" or None
	"""
	# TODO: better way of finding name
	name = source.rsplit("_", 1)[0]
	attributes = cmds.attributeQuery("translate", node=target, listChildren=True)
	locked_attributes = attributeslib.get_locked_attributes(target, "translate")

	if len(locked_attributes) == 3:
		return

	mirror_plugs = ["{}.{}".format(source, a) for a in attributes]

	if mirror:
		mirror_index = AXIS.index(mirror.upper())
		mirror_values = [1 if i != mirror_index else -1 for i in range(3)]

		md = cmds.createNode("multiplyDivide", name="{}TranslateMirror_MD".format(name))
		cmds.setAttr("{}.input1".format(md), *mirror_values)
		cmds.connectAttr("{}.translate".format(source), "{}.input2".format(md))

		mirror_plugs = ["{}.output{}".format(md, a) for a in AXIS]

	for plug, attribute in zip(mirror_plugs, attributes):
		if attribute in locked_attributes:
			continue

		cmds.connectAttr(plug, "{}.{}".format(target, attribute))


def create_mirror_rotate_link(source, target, mirror=None):
	"""
	Create a rotate mirrorpart link between the source and the target. The
	mirroring is handled in local space.

	:param str source:
	:param str target:
	:param str/None mirror: "x", "y", "z" or None
	"""
	# TODO: better way of finding name
	name = source.rsplit("_", 1)[0]
	attributes = cmds.attributeQuery("rotate", node=target, listChildren=True)
	locked_attributes = attributeslib.get_locked_attributes(target, "rotate")

	if len(locked_attributes) == 3:
		return

	mirror_plugs = ["{}.{}".format(source, a) for a in attributes]

	if mirror:
		mirror_index = AXIS.index(mirror.upper())
		mirror_values = ROTATION_MIRROR[mirror_index]

		dm = cmds.createNode("decomposeMatrix", name="{}RotateMirror_DM".format(name))
		cmds.connectAttr("{}.matrix".format(source), "{}.inputMatrix".format(dm))

		md = cmds.createNode("multiplyDivide", name="{}RotateMirror_MD".format(name))
		cmds.setAttr("{}.input1".format(md), *mirror_values)
		cmds.connectAttr("{}.outputQuatX".format(dm), "{}.input2X".format(md))
		cmds.connectAttr("{}.outputQuatY".format(dm), "{}.input2Y".format(md))
		cmds.connectAttr("{}.outputQuatZ".format(dm), "{}.input2Z".format(md))

		qte = cmds.createNode("quatToEuler", name="{}RotateMirror_QTE".format(name))
		cmds.connectAttr("{}.outputX".format(md), "{}.inputQuatX".format(qte))
		cmds.connectAttr("{}.outputY".format(md), "{}.inputQuatY".format(qte))
		cmds.connectAttr("{}.outputZ".format(md), "{}.inputQuatZ".format(qte))
		cmds.connectAttr("{}.outputQuatW".format(dm), "{}.inputQuatW".format(qte))

		mirror_plugs = ["{}.outputRotate{}".format(qte, a) for a in AXIS]

	for plug, attribute in zip(mirror_plugs, attributes):
		if attribute in locked_attributes:
			continue

		cmds.connectAttr(plug, "{}.{}".format(target, attribute))
