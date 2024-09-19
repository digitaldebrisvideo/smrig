import logging

from maya import cmds as cmds
from smrig.dataioo import api
from smrig.dataioo import topology
from smrig.dataioo import utils

log = logging.getLogger("deformerIO.tools")


# Functions for setting data on import ---------------------------------------------------


def set_transforms_data(xforms_data, set_matrix=True, set_parent=True):
	"""
	Set xform data
	:param xforms_data:
	:param set_matrix:
	:param set_parent:
	:return:
	"""
	for xform_data in xforms_data:
		name = xform_data.get("name")
		matrix = xform_data.get("matrix")
		parent = xform_data.get("parent")

		if set_matrix:
			cmds.setAttr(name + ".ro", matrix[-1])
			cmds.xform(name, ws=1, t=matrix[0])
			cmds.xform(name, ws=1, ro=matrix[1])
			cmds.xform(name, a=1, s=matrix[2])

		if set_parent and parent and cmds.objExists(parent):
			try:
				cmds.parent(name, parent)
			except:
				pass


def set_attributes_data(deformer, attrs_data):
	"""
	Get attributes as dict. For some reason the function in attributeTools does not return values properly
	TODO: Fix attribute tools function: at.create_dict_from_node_attrs

	:param deformer:
	:param attrs_data:
	:return:
	"""
	for attr, value in attrs_data.items():

		node_attr = "{}.{}".format(deformer, attr)
		try:
			cmds.setAttr(node_attr, value)

		except:
			if type(value) is list:
				try:
					cmds.setAttr("{}[*]".format(node_attr), *value[0])
				except:
					pass


def transfer_deformer_weights(source_deformer, destination_deformer, transfer_geos, geo_data, method="closest"):
	"""
	Transfer weights from transfer geos to actual geos based on closest point or uv space
	TODO: This has a bug where if you dont have all verts in the deformer, then copying will leave all non-deforened vert weights at a value 1

	:param source_deformer:
	:param destination_deformer:
	:param transfer_geos:
	:param geo_data:
	:param method:
	:return:
	"""
	source_geos = [g[1] if g else None for g in transfer_geos] if transfer_geos else None
	destination_geos = [g.get("name") for g in geo_data]

	for s_geo, d_geo in zip(source_geos, destination_geos):
		if not s_geo or not d_geo:
			continue

		if method in "uv":
			s_uvs = cmds.polyUVSet(s_geo, q=True, cuv=True)
			d_uvs = cmds.polyUVSet(d_geo, q=True, cuv=True)

			if s_uvs and d_uvs:
				if cmds.nodeType(source_deformer) in "skinCluster":
					cmds.copySkinWeights(ss=source_deformer, ds=destination_deformer, sm=1, nm=1, ia="oneToOne",
					                     uv=s_uvs + d_uvs)
					cmds.copySkinWeights(ss=source_deformer, ds=destination_deformer, sm=1, nm=1, nbw=1, ia="oneToOne",
					                     uv=s_uvs + d_uvs)
				else:
					cmds.copyDeformerWeights(sd=source_deformer, dd=destination_deformer, sm=1, ss=s_geo, ds=d_geo,
					                         nm=True, uv=s_uvs + d_uvs)

			else:
				log.warning("Cannot copy weights in uvSpace: uvs not found.. " + d_geo)

		else:
			if cmds.nodeType(source_deformer) in "skinCluster":
				cmds.copySkinWeights(ss=source_deformer, ds=destination_deformer, sm=1, nm=1, ia="oneToOne",
				                     sa="closestPoint", )
				cmds.copySkinWeights(ss=source_deformer, ds=destination_deformer, sm=1, nm=1, nbw=1, ia="oneToOne",
				                     sa="closestPoint", )
			else:
				cmds.copyDeformerWeights(sd=source_deformer, dd=destination_deformer, sm=1, ss=s_geo, ds=d_geo,
				                         sa="closestPoint", nm=True)


def build_transfer_geos(geo_data):
	"""
	Wrapper for recreating trasnfer geos for import

	:param geos:
	:param mesh_data:
	:return:
	"""
	transfer_geos = []
	for g_data in geo_data:
		name = g_data.get("name")
		m_data = g_data.get("mesh_data")

		if m_data:
			transfer_geos.append(topology.create_mesh(name=name + "_TRANSFER_PLY", **m_data))
		else:
			transfer_geos.append(None)

	return transfer_geos


def set_weights(deformer, value=1.0, geo_data=None):
	"""
	Set deformer weights using either geo_data or explicit value

	:param deformer:
	:param value:
	:param geo_data:
	:return:
	"""
	fn_deformer = api.get_fn_deformer(deformer)
	cmpts_array = api.get_cmpts(deformer)

	for idx, item in enumerate(cmpts_array):

		dag_path = item[0]
		cmpts = item[1]

		if geo_data:
			weights = geo_data[idx].get("weights")

			if weights:
				weights_array = api.convert_to_array(weights)
				fn_deformer.setWeight(dag_path, cmpts, weights_array)

		else:
			fn_comp = api.get_fn_cmpt(dag_path, cmpts)
			cmpt_count = fn_comp.elementCount()

			weights_array = api.create_float_array(cmpt_count, value)
			fn_deformer.setWeight(dag_path, cmpts, weights_array)


def set_skin_weights(deformer, geo_data):
	"""
	Get skin weights and blend weights arrays

	:param str deformer:
	:return list: (weights, blend weights)
	"""
	weights = api.convert_to_array(geo_data[0].get("weights")[0], double_array=True)
	blend_weights = api.convert_to_array(geo_data[0].get("weights")[1], double_array=True)

	fn_skin = api.get_fn_deformer(deformer)
	cmpts_array = api.get_cmpts(deformer)

	dag_path = cmpts_array[0]
	cmpts = cmpts_array[1]

	infs = cmds.skinCluster(deformer, q=True, inf=True)
	inf_indecies = api.convert_to_int_array([i for i in range(len(infs))])

	cmds.setAttr("{}.normalizeWeights".format(deformer), False)
	fn_skin.setWeights(dag_path, cmpts, inf_indecies, weights, False)
	fn_skin.setBlendWeights(dag_path, cmpts, blend_weights)


def generate_deform_cmpts_list(geo_data, transfer_geos=None, full_shape=False):
	"""
	For regenerating components list to deform

	:param dict geo_data:
	:param list transfer_geos:
	:param full_shape:
	:return:
	"""
	results = []
	transfer_geo = [g[1] if g else None for g in transfer_geos] if transfer_geos else None

	for idx, g_data in enumerate(geo_data):

		geo = transfer_geo[idx] if transfer_geo else g_data.get("name")
		cmpt = g_data.get("cmpts")

		if cmpt and not full_shape:
			results.extend(["{}.{}".format(geo, c) for c in cmpt])

		elif geo not in results:
			results.append(geo)

	return results


# Functions for getting data to export ---------------------------------------------------


def get_geometry_data(deformer, get_weights=True):
	"""
	Generate a dict of geometry weights, cmpts, and mesh creation data
	:param deformer:
	:param get_weights:
	:return:
	"""
	result = []

	geos, cmpts = get_deformed_cmpts(deformer)
	if get_weights:
		weights = api.get_weights(deformer)
		mesh_data = topology.get_transfer_geo_data(geos)

		for geo, cmpt, weight, m_data in zip(geos, cmpts, weights, mesh_data):
			result.append({"name": geo,
			               "cmpts": cmpt,
			               "weights": weight,
			               "mesh_data": m_data})
	else:
		for geo, cmpt in zip(geos, cmpts):
			result.append({"name": geo,
			               "cmpts": cmpt,
			               "weights": None,
			               "mesh_data": None})

	return result


def get_deformed_cmpts(deformer):
	"""
	Get a set of deformed geometry and its deformend components

	:param deformer:
	:return: set(geometry, list(cmpts))
	"""
	indices, geos = utils.get_deformer_geo_and_indices(deformer)
	results = []

	if cmds.listConnections(deformer, type="objectSet"):
		results = utils.get_mesh_cmpts_from_set(deformer)

	else:
		for idx, geo in zip(indices, geos):
			tag = cmds.getAttr("{}.input[{}].componentTagExpression".format(deformer, idx))
			results.append(utils.get_mesh_cmpts_from_tag(geo, tag))

	return geos, results


def get_transform_data(nodes, required=True):
	"""
	Get transforms data in world space and rotation order

	:param nodes:
	:param required:
	:return:
	"""
	results = []
	for node in utils.as_list(nodes):
		if node and cmds.objExists(node):
			matrix = utils.decompose_node(node)
		else:
			matrix = None

		results.append({"name": node,
		                "required": required,
		                "parent": utils.get_parent(node),
		                "matrix": matrix})
	return results


def get_attributes_data(deformer, attrs):
	"""
	Get attributes as dict. For some reason the function in attributeTools does not return values properly
	TODO: Fix attribute tools function: at.create_dict_from_node_attrs

	:param deformer:
	:param attrs:
	:return:
	"""
	attrs_dict = {}

	for attr in attrs:
		try:
			attrs_dict[attr] = cmds.getAttr("{}.{}".format(deformer, attr))

		except:
			try:
				attrs_dict[attr] = cmds.listConnections("{}.{}".format(deformer, attr), s=True, d=False)
			except:
				pass

	return attrs_dict


# Helper functions --------------------------------------------------------------


def evaluate_method(geo_data, method):
	"""
	Compare meshes vert count in scene with whats in the file

	:param geo_data:
	:param method:
	:return:
	"""
	for g_data in geo_data:
		geo = g_data.get("name")
		m_data = g_data.get("mesh_data")

		# if geo is not a mesh then we must use point method
		if cmds.nodeType(geo) not in ["mesh", "nurbsCurve", "nurbsSurface"]:
			return "vertex"

		# if method is auto then check topology and switch to closest if
		if m_data and method == "auto":
			if topology.compare_topology(geo, shape2_data=m_data):
				return "vertex"

			elif topology.compare_topology(geo, shape2_data=m_data, uv_exists=True):
				return "uvs"

			else:
				return "closest"

	# catch all for defaulting to vert oder
	return "vertex" if method == "auto" else method
