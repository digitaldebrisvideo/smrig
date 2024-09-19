from maya import cmds

from smrig.dataioo import tools, utils

deformer_type = "sculpt"
file_type = "json"


def get_data(deformer, **kwargs):
	"""
	Get deformer creation data.

	:param str deformer: deformer
	:return dict: creation data to export
	"""
	attrs = ["mode",
	         "insideMode",
	         "maximumDisplacement",
	         "dropoffType",
	         "dropoffDistance"]

	attrs_data = tools.get_attributes_data(deformer, attrs)
	geo_data = tools.get_geometry_data(deformer, get_weights=False)

	origin_shape = cmds.listConnections(deformer + ".startPosition")
	sculpt_shape = cmds.listConnections(deformer + ".sculptObjectGeometry")

	origin = utils.get_transform(origin_shape)
	sculpt = utils.get_transform(sculpt_shape)

	xforms_data = tools.get_transform_data(sculpt + origin, required=False)

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "geometry": geo_data,
	        "transforms": xforms_data,
	        "attributes": attrs_data}

	return data


def set_data(data, method="auto", **kwargs):
	"""
	Set / Create deformer from creation data.

	:param dict data:
	:param str method: auto, vertex, uv, closest (auto will default vertex first then closest if vert count is off)
	:param bool rebuild: recreate the deformer (if it exists in scene it deletes it and recreates it)
	:param kwargs:
	:return:
	"""
	deformer = data.get("name")
	geo_data = data.get("geometry")
	xforms_data = data.get("transforms")
	attrs_data = data.get("attributes")

	sculpt = xforms_data[0].get("name")
	origin = xforms_data[1].get("name")

	method = tools.evaluate_method(geo_data, method) if method == "auto" else method

	full_shape = False if method in "vertex" else True
	deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=full_shape)

	# Create deformer
	if not cmds.objExists(deformer):
		result = cmds.sculpt(deformed_cmpts)
		deformer = cmds.rename(result[0], deformer)
		sculpt = cmds.rename(result[1], sculpt)
		origin = cmds.rename(result[2], origin)

	# set attrs data
	tools.set_transforms_data(xforms_data)
	tools.set_attributes_data(deformer, attrs_data)
