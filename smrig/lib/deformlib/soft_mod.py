import logging

import maya.cmds as cmds

log = logging.getLogger("smrig.lib.deformlib.soft_mod")

FALL_OFF_MODE = {"volume": 0, "surface": 1}


def create_soft_mod(name, base, target, geometry, falloff_mode="volume"):
	"""
	The soft mod creation add a sof mod of the provided name an has it driven
	by the base and target. The base node can be moved around without having
	effect on the soft mod where the translational differences of the target
	activate the soft mod.

	When providing the name the suffix can be omitted as any node created will
	have its suffix appended to the name.

	:param str name:
	:param str base:
	:param str target:
	:param str/list geometry:
	:param str falloff_mode: "volume" or "surface"
	:return: Soft mod
	:rtype: str
	"""
	# create soft mod
	soft_mod = cmds.softMod(geometry, name="{}_SM".format(name), weightedNode=(target, target))[0]

	# extract world matrix
	dm = cmds.createNode("decomposeMatrix", name="{}_DM".format(name))
	cmds.connectAttr("{}.worldMatrix".format(base), "{}.inputMatrix".format(dm))

	# extract difference matrix
	mm = cmds.createNode("multMatrix", name="{}_MM".format(name))
	cmds.connectAttr("{}.worldInverseMatrix".format(base), "{}.matrixIn[0]".format(mm))
	cmds.connectAttr("{}.worldMatrix".format(target), "{}.matrixIn[1]".format(mm))

	# set falloff mode
	falloff_mode_integer = FALL_OFF_MODE.get(falloff_mode)
	if falloff_mode_integer is None:
		falloff_mode_integer = 0
		log.warning("Falloff mode '{}' is not supported, falling back to 'volume'.")

	cmds.setAttr("{}.falloffMode".format(soft_mod), falloff_mode_integer)

	# connect matrices
	cmds.connectAttr("{}.matrixSum".format(mm), "{}.weightedMatrix".format(soft_mod))
	cmds.connectAttr("{}.worldMatrix".format(base), "{}.preMatrix".format(soft_mod))
	cmds.connectAttr("{}.worldInverseMatrix".format(base), "{}.postMatrix".format(soft_mod))
	cmds.connectAttr("{}.outputTranslate".format(dm), "{}.falloffCenter".format(soft_mod))

	return soft_mod
