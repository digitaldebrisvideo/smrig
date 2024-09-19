import logging
import math

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
from six import string_types

from . import conversion

log = logging.getLogger("smrig.lib.api2lib.matrix")

ROTATION_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
ROW_MAPPER = {
	"x": 0,
	"y": 1,
	"z": 2,
	"translate": 3
}


def get_matrix_from_list(matrix_list):
	"""
	:param list matrix_list:
	:return: Matrix
	:rtype: OpenMaya.MMatrix
	"""
	return OpenMaya.MMatrix(matrix_list)


def get_matrix_from_plug(matrix_plug):
	"""
	:param str matrix_plug:
	:return: Matrix
	:rtype: OpenMaya.MMatrix
	"""
	plug = conversion.get_plug(matrix_plug)
	matrix_obj = plug.asMObject()
	matrix_data = OpenMaya.MFnMatrixData(matrix_obj)
	return matrix_data.matrix()


# ----------------------------------------------------------------------------


def get_row(matrix, row=0):
	"""
	Extract a row from the provided OpenMaya.MMatrix node into an
	OpenMaya.MVector. The provided row can be an integer or a string using
	the ROW_MAPPER variable. An ValueError will be thrown if the row cannot
	be determined.

	:param OpenMaya.MMatrix matrix:
	:param str/int row:
	:return: Row
	:rtype: OpenMaya.MVector
	:raise ValueError: When row cannot be determined.
	"""
	if isinstance(row, string_types):
		row_ = row
		row = ROW_MAPPER.get(row)
		if row is None:
			error_message = "Provided row '{}' is not valued, options are {}.".format(row_, ROW_MAPPER.keys())
			log.error(error_message)
			raise ValueError(error_message)

	return OpenMaya.MVector(
		[
			matrix.getElement(row, i)
			for i in range(3)
		]
	)


def set_row(matrix, vector, row=0):
	"""
	Set a row on a matrix using an MVector and a row. The provided row can be
	an integer or a string using the ROW_MAPPER variable. An ValueError will
	be thrown if the row cannot be determined.

	:param OpenMaya.MMatrix matrix:
	:param OpenMaya.MVector vector:
	:param str/int row:
	:raise ValueError: When row cannot be determined.
	"""
	if isinstance(row, string_types):
		row_ = row
		row = ROW_MAPPER.get(row)
		if row is None:
			error_message = "Provided row '{}' is not valued, options are {}.".format(row_, ROW_MAPPER.keys())
			log.error(error_message)
			raise ValueError(error_message)

	for i in range(3):
		matrix.setElement(row, i, vector[i])


# ----------------------------------------------------------------------------


def decompose_matrix(matrix, rotate_order="xyz", precision=8):
	"""
	Decompose a MMatrix into its translate, rotate and scales values. The
	rotational values are determined using the provided rotation order which
	defaults to "xyz".

	:param OpenMaya.MMatrix matrix:
	:param int/str rotate_order: "xyz", "yzx", "zxy", "xzy", "yxz" or "zyx"
	:param int precision:
	:return: Decompose matrix
	:rtype: list
	"""
	# get transformation matrix
	transformation_matrix = OpenMaya.MTransformationMatrix(matrix)

	# get translate
	translate = transformation_matrix.translation(OpenMaya.MSpace.kWorld)
	translate = [round(value, precision) for value in list(translate)]

	# get rotate
	rotate = transformation_matrix.rotation()
	rotate.reorderIt(rotate_order)
	rotate = [round(math.degrees(value), precision) for value in list(rotate)]

	# get scale
	scale = transformation_matrix.scale(OpenMaya.MSpace.kWorld)
	scale = [round(value, precision) for value in list(scale)]

	return [
		translate,
		rotate,
		scale
	]


def decompose_node(node, world_space=True, precision=8, matrix_plug=None):
	"""
	Decompose the matrix of a node in either world or local space and return
	the decomposed matrix which contains its translate, rotate, scale and
	rotation order values.

	:param str node:
	:param bool world_space:
	:param int precision:
	:param str matrix_plug:
	:return: Decompose matrix
	:rtype: list
	"""
	# get matrix
	matrix_plug = matrix_plug if matrix_plug else "worldMatrix" if world_space else "matrix"
	matrix = get_matrix_from_plug("{}.{}".format(node, matrix_plug))

	# get rotation order
	rotate_order = cmds.getAttr("{}.rotateOrder".format(node))

	# get xforms
	xforms = decompose_matrix(matrix, rotate_order=rotate_order, precision=precision)
	xforms.append(rotate_order)

	return xforms


# ----------------------------------------------------------------------------


def get_offset_matrix(parent, child, parent_matrix_plug="worldMatrix", child_matrix_plug="worldMatrix"):
	"""
	Get the offset matrix between the provided parent and child. The offset
	matrix is calculated by multiplying the world matrix of the child with the
	world inverse matrix of the parent.

	:param str parent:
	:param str child:
	:param str parent_matrix_plug:
	:param str child_matrix_plug:
	:return: Offset matrix
	:rtype: OpenMaya.MMatrix
	"""
	parent_matrix = get_matrix_from_plug("{}.{}".format(parent, parent_matrix_plug))
	child_matrix = get_matrix_from_plug("{}.{}".format(child, child_matrix_plug))
	return child_matrix * parent_matrix.inverse()
