import math

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds

from smrig.lib import nodepathlib
from smrig.lib import nodeslib
from smrig.lib.kinematicslib import ik


def get_pole_position(start_joint, middle_joint, end_joint, offset=None):
	"""
	Get a world space position of a pole vector using only the start middle
	and end joint. If the offset is left to None it will be calculated using
	the half the length of the chain.

	:param str start_joint:
	:param str middle_joint:
	:param str end_joint:
	:param int/float/None offset:
	:return: Pole position
	:rtype: list
	"""
	# get joint positions
	start_pos = OpenMaya.MVector(cmds.xform(start_joint, query=True, worldSpace=True, translation=True))
	middle_pos = OpenMaya.MVector(cmds.xform(middle_joint, query=True, worldSpace=True, translation=True))
	end_pos = OpenMaya.MVector(cmds.xform(end_joint, query=True, worldSpace=True, translation=True))

	# get vectors from the start to the middle and end
	vec1 = end_pos - start_pos
	vec2 = middle_pos - start_pos

	# get up vector
	up = vec1 ^ vec2

	# when the vectors 1 and 2 are perfectly in line the length of the up
	# vector is 0, when this is the case default is calculated as the -z
	# vector from the start joint.
	if up.length() < 0.0000001:
		# TODO: test to make sure this works always
		matrix = OpenMaya.MMatrix(cmds.xform(start_joint, query=True, worldSpace=True, matrix=True))
		up = OpenMaya.MVector(0, 0, -1) * matrix

	# get side vector
	side = up ^ vec1

	# get offset
	if not offset:
		offset = ((start_pos - middle_pos).length() + (middle_pos - end_pos).length()) * 0.5

	# get position taking the middle pos as the base and adding the
	# multiplication of the normalized vector and the offset.
	pos = middle_pos + (side.normal() * offset)
	return list(pos)


def get_pole_position_from_ik_handle(ik_handle, offset=None):
	"""
	Get a world space position of a pole vector from an ik handle. If the
	offset is left to None it will be calculated using the half the length of
	the chain.

	If the joint chain is longer than 2 joints the :meth:`~get_pole_position`
	method will be used to get the pole position.

	If only two joints are driven using the IK handle that method can't be
	used. If that is the case we can fall back on getting the pole vector from
	the IK handle itself.

	:param str ik_handle:
	:param int/float/None offset:
	:return: Pole position
	:rtype: list
	"""
	# get joint chain
	chain = ik.get_joint_chain_from_ik_handle(ik_handle)
	num = len(chain)

	# get pole position from middle joint
	if num > 2:
		middle_joint_index = int(math.floor((num - 1) * 0.5))
		middle_joint = chain[middle_joint_index]

		# get pole pos
		return get_pole_position(chain[0], middle_joint, chain[-1], offset)

	# It is possible to create an ik handle between two joints, if this is the
	# case the pole position will have to be retrieved from the ik handle
	# using its pole vector as no middle joint exists.
	start_pos = OpenMaya.MVector(cmds.xform(chain[0], query=True, worldSpace=True, translation=True))
	end_pos = OpenMaya.MVector(cmds.xform(chain[-1], query=True, worldSpace=True, translation=True))
	direction = OpenMaya.MVector(cmds.getAttr("{}.poleVector".format(ik_handle))[0]).normal()

	# get offset
	if not offset:
		offset = (start_pos - end_pos).length() * 0.5

	# get pole pos
	pos = start_pos + (direction * offset)
	return list(pos)


def create_pole_locator(ik_handle, offset=None, local_scale=0.25):
	"""
	Create a pole vector constraint using the ik handle. A locator will be
	created and positioned using the middle of the joint chain the ik handle
	is driving and the starting point and offsetting the locator in the
	direction found using the triangle of start, middle and end joint. The
	offset of this distance can be either set or automatically calculated.

	:param str ik_handle:
	:param int/float/None offset:
	:param int/float local_scale:
	:return: Pole locator
	:type: str
	"""
	# get pole position
	position = get_pole_position_from_ik_handle(ik_handle, offset)

	# create locator
	# TODO: update naming?
	locator = nodeslib.create.locator(
		name="{}_pole_LOC".format(ik_handle),
		position=position,
		local_scale=local_scale
	)

	# create constraint
	ik_handle_name = nodepathlib.get_leaf_name(ik_handle)
	cmds.poleVectorConstraint(locator, ik_handle, name="{}_PVC".format(ik_handle_name))

	return locator
