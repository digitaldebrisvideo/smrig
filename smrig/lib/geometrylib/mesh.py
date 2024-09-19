import logging

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds

from smrig.lib import api2lib as apilib
from smrig.lib import selectionlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.geometrylib.mesh")


def create_mesh(name, matrix, points, triangles):
	"""
	Create a new mesh and position it using its matrix, points and triangles.
	This function can be used in unison with the
	:meth:`~extract_mesh_creation_data`, which returns the matrix, points and
	triangles using in the correct format.

	:param str name:
	:param list matrix:
	:param list points:
	:param list triangles:
	:return: Mesh transform and shape
	:rtype: tuple
	"""
	# TODO: implement creation of normals, uvs, non-triangular faces etc.

	# get dataexporter
	num_polygons = len(triangles) / 3
	polygon_connects = OpenMaya.MIntArray(triangles)
	polygon_counts = OpenMaya.MIntArray([3] * num_polygons)
	points = OpenMaya.MPointArray(points)

	# create mesh
	shape = OpenMaya.MFnMesh()
	shape.create(
		points,
		polygon_counts,
		polygon_connects
	)

	# get transform
	transform = selectionlib.get_transform(shape.name())
	transform = cmds.rename(transform, name)

	# decompose matrix
	translate, rotate, scale, rotate_order = matrix

	# position transform
	cmds.setAttr("{}.rotateOrder".format(transform), rotate_order)
	cmds.xform(transform, worldSpace=True, translation=translate, rotation=rotate)
	cmds.xform(transform, relative=True, scale=scale)

	return transform, shape.name()


def extract_mesh_creation_data(shape):
	"""
	Extract the mesh creation dataexporter using the api. This creation dataexporter can be
	used to re-create that mesh. The dataexporter will be returned in a dictionary
	format where the matrix of the transform, the points and the triangles of
	the mesh are saved.

	:param str shape:
	:raise RuntimeError: When the shape doesn't exist.
	:raise ValueError: When the shape is not a mesh.
	"""
	# TODO: implement extraction of normals, uvs etc?
	# validate
	if not cmds.objExists(shape):
		error_message = "Provided shape '{}' doesn't exist in the current scene.".format(shape)
		log.error(error_message)
		raise RuntimeError(error_message)

	node_type = cmds.nodeType(shape)
	if node_type != "mesh":
		error_message = "Provided shape '{}' is of type '{}' and should be of type 'mesh'.".format(shape, node_type)
		log.error(error_message)
		raise ValueError(error_message)

	# get matrix
	# TODO: just store and set matrix directly?
	transform = selectionlib.get_transform(shape, full_path=True)
	mesh_matrix = apilib.matrix.decompose_node(transform)

	# get mesh dataexporter
	mesh_dep = apilib.conversion.get_dep(shape)
	mesh_fn = OpenMaya.MFnMesh(mesh_dep)

	mesh_triangles = list(mesh_fn.getTriangles()[1])
	mesh_points = mesh_fn.getPoints(OpenMaya.MSpace.kObject)
	mesh_points = [list(point)[:3] for point in mesh_points]

	return {
		"matrix": mesh_matrix,
		"points": mesh_points,
		"triangles": mesh_triangles
	}


# ----------------------------------------------------------------------------


def delete_color_sets(meshes):
	"""
	Removes any and all color sets attached the provided meshes.

	:param str/list meshes:
	"""
	meshes = utilslib.conversion.as_list(meshes)
	for mesh in meshes:
		color_sets = cmds.polyColorSet(mesh, query=True, allColorSets=True) or []
		for color_set in color_sets:
			cmds.polyColorSet(mesh, delete=True, colorSet=color_set)


def delete_all_color_sets():
	"""
	Removes any and all color sets that is currently in the scene.
	"""
	meshes = cmds.ls(type="mesh", noIntermediate=True) or []
	delete_color_sets(meshes)
