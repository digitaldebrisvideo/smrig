import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.cmds as cmds


def get_weights(deformer):
	"""
	get deformer weights as list

	:param deformer:
	:return:
	"""
	try:
		if cmds.nodeType(deformer) in "skinCluster":
			return [get_skin_weights_array(deformer)]
		else:
			return get_deformer_weights_array(deformer)
	except:
		return [None] * len(cmds.deformer(deformer, q=1, g=1))


def get_skin_weights_array(deformer):
	"""
	Get skin weights and blend weights arrays

	:param str deformer:
	:return list: (weights, blend weights)
	"""
	weights = OpenMaya.MDoubleArray()
	blend_weights = OpenMaya.MDoubleArray()

	p_int_util = OpenMaya.MScriptUtil()
	p_int_util.createFromInt(0)
	p_int = p_int_util.asUintPtr()

	fn_skin = get_fn_deformer(deformer)
	cmpts_array = get_cmpts(deformer)

	dag_path = cmpts_array[0]
	cmpts = cmpts_array[1]

	fn_skin.getWeights(dag_path, cmpts, weights, p_int)
	fn_skin.getBlendWeights(dag_path, cmpts, blend_weights)

	return list(weights), list(blend_weights)


def get_deformer_weights_array(deformer):
	"""
	Get deformer weights array

	:param deformer:
	:return:
	"""
	fn_deformer = get_fn_deformer(deformer)
	cmpts_array = get_cmpts(deformer)

	results = []
	for idx, item in enumerate(cmpts_array):
		dag_path = item[0]
		cmpts = item[1]

		weight_array = OpenMaya.MFloatArray()
		fn_deformer.getWeights(dag_path, cmpts, weight_array)
		results.append(list(weight_array))

	return results


def convert_to_array(py_list, double_array=False):
	"""
	Convert a python list to an MFloatArray

	:param list py_list:
	:param double_array:
	:return: OpenMaya.MFloatArray
	"""
	array = create_double_array(len(py_list)) if double_array else create_float_array(len(py_list))

	for ii, value in enumerate(py_list):
		array.set(value, ii)

	return array


def convert_to_int_array(py_list):
	"""
	Convert a python list to an MFloatArray

	:param list py_list:
	:return: OpenMaya.MFloatArray
	"""
	array = create_int_array(len(py_list))

	for ii, value in enumerate(py_list):
		array.set(value, ii)

	return array


def create_float_array(length, value=None):
	"""
	Create an MFloatArray of given size

	:param length:
	:param value:
	:return:
	"""
	if value:
		return OpenMaya.MFloatArray(length, value)
	else:
		return OpenMaya.MFloatArray(length)


def create_double_array(length, value=None):
	"""
	Create an MFloatArray of given size

	:param length:
	:param value:
	:return:
	"""
	if value:
		return OpenMaya.MDoubleArray(length, value)
	else:
		return OpenMaya.MDoubleArray(length)


def create_int_array(length, value=None):
	"""
	Create an MIntArray of given size

	:param length:
	:param value:
	:return:
	"""
	if value:
		return OpenMaya.MIntArray(length, value)
	else:
		return OpenMaya.MIntArray(length)


def get_fn_deformer(deformer):
	"""
	Get MFnSkinCluster for skin cluster or MFnWeightGeometryFilter for all other deformers.

	:param deformer:
	:return:
	"""
	dep = get_dep(deformer)

	if cmds.nodeType(deformer) in "skinCluster":
		return OpenMayaAnim.MFnSkinCluster(dep)
	else:
		return OpenMayaAnim.MFnWeightGeometryFilter(dep)


def get_fn_cmpt(dag_path, cmpts):
	"""
	Get indexed component for geo dag path.

	:param OpenMaya.MDagPath dag_path:
	:param OpenMaya.MObject cmpts: components
	:return:
	"""
	node_type = cmds.nodeType(dag_path.fullPathName())
	if node_type in ["mesh", "nurbsCurve"]:
		return OpenMaya.MFnSingleIndexedComponent(cmpts)

	elif node_type in "nurbsSurface":
		return OpenMaya.MFnDoubleIndexedComponent(cmpts)

	elif node_type in "lattice":
		return OpenMaya.MFnTripleIndexedComponent(cmpts)


def get_cmpts(deformer):
	"""
	Wrapper for getting deformer sets from either set OR tags

	:param deformer:
	:return:
	"""
	try:
		return get_cmpts_from_set(deformer)
	except:
		return get_cmpts_from_tags(deformer)


def get_cmpts_from_tags(deformer):
	"""
	Get the mesh components from the  component tag expression

	:param deformer:
	:return:
	"""

	shapes = cmds.deformer(deformer, q=True, g=True)
	results = []
	tags = []

	for idx in cmds.getAttr("{}.input".format(deformer), mi=True):
		if cmds.listConnections("{}.input[{}].inputGeometry".format(deformer, idx)):
			tags.append(cmds.getAttr("{}.input[{}].componentTagExpression".format(deformer, idx)))

	for shape, tag in zip(shapes, tags):
		# Get the geo out attribute for the shape
		out_attr = cmds.deformableShape(shape, localShapeOutAttr=True)

		dep = get_dep(shape)
		plug = find_plug(dep, out_attr[0])
		fn_geo_data = OpenMaya.MFnGeometryData(plug.asMObject())

		# Components MObject
		components = fn_geo_data.resolveComponentTagExpression(tag)
		dag_path = OpenMaya.MDagPath.getAPathTo(dep)

		results.append((dag_path, components))

		if cmds.nodeType(deformer) in "skinCluster":
			return dag_path, components

	return results


def get_cmpts_from_set(deformer):
	"""
	Get deformer dag path and components from set

	:param deformer:
	:return:
	"""
	fn_deformer = get_fn_deformer(deformer)

	members = OpenMaya.MSelectionList()

	fn_set = OpenMaya.MFnSet(fn_deformer.deformerSet())
	fn_set.getMembers(members, False)

	geos = cmds.deformer(deformer, q=True, g=True)
	results = [None] * len(geos)

	for i in range(members.length()):
		dag_path = OpenMaya.MDagPath()
		components = OpenMaya.MObject()
		members.getDagPath(i, dag_path, components)

		idx = geos.index(dag_path.partialPathName())
		results[idx] = (dag_path, components)

		if cmds.nodeType(deformer) in "skinCluster":
			return dag_path, components

	return results


def get_dep(node):
	"""
	get depend node

	:param str node:
	:return: Maya dependency node
	:rtype: OpenMaya.MObject
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)

	obj = OpenMaya.MObject()
	sel.getDependNode(0, obj)

	return obj


def get_dag(node):
	"""
	Get dag path
	:param str node:
	:return: Maya dag path
	:rtype: OpenMaya.MDagPath
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)

	dag = OpenMaya.MDagPath()
	sel.getDagPath(0, dag)

	return dag


def get_plug(node):
	"""

	:param str node:
	:return: Maya plug node
	:rtype: OpenMaya.MPlug
	"""
	plug = OpenMaya.MPlug()
	sel = OpenMaya.MSelectionList()
	sel.add(node)
	sel.getPlug(0, plug)

	return plug


def find_plug(dep, attr):
	"""
	Find plug from depend node

	:param dep:
	:param attr:
	:return:
	"""
	fn_dep = OpenMaya.MFnDependencyNode(dep)
	return fn_dep.findPlug(attr, True)
