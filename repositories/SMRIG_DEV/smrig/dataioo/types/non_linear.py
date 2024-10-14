from maya import cmds

from smrig.dataioo import tools, utils

deformer_type = "nonLinear"
file_type = "pickle"


def get_data(deformer, **kwargs):
	"""
	Get deformer creation data.

	:param str deformer: deformer
	:return dict: creation data to export
	"""
	attrs = ["en", "mnr", "ea", "fac", "es", "efx",
	         "efz", "lb", "cur", "wav", "sfz", "sfx",
	         "mxr", "hb", "off", "dr", "dp", "crv",
	         "amp", "ss", "mp", "exp", "sa"]

	geo_data = tools.get_geometry_data(deformer)
	attrs_data = tools.get_attributes_data(deformer, attrs)

	handle = cmds.listConnections(deformer + ".deformerData", s=1, d=0)[0]
	n_type = cmds.nodeType(utils.get_shapes(handle)).replace("deform", "").lower()

	xforms_data = tools.get_transform_data(handle, required=False)

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "nonlinear_type": n_type,
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
	n_type = data.get("nonlinear_type")
	xforms_data = data.get("transforms")
	attrs_data = data.get("attributes")

	handle = xforms_data[0].get("name")

	method = tools.evaluate_method(geo_data, method) if method == "auto" else method

	full_shape = False if method in "vertex" else True
	deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=full_shape)

	# Create deformer
	if not cmds.objExists(deformer):
		result = cmds.nonLinear(deformed_cmpts, type=n_type)
		deformer = cmds.rename(result[0], deformer)
		handle = cmds.rename(result[1], handle)

	# apply weights
	if method in "vertex":
		tools.set_weights(deformer, geo_data=geo_data)

	else:
		transfer_geos = tools.build_transfer_geos(geo_data)
		t_deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, transfer_geos, full_shape=True)

		t_deformer = cmds.nonLinear(t_deformed_cmpts, type=n_type, n=deformer + "_TRANSFER")[0]
		tools.set_weights(t_deformer, geo_data=geo_data)

		tools.transfer_deformer_weights(t_deformer, deformer, transfer_geos, geo_data, method)
		cmds.delete(t_deformer, [t[0] for t in transfer_geos])

	# set attrs data
	tools.set_transforms_data(xforms_data)
	tools.set_attributes_data(deformer, attrs_data)
