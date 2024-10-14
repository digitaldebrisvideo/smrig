import logging

import maya.OpenMaya as OpenMaya

log = logging.getLogger("smrig.lib.apilib.vector")

AXIS_VECTORS = {
	"x": OpenMaya.MVector.xAxis,
	"y": OpenMaya.MVector.yAxis,
	"z": OpenMaya.MVector.zAxis,
	"-x": OpenMaya.MVector.xNegAxis,
	"-y": OpenMaya.MVector.yNegAxis,
	"y-z": OpenMaya.MVector.zNegAxis,
}


def get_vector_from_axis(axis):
	"""
	:param axis: "x", "y", "z", "-x", "-y", "-z"
	:return: Vector
	:rtype: OpenMaya.MVector
	:raise ValueError: When no vector is associated with the provided axis.
	"""
	vector = AXIS_VECTORS.get(axis.lower())

	if not vector:
		error_message = "Axis '{}' has not vector associated with it, options: {}.".format(axis, AXIS_VECTORS.keys())
		log.error(error_message)
		raise ValueError(error_message)

	return vector
