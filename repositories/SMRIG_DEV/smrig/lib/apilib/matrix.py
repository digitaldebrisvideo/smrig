import logging
import math

import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import sys

if sys.version_info[0] < 3:
    string_types = (str, unicode)
else:
    string_types = (str,)

from smrig.lib.apilib import conversion

log = logging.getLogger("smrig.lib.apilib.matrix")

ROTATION_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
ROW_MAPPER = {
	"x": 0,
	"y": 1,
	"z": 2,
	"translate": 3
}


def get_matrix_from_list(matrix_list):
	"""
	The old API doesn't have the constructors implemented to populate an
	MMatrix using a list.

	:param list matrix_list:
	:return: Matrix
	:rtype: OpenMaya.MMatrix
	"""
	matrix_index = 0
	matrix = OpenMaya.MMatrix()

	for i in range(4):
		for j in range(4):
			OpenMaya.MScriptUtil.setDoubleArray(matrix[i], j, matrix_list[matrix_index])
			matrix_index += 1

	return matrix


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
			matrix(row, i)
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
		OpenMaya.MScriptUtil.setDoubleArray(matrix[row], i, vector[i])


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
	translate = transformation_matrix.getTranslation(OpenMaya.MSpace.kWorld)
	translate = [round(value, precision) for value in [translate.x, translate.y, translate.x]]

	# get rotate
	rotate = transformation_matrix.eulerRotation()
	rotate.reorderIt(rotate_order)
	rotate = [round(math.degrees(value), precision) for value in [rotate.x, rotate.y, rotate.z]]

	# get scale
	scale_double_array = OpenMaya.MScriptUtil()
	scale_double_array.createFromList([0.0, 0.0, 0.0], 3)
	scale_double_array_ptr = scale_double_array.asDoublePtr()
	transformation_matrix.getScale(scale_double_array_ptr, OpenMaya.MSpace.kWorld)

	# Each of these is a decimal number reading from the pointer's reference
	scale_x = OpenMaya.MScriptUtil().getDoubleArrayItem(scale_double_array_ptr, 0)
	scale_y = OpenMaya.MScriptUtil().getDoubleArrayItem(scale_double_array_ptr, 1)
	scale_z = OpenMaya.MScriptUtil().getDoubleArrayItem(scale_double_array_ptr, 2)

	scale = [round(value, precision) for value in [scale_x, scale_y, scale_z]]

	return [
		translate,
		rotate,
		scale
	]


def decompose_node(node, world_space=True, precision=8):
	"""
	Decompose the matrix of a node in either world or local space and return
	the decomposed matrix which contains its translate, rotate, scale and
	rotation order values.

	:param str node:
	:param bool world_space:
	:param int precision:
	:return: Decompose matrix
	:rtype: list
	"""
	# get matrix
	matrix_plug = "worldMatrix" if world_space else "matrix"
	matrix = get_matrix_from_plug("{}.{}".format(node, matrix_plug))

	# get rotation order
	rotate_order = cmds.getAttr("{}.rotateOrder".format(node))

	# get xforms
	xforms = decompose_matrix(matrix, rotate_order=rotate_order, precision=precision)
	xforms.append(rotate_order)

	return xforms


# ----------------------------------------------------------------------------


def get_offset_matrix(parent, child):
	"""
	Get the offset matrix between the provided parent and child. The offset
	matrix is calculated by multiplying the world matrix of the child with the
	world inverse matrix of the parent.

	:param str parent:
	:param str child:
	:return: Offset matrix
	:rtype: OpenMaya.MMatrix
	"""
	parent_matrix = get_matrix_from_plug("{}.worldMatrix".format(parent))
	child_matrix = get_matrix_from_plug("{}.worldMatrix".format(child))
	return child_matrix * parent_matrix.inverse()
