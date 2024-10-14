import logging

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds

log = logging.getLogger("smrig.lib.mathlib.common")

__all__ = [
	"remap",
	"get_distance_between",
	"get_bounding_box",
	"get_bounding_box_size",
	"get_center_from_bounding_box",
	"fibonacci",
	"get_point_between"
]


def remap(x, in_min, in_max, out_min, out_max):
	"""
	Remap value x between input min and max and output min and max.

	:param float x:
	:param float in_min:
	:param float in_max:
	:param float out_min:
	:param float out_max:
	:return: Remapped value
	:rtype: float
	"""
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def get_distance_between(source, target):
	"""
	Get the distance between two nodes in world space. No nodes are created
	during the retrieval of the distance. This function also makes it possible
	to get the distance between components, between two vertices for example.

	It is also possible to directly parse a world space position. This
	position needs to be a list containing 3 float/integer values.

	:param str/list source:
	:param str/list target:
	:return: Distance
	:rtype: float
	"""
	# get position
	if not isinstance(source, list):
		source_argument = {"rotatePivot": True} if not source.count(".") else {"translation": True}
		source = cmds.xform(source, query=True, worldSpace=True, **source_argument)
	if not isinstance(target, list):
		target_argument = {"rotatePivot": True} if not target.count(".") else {"translation": True}
		target = cmds.xform(target, query=True, worldSpace=True, **target_argument)

	return (OpenMaya.MVector(source) - OpenMaya.MVector(target)).length()


def get_bounding_box(points):
	"""
	Get the bounding box of the provided points. The bounding box will be
	calculated in world space. The provided point list should have points
	inside which are represented as a list ( x, y, z )

	:param list points:
	:return: Bounding box ( min x, min y, min z, max x, max y, max z )
	:rtype: list
	"""
	x, y, z = zip(*points)
	return [min(x), min(y), min(z), max(x), max(y), max(z)]


def get_center_from_bounding_box(nodes=None):
	"""
	Get exact world bounding box
	:param nodes:

	:return:
	"""
	nodes = nodes if nodes else cmds.ls(sl=1)
	bb = cmds.exactWorldBoundingBox(nodes, ii=1)

	return [(bb[3] + bb[0]) / 2, (bb[4] + bb[1]) / 2, (bb[5] + bb[2]) / 2]


def get_bounding_box_size(nodes=None):
	"""

	:param nodes:
	:return:
	"""
	nodes = nodes if nodes else cmds.ls(sl=1)
	bb = cmds.exactWorldBoundingBox(nodes, ii=1)

	return [(bb[3] - bb[0]), (bb[4] - bb[1]), (bb[5] - bb[2])]


def fibonacci(num):
	"""
	:param int num:
	:return: Fibonacci
	:rtype: int
	:raise ValueError: When the input number is not valid for fibonacci calculation
	"""
	if num < 1:
		error_message = "Unable to generate fibonacci number for {}, it is lower than 1.".format(num)
		log.error(error_message)
		raise ValueError(error_message)

	elif num == 1:
		return 0
	elif num == 2:
		return 1
	else:
		return fibonacci(num - 1) + fibonacci(num - 2)


def get_point_between(start, end, distance=0.5):
	"""
	:param start:
	:param end:
	:param distance:
	:return:
	"""
	return [(end[0] * distance) + (start[0] * (1.0 - distance)),
	        (end[1] * distance) + (start[1] * (1.0 - distance)),
	        (end[2] * distance) + (start[2] * (1.0 - distance))]
