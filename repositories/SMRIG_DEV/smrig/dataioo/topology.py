import logging

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
from smrig.dataioo import utils

log = logging.getLogger("deformerIO.topology")


def get_transfer_geo_data(geos):
	"""
	Wrapper for exporting mesh data

	:param geos:
	:return:
	"""
	shapes = [utils.get_orig_shape(g) for g in geos]
	return [get_mesh_data(s, get_name=False) for s in shapes]


def create_mesh(name, matrix, points, poly_connects, poly_count, uvs, uv_ids, uv_counts):
	"""
	Create a new mesh and position it using its matrix, points and triangles.
	This function can be used in unison with the
	:meth:`~get_mesh_data`, which returns the matrix, points and
	triangles using in the correct format.

	:param str name:
	:param list matrix:
	:param list points:
	:param list triangles:
	:return: Mesh transform and shape
	:rtype: tuple
	"""
	polygon_connects = OpenMaya.MIntArray(poly_connects)
	polygon_counts = OpenMaya.MIntArray(poly_count)
	points = OpenMaya.MPointArray(points)

	uarray = OpenMaya.MFloatArray(uvs[0])
	varray = OpenMaya.MFloatArray(uvs[1])
	uv_ids_array = OpenMaya.MFloatArray(uv_ids)
	uv_counts_array = OpenMaya.MFloatArray(uv_counts)

	translate, rotate, scale, rotate_order = matrix

	# create mesh
	shape = OpenMaya.MFnMesh()
	shape.create(points,
	             polygon_counts,
	             polygon_connects,
	             uarray,
	             varray)

	shape.setUVs(uarray, varray)
	shape.assignUVs(uv_counts_array, uv_ids_array)
	shape.updateSurface()

	cmds.sets(shape.name(), edit=True, forceElement="initialShadingGroup")

	# get transform
	transform = utils.get_transform(shape.name())
	transform = cmds.rename(transform, name)

	# decompose matrix
	cmds.setAttr("{}.rotateOrder".format(transform), rotate_order)
	cmds.xform(transform, worldSpace=True, translation=translate, rotation=rotate)
	cmds.xform(transform, relative=True, scale=scale)

	return transform, shape.name()


def get_mesh_data(shape, get_name=True):
	"""
	Extract the mesh creation dataexporter using the api. This creation dataexporter can be
	used to re-create that mesh. The dataexporter will be returned in a dictionary
	format where the matrix of the transform, the points and the triangles of
	the mesh are saved.

	:param str geo:
	:raise RuntimeError: When the shape doesn't exist.
	:raise ValueError: When the shape is not a mesh.
	"""

	# validate
	if not cmds.objExists(shape):
		return {}

	node_type = cmds.nodeType(shape)
	if node_type != "mesh":
		return {}

	# get matrix
	transform = utils.get_transform(shape, full_path=True)
	mesh_matrix = utils.decompose_node(transform)

	# get mesh dataexporter
	mesh_dep = utils.get_dep(shape)
	mesh_fn = OpenMaya.MFnMesh(mesh_dep)

	mesh_points = mesh_fn.getPoints(OpenMaya.MSpace.kObject)
	mesh_points = [list(point)[:3] for point in mesh_points]

	poly_connects = [mesh_fn.getPolygonVertices(i) for i in range(mesh_fn.numPolygons)]
	poly_count = [len(i) for i in poly_connects]

	flatten = lambda l: [item for sublist in l for item in sublist]
	poly_connects = flatten(poly_connects)

	uvs = [[i for i in l] for l in mesh_fn.getUVs()]
	uv_counts, uv_ids = [[i for i in l] for l in mesh_fn.getAssignedUVs()]

	data = {"matrix": mesh_matrix,
	        "points": mesh_points,
	        "poly_connects": poly_connects,
	        "poly_count": poly_count,
	        "uvs": uvs,
	        "uv_ids": uv_ids,
	        "uv_counts": uv_counts}

	if get_name:
		data["name"] = shape

	return data


# Other mesh utilites ---------------------------------------------------------------------


def compare_topology(shape1, shape2=None, shape2_data=None, key="poly_connects", uv_exists=False):
	"""
	Comapre the topology of two meshes

	:param shape1:
	:param shape2:
	:param key:
	:return:
	"""
	shape1 = utils.get_shapes(shape1)
	dat1 = get_mesh_data(shape1[0])

	shape2 = utils.get_shapes(shape2) if shape2 else None
	dat2 = shape2_data if shape2_data else get_mesh_data(shape2[0])

	result = dat1.get(key) == dat2.get(key)

	if uv_exists and dat1.get("uvs") and dat2.get("uvs"):
		result = True

	if not result:
		log.warning("{} & {} do NOT match".format(shape1, shape2))

	return result
