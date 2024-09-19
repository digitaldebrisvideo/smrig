import functools
import logging
import math
import os
import time

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
from six import string_types
from smrig import env

log = logging.getLogger("deformerIO.utils")
remap_file = os.path.join(env.asset.get_data_path(), "remap.json")


def get_deformer_geo_and_indices(deformer):
	"""
	Get a list of the connected deformer indices

	:param deformer:
	:return:
	"""
	indices = []
	geos = cmds.deformer(deformer, q=True, g=True)

	for idx in cmds.getAttr("{}.input".format(deformer), mi=True):
		if cmds.listConnections("{}.input[{}].inputGeometry".format(deformer, idx)):
			indices.append(idx)

	return indices, geos


def get_mesh_cmpts_from_tag(shape, tag=None):
	"""
	Get mesh components from tag as list
	:param shape:
	:param tag:
	:return:
	"""
	tag = tag if tag else "*"
	out_attr = cmds.deformableShape(shape, localShapeOutAttr=True)[0]
	return cmds.geometryAttrInfo("{}.{}".format(shape, out_attr), componentTagExpression=tag, components=True)


def get_mesh_cmpts_from_set(deformer):
	"""
	Get mesh components from object set as list

	:param deformer:
	:return:
	"""
	geos = cmds.deformer(deformer, q=True, g=True)
	results = []

	deformer_set = cmds.listConnections(deformer, type="objectSet")
	if not deformer_set:
		return

	cmpts_flat = cmds.sets(deformer_set[0], q=1)
	cmpts_dict = {k.split(".")[0]: [] for k in cmpts_flat}

	for item in cmpts_flat:
		items = item.split(".")
		cmpts_dict[items[0]].append(items[1])

	for geo in geos:
		results.append(cmpts_dict.get(get_transform(geo)))

	return results


def get_required_nodes(data):
	"""
	Get required nodes this is a blanket function to catch all deformer and constraint types
	:param data:
	:return:
	"""
	nodes = []
	nodes += [d.get("name") for d in data.get("geometry", [])]
	nodes += [d.get("name") for d in data.get("transforms", []) if d.get("required", True)]
	nodes += [d.get("sdk_driver") for d in data.get("curves", [])]
	nodes += data.get("joints", [])
	nodes += data.get("nodes", [])
	nodes += data.get("drivers", [])
	nodes += data.get("driven", [])
	nodes += data.get("wuo", [])

	for cnn in data.get("connections", []) or []:
		nodes.extend(cnn)

	for cnn in data.get("assignments", []) or []:
		nodes.extend(cnn)

	return list(set([n.split(".")[0] for n in nodes]))


def get_missing_nodes(nodes):
	"""
	Get a list of missing nodes:

	:param nodes:
	:return:
	"""
	return [n for n in nodes if not cmds.objExists(n)]


def remap_dict(dict_list, remap, key="name"):
	"""
	Remap node list of dicts with search and replace

	:param dict_list:
	:param remap:
	:param key:
	:return:
	"""
	for search, replace in remap:
		for i in range(len(dict_list)):
			dict_list[i][key] = dict_list[i].get(key).replace(search, replace)
	return dict_list


def remap_list(nodes, remap):
	"""
	Remap node list with search and replace

	:param nodes:
	:param remap:
	:return:
	"""
	for search, replace in remap:
		nodes = [j.replace(search, replace) for j in nodes]
	return nodes


def remap_nested_list(nested_list, remap):
	"""
	Remap node list with search and replace

	:param nodes:
	:param remap:
	:return:
	"""
	for search, replace in remap:
		for i, plist in enumerate(nested_list):
			nested_list[i] = [i.replace(search, replace) for i in plist]

	return nested_list


def swap_node_connections(source, target, delete_source=False):
	"""
	Swap connections from source to target

	:param source:
	:param target:
	:param delete_source:
	:return:
	"""
	connections = cmds.listConnections(source, s=0, d=1, p=1)
	for cnn in connections:
		try:
			src = cmds.listConnections(cnn, d=0, s=1, p=1)
			if src:
				cmds.connectAttr(src[0].replace(source, target), cnn, f=1)
		except:
			pass

	# connect incoming connections
	connections = cmds.listConnections(source, s=1, d=0, p=1)
	for cnn in connections:
		try:
			src = cmds.listConnections(cnn, d=1, s=0, p=1)
			cmds.connectAttr(cnn, src[0].replace(source, target), f=1)
		except:
			pass

	if delete_source:
		cmds.delete(source)


def get_sdk(node):
	"""
	Get setdriven keyframes from node

	:param str node:
	:return:
	"""
	crvs = cmds.listConnections(node, s=1, d=0, type="animCurve", scn=1) or []
	sdks = [c for c in crvs if cmds.listConnections(c + ".input", s=1, d=0, p=1, scn=1)]

	return sdks


def get_connections(node, as_string=False):
	"""

	:param node:
	:param as_string:
	:return:
	"""
	connections = []
	excluded_types = ["animCurve", "blendWeighted", "Constraint"]

	attrs = [a for a in cmds.listAttr(node, k=1) or [] if "." not in a] + ["t", "r", "s", "scale[0]"]
	if cmds.nodeType(node) == "blendShape":
		attrs.extend(["weight[{0}]".format(i) for i in range(cmds.blendShape(node, q=1, wc=1))])

	for attr in attrs:
		if cmds.objExists(node + "." + attr):
			source_connecitons = cmds.listConnections(node + "." + attr, s=1, d=0, p=1, scn=1) or []

			if source_connecitons:
				for src_conneciton in source_connecitons:

					passed_check = True
					for exluded in excluded_types:
						if exluded in cmds.nodeType(src_conneciton):
							passed_check = False

					if cmds.objExists(src_conneciton.split(".")[0] + ".smrigMatrixConstraint"):
						passed_check = False

					if passed_check:
						if as_string:
							connections.append("{}, {}".format(src_conneciton, "{}.{}".format(node, attr)))
						else:
							connections.append([src_conneciton, "{}.{}".format(node, attr)])

	return connections


def get_deformers(shape, dtype=None):
	"""

	:param shape:
	:param dtype:
	:return:
	"""
	deformers = cmds.findDeformers(shape)

	if deformers:
		if dtype:
			deformers = [d for d in deformers if cmds.nodeType(d) in dtype]

	return deformers


def get_transform(node, **kwargs):
	"""
	Get transform from specified node

	:param node:
	:return:
	"""
	if cmds.nodeType(node) in ["mesh", "nurbsCurve", "nurbsSurface", "locator", "lattice", "baseLattice"]:
		return cmds.listRelatives(node, p=True)[0]
	else:
		return node


def get_shapes(node, **kwargs):
	"""
	Get shape from specified node

	:param node:
	:return:
	"""
	if cmds.nodeType(node) in ["transform", "joint"]:
		return cmds.listRelatives(node, s=True, ni=True)
	else:
		return as_list(node)


def get_parent(node):
	"""
	Get node parent.

	:param node:
	:return:
	"""
	parent = cmds.listRelatives(node, parent=True)
	return parent[0] if parent else None


def get_orig_shape(node):
	"""
	Get original shape of node

	:param node:
	:return:
	"""
	transform = get_transform(node)
	shapes = get_shapes(transform) or []
	all_shapes = [s for s in cmds.listRelatives(transform, s=True, ni=False) or [] if s not in shapes]
	if all_shapes:
		return all_shapes[0]
	else:
		return shapes[0]


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

	return [translate, rotate, scale]


def get_plug(node):
	"""
	Get plug - py api 2

	:param str node:
	:return: Maya plug node
	:rtype: OpenMaya.MPlug
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)
	return sel.getPlug(0)


def find_plug(dep, attr):
	"""
	Find plug from dependency node - py api 2

	:param dep:
	:param attr:
	:return:
	"""
	fn_dep = OpenMaya.MFnDependencyNode(dep)
	plug = fn_dep.findPlug(attr, True)
	return plug.asMObject()


def get_matrix_from_plug(matrix_plug):
	"""
	Get matrix from plug - py api 2

	:param str matrix_plug:
	:return: Matrix
	:rtype: OpenMaya.MMatrix
	"""
	plug = get_plug(matrix_plug)
	matrix_obj = plug.asMObject()
	matrix_data = OpenMaya.MFnMatrixData(matrix_obj)
	return matrix_data.matrix()


def get_dep(node):
	"""
	Get dependancy node - py api 2

	:param str node:
	:return: Maya dependency node
	:rtype: OpenMaya.MObject
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)


def get_dag_path(dep):
	"""
	Get dag path from dependency node - py api 2

	:param dep:
	:return:
	"""
	return OpenMaya.MDagPath.getAPathTo(dep)


def tag_export_data_nodes(nodes, data=None):
	"""

	:param nodes:
	:param data:
	:return:
	"""
	for node in as_list(nodes):
		if not cmds.objExists(node + ".exportData"):
			cmds.addAttr(node, ln="exportData", dt="string")
			data = data if data else {}
			cmds.setAttr(node + ".exportData", str(data), type="string")


def get_export_data_nodes(nodes=None):
	"""

	:return:
	"""
	nodes = as_list(nodes) if nodes else cmds.ls()
	return [n for n in nodes if cmds.objExists(n + ".exportData")]


def untag_export_data_nodes(nodes=None):
	"""

	:param nodes:
	:return:
	"""
	nodes = as_list(nodes) if nodes else cmds.ls()
	nodes = [n for n in nodes if cmds.objExists(n + ".exportData")]
	for node in nodes:
		cmds.deleteAttr("{}.exportData".format(node))


def delete_export_data_nodes():
	"""
	Remove all imported ".exportData" nodes in scene.

	:return:
	"""
	nodes = cmds.ls('*.exportData')
	if nodes:
		cmds.delete([n.replace('.exportData', '') for n in nodes])


def as_list(data):
	"""
	Convert any data type into a list.

	:param str/list/tuple/None data:
	:return: Selection
	:rtype: list
	:raise ValueError: When the provided type is not supported
	"""
	if data is None:
		return []
	elif isinstance(data, string_types):
		return [data]
	elif isinstance(data, list):
		return data
	elif isinstance(data, tuple):
		return list(data)
	elif isinstance(data, int):
		return [data]
	elif isinstance(data, float):
		return [data]

	log.warning("Unable to convert type '{}' to list.".format(type(data)))


def timer(func):
	"""
	The timer decorator will print the fill name of the function and the
	duration of the execution of that function. This is ideal to keep track
	of more time consuming methods and benchmark their speed.
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		# get module
		full_name = []

		# get class, classes are parsed as self into functions, this means that it
		# is possible the first argument parsed into the function can be used to
		# extract the class name
		if args and "__class__" in dir(args[0]):
			full_name.append(args[0].__class__.__name__)

		# append name
		full_name.append(func.__name__)
		full_name = ".".join(full_name)

		# store time
		t = time.time()

		# call function
		ret = func(*args, **kwargs)

		# print time it took function to run
		log.info("{0} was executed in {1:.3f} seconds".format(full_name, time.time() - t))
		return ret

	return wrapper


def preserve_selection(func):
	"""
	The preserve selection function will store the current selection in maya
	before the function is ran and will restore it once the function has
	completed.
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		selection = cmds.ls(sl=True)
		ret = func(*args, **kwargs)

		if selection:
			try:
				if selection:
					cmds.select(selection, noExpand=True)
				else:
					cmds.select(clear=True)
			except:
				cmds.select(clear=True)
		else:
			cmds.select(clear=True)
		return ret

	return wrapper
