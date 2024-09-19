import logging
import math

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
from six import string_types

from smrig.lib import api2lib as apilib
from smrig.lib import decoratorslib
from smrig.lib import nodepathlib
from smrig.lib import nodeslib
from smrig.lib import selectionlib

log = logging.getLogger("smrig.lib.geometrylib.curve")

MIRROR_PLANE = {"x": [-1, 1, 1], "y": [1, -1, 1], "z": [1, 1, -1]}


def get_nearest_point_on_curve(curve, input):
	"""
	Return the neatest piint on curve world xforms and parameter

	:param str curve:
	:param str/list input: either a node or a list of floats [X, Y, Z]
	:return: world positions and parameter
	:rtype
	"""

	npoc = cmds.createNode("nearestPointOnCurve")
	cmds.connectAttr(curve + ".worldSpace", npoc + ".inputCurve")

	if isinstance(input, list):
		cmds.setAttr(npoc + ".inPositionX", input[0])
		cmds.setAttr(npoc + ".inPositionY", input[1])
		cmds.setAttr(npoc + ".inPositionZ", input[2])

	else:
		cmds.setAttr(npoc + ".inPositionX", cmds.xform(input, q=1, ws=1, t=1)[0])
		cmds.setAttr(npoc + ".inPositionY", cmds.xform(input, q=1, ws=1, t=1)[1])
		cmds.setAttr(npoc + ".inPositionZ", cmds.xform(input, q=1, ws=1, t=1)[2])

	result = list(cmds.getAttr(npoc + ".position")[0]) + [cmds.getAttr(npoc + ".parameter")]
	cmds.delete(npoc)

	return result


def create_curve(*args, **kwargs):
	"""
	A wrapper for the cmds.curve command. The benefit of this wrapper is that
	the shape node that gets created is renamed, which is something the
	original function does not do. The shape function is only renamed if the
	name attribute is used.

	It will also allow for the creation of periodic curves when no knots are
	provided. The knots are calculated in this function and added to the
	keyword arguments when creating the curve. The automatic calculation of
	the knots will only happen when either they are not provided and the
	points are defined in the "point" argument and not the "editPoint"
	argument.

	:param args:
	:param kwargs:
	:return: Curve
	:rtype: str
	"""
	# variables
	point = kwargs.get("point")[:]
	edit_point = kwargs.get("editPoint")
	periodic = kwargs.get("periodic")
	degree = kwargs.get("degree")
	knot = kwargs.get("knot")

	# validate periodic, we can only safely adjust the input value when the
	# edit point and knot argument are not defined and we do have values for
	# points, periodic and degree.
	if not edit_point and not knot and point and periodic and degree:
		# get the number of points
		num_points = len(point)

		# get knots
		start_knots = [0] * (degree - 1)
		end_knots = [num_points - degree] * (degree - 1)
		knot = start_knots + [x for x in range(num_points - degree + 1)] + end_knots

		if periodic:
			# when periodic the knots are a list
			knot = range(len(knot) + degree)

		if periodic and point[0] != point[num_points - degree]:
			# when periodic the start points have to be repeated by the length
			# of the degree
			point.extend(point[:degree])

		# update kwargs
		kwargs["knot"] = knot
		kwargs["point"] = point

	# create curve
	kwargs = {str(k): v for k, v in kwargs.items()}
	curve = cmds.curve(*args, **kwargs)

	# rename shape
	curve_shape = cmds.listRelatives(curve, type="nurbsCurve")[0]
	cmds.rename(curve_shape, "{}Shape".format(nodepathlib.get_leaf_name(curve)))

	return curve


def create_curve_from_points(points, name="curve#", degree=3, spans=None, periodic=False):
	"""
	Create a curve from reference points, these reference points can be actual
	world space positions or can be links to nodes or components which of
	which the position can be queried using the cmds.xform command.

	After creation it is possible to rebuild the curve using the number of
	spans desired. If the spans are left set to None the curve will not be
	rebuild. It is also possible to create a periodic curve if desired.

	:param list points:
	:param str name:
	:param int degree:
	:param int spans:
	:param bool periodic:
	:return: Curve
	:rtype: str
	:raise ValueError: When no valid points are found.
	"""
	# get positions
	positions = []
	for point in points:
		if isinstance(point, list) and len(point) == 3:
			positions.append(point)
		elif isinstance(point, string_types):
			# if the point parsed is a component we can only use the
			# translation to query the position, if it is not a component the
			# rotatePivot is used as this would make it work with clusters,
			# locators and frozen transforms.
			arguments = {"translation": True} if point.count(".") else {"rotatePivot": True}
			position = cmds.xform(point, query=True, worldSpace=True, **arguments)
			positions.append(position)
		else:
			log.warning("Unable to retrieve world space position from point '{}'.".format(point))

	# validate positions
	num_positions = len(positions)
	if num_positions < 2:
		error_message = "Unable to build curve as not enough valid points were found."
		log.error(error_message)
		raise ValueError(error_message)

	# validate degree
	degree_cache = degree
	if num_positions < degree + 1:
		degree = num_positions - 1
		log.warning(
			"Unable to use degree of '{}' as not enough points where defined, reverting to a degree of '{}'.".format(
				degree_cache,
				degree
			)
		)

	# create curve
	curve = create_curve(name=name, point=positions, degree=degree, periodic=periodic)

	# update curve
	if spans:
		cmds.rebuildCurve(
			curve,
			constructionHistory=False,
			replaceOriginal=True,
			rebuildType=0,
			endKnots=1,
			keepRange=1,
			keepControlPoints=0,
			keepEndPoints=True,
			keepTangents=False,
			degree=degree_cache,
			tolerance=0.01,
			spans=spans
		)

	return curve


@decoratorslib.preserve_selection
def create_curve_from_edges(edges, name, degree=3, spans=None, periodic=False):
	"""
	Create a curve from edges, it is up to the user to define if the curve
	should be periodic or not. The curve can be rebuild using the provided
	spans.

	:param list edges:
	:param str name:
	:param int degree:
	:param int spans:
	:param bool periodic:
	:return: Curve
	:rtype: str
	:raise ValueError: When no valid edges are found.
	"""
	# filter edges
	edges = cmds.filterExpand(edges, expand=True, selectionMask=32)

	# validate edges
	if not edges:
		error_message = "No valid edge found in the provided argument, {}.".format(edges)
		log.error(error_message)
		raise ValueError(error_message)

	# create curve
	cmds.select(edges)
	form = 2 if periodic else 0
	curve = cmds.polyToCurve(name=name, form=form, degree=degree, constructionHistory=False)[0]

	# update curve
	if spans:
		cmds.rebuildCurve(
			curve,
			constructionHistory=False,
			replaceOriginal=True,
			rebuildType=0,
			endKnots=1,
			keepRange=1,
			keepControlPoints=0,
			keepEndPoints=True,
			keepTangents=False,
			degree=degree,
			tolerance=0.01,
			spans=spans
		)

	return curve


def create_curve_link(targets, name=None, parent=None, degree=1, periodic=False, display_type="template",
                      replace_shapes=False):
	"""
	Create a curve link that is driven by the targets provided targets. This
	curve defaults to be a one degree curve as it tends to be used for display
	purposes to aid the animators. Obviously it can be used for other ends as
	well, which allows for the flexibility.

	:param list targets:
	:param str name:
	:param int degree:
	:param bool periodic:
	:param str display_type:
	:return: Curve
	:rtype: str
	"""
	# create curve
	name = name if name else "curve"
	curve = create_curve_from_points(targets, name=name, degree=degree, periodic=periodic)

	# drive curve
	for i, target in enumerate(targets):

		if parent:
			mmx = cmds.createNode('multMatrix', name="{}_{:03d}_MMX".format(name, i + 1))
			cmds.connectAttr(target + '.worldMatrix', mmx + '.matrixIn[0]')
			cmds.connectAttr(parent + '.worldInverseMatrix', mmx + '.matrixIn[1]')

			dcm = cmds.createNode("decomposeMatrix", name="{}_{:03d}_DMX".format(name, i + 1))
			cmds.connectAttr(mmx + '.matrixSum', dcm + '.inputMatrix')
			cmds.connectAttr(dcm + '.outputTranslate', "{}.controlPoints[{}]".format(curve, i))

		else:
			dm = cmds.createNode("decomposeMatrix", name="{}_{:03d}_DMX".format(name, i + 1))
			cmds.connectAttr("{}.worldMatrix".format(target), "{}.inputMatrix".format(dm))
			cmds.connectAttr("{}.outputTranslate".format(dm), "{}.controlPoints[{}]".format(curve, i))

	# set display type
	nodeslib.display.set_display_type(curve, display_type=display_type)

	if parent:
		if replace_shapes:
			shapes = selectionlib.get_shapes(parent)
			if shapes:
				cmds.delete(shapes)

		curve_shape = selectionlib.get_shapes(curve)
		curve_shape = cmds.parent(curve_shape, parent, r=True, s=True)
		curve_shape = cmds.rename(curve_shape[0], parent + "Shape")
		cmds.delete(curve)
		curve = curve_shape

	return curve


# ----------------------------------------------------------------------------


def extract_curve_creation_data(curve, precision=5, world_space=False):
	"""
	Get the curve creation dataexporter, the dataexporter is a dictionary that can be parsed
	into the :meth:`~create_curve` function to recreate the exact same curve.
	The method does return a list of dictionaries as it is possible for a
	transform to contain more than one curve shape.

	This function can be used for saving out template of control curves and
	other curve shapes that might be desired.

	:param str curve:
	:param int precision:
	:param bool world_space:
	:return: Curve creation dataexporter
	:rtype: list
	:raise ValueError: When no nurbs curves can be found.
	"""
	object_space = False if world_space else True

	# get curve shapes
	curve_shapes = selectionlib.extend_with_shapes(curve)
	curve_shapes = selectionlib.filter_by_type(curve_shapes, types="nurbsCurve")

	# validate curve shapes
	if not curve_shapes:
		return

	return [
		{
			"degree": cmds.getAttr("{}.degree".format(curve_shape)),
			"periodic": True if cmds.getAttr("{}.form".format(curve_shape)) == 2 else False,
			"point": [
				[
					round(value, precision)
					for value in
					cmds.xform(cv, query=True, objectSpace=object_space, worldSpace=world_space, translation=True)
				]
				for cv in cmds.ls("{}.cv[*]".format(curve_shape), flatten=True) or []
			]
		}
		for curve_shape in curve_shapes
	]


# ----------------------------------------------------------------------------


@decoratorslib.preserve_selection
def set_curve_direction(curve, axis="x", direction=1, world_space=True):
	"""
	Sometimes it is helpful to get the curve direction aligned a specific way.
	This function will allow you to do that. You can choose which axis the
	check is performed on and if the direction is supposed to be positive or
	negative. If the the provided curve doesn't match the criteria its
	direction will be reversed. The curves first and last cv are used to
	determine the direction.

	:param str curve:
	:param str axis: 'x', 'y' or 'z'
	:param int/float direction: 1 or -1
	:param bool world_space:
	"""
	# get curve position
	cvs = cmds.ls("{}.cv[*]".format(curve), flatten=True)
	cv1 = OpenMaya.MVector(cmds.xform(cvs[0], query=True, worldSpace=world_space, translation=True))
	cv2 = OpenMaya.MVector(cmds.xform(cvs[-1], query=True, worldSpace=world_space, translation=True))

	# get vectors
	curve_vector = cv2 - cv1
	direction_vector = OpenMaya.MVector([direction if axis == a else 0 for a in ["x", "y", "z"]])

	# validate angle
	if direction_vector.angle(curve_vector) > math.pi * 0.5:
		cmds.reverseCurve(curve, constructionHistory=False, replaceOriginal=True)
		log.debug("Reversed curve direction of '{}', to match axis '{}' "
		          "and direction '{}'.".format(curve, axis, direction))
	else:
		log.debug("Curve direction of '{}' matches axis '{}' "
		          "and direction '{}' and will be ignored.".format(curve, axis, direction))


# ----------------------------------------------------------------------------


def get_uniform_parameters_on_curve(curve, num):
	"""
	Get a list of parameters that will indicate a point on the curve which are
	evenly spaced based on the distance. When curves are already stretched or
	positioned evenly spacing the parameters will not evenly space point on
	the curve. This function will help get that result.

	:param str curve:
	:param int num:
	:return: Parameters
	:rtype: list
	"""
	# get curve fn
	dag = apilib.conversion.get_dag(curve)
	curve_fn = OpenMaya.MFnNurbsCurve(dag)

	# get length
	length = curve_fn.length()
	length_section = length / (num - 1)

	# get parameters at length
	return [
		curve_fn.findParamFromLength(i * length_section)
		for i in range(num)
	]


def get_uniform_points_on_curve(curve, num, world_space=True):
	"""
	Get a list of evenly spaces points on a curve. The points on the curve
	can be returned in local and world space.

	:param str curve:
	:param int num:
	:param bool world_space:
	:return: Points on curve
	:rtype: list
	"""
	# get space
	space = OpenMaya.MSpace.kWorld if world_space else OpenMaya.MSpace.kObject

	# get curve fn
	dag = apilib.conversion.get_dag(curve)
	curve_fn = OpenMaya.MFnNurbsCurve(dag)

	# get positions
	return [
		list(curve_fn.getPointAtParam(parameter, space))
		for parameter in get_uniform_parameters_on_curve(curve, num)
	]


def mirror_curve_data(curve_data, mirror):
	"""
	Mirror curve point dataexporter across plane

	:curve_data dict:
	:mirrorpart str: "x", "y", "z"
	:return: curve dataexporter
	:rtype: dict
	"""

	mirror_plane = MIRROR_PLANE[mirror.lower()]

	for index in range(len(curve_data)):
		point_data = curve_data[index].get('point')
		curve_data[index]['point'] = [[a * b for a, b in zip(p, mirror_plane)] for p in point_data]

	return curve_data


def rebuild_curve(curve, spans, degree=3, keep_history=False):
	"""
	Rebuild curve

	:param curve:
	:param spans:
	:param degree:
	:param keep_history:
	:return:
	"""
	crv = cmds.rebuildCurve(curve, ch=keep_history, rpo=1, rt=0, end=1, kr=0,
	                        kcp=0, kep=1, kt=0, s=spans, d=degree, tol=0.01)[0]
	return crv
