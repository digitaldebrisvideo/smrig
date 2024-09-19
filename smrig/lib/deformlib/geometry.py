import logging

import maya.cmds as cmds

from smrig.lib import selectionlib

log = logging.getLogger("smrig.lib.deformlib.geometry")


def add_geometry_to_non_linear_deformer(deformer, geometry):
	"""
	:param str deformer: The deformer node
	:param str/list geometry: Geometry to add to deformer
	:raise ValueError: When no valid geometry is provided
	:raise ValueError: When no valid deformer is provided
	"""
	# get geometry as list
	shapes = selectionlib.extend_with_shapes(geometry)
	shapes = [shape for shape in shapes if cmds.nodeType(shape) != "transform"]

	# validate geometry
	if not shapes:
		error_message = "Provided geometry '{}' is not valid!".format(geometry)
		log.error(error_message)
		raise ValueError(error_message)

	# get deformer set
	non_linear_deformer = selectionlib.filter_by_type(deformer, types="nonLinear")

	# validate deformer
	if not non_linear_deformer:
		error_message = "Provided deformer '{}' is not a non linear deformer!".format(deformer)
		log.error(error_message)
		raise ValueError(error_message)

	# get deformer set
	deformer_set = cmds.listConnections(non_linear_deformer, type="objectSet")[0]

	# add geometry
	cmds.sets(shapes, addElement=deformer_set)
