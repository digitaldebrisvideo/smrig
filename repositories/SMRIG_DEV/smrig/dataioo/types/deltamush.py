from maya import cmds

from smrig.dataioo import tools

deformer_type = "deltaMush"
file_type = "pickle"


def get_data(deformer, **kwargs):
	"""
	Get deformer creation data.

	:param deformer:
	:param kwargs:
	:return dict: creation data to export
	"""
	attrs = ["smoothingIterations",
	         "smoothingStep",
	         "pinBorderVertices",
	         "displacement",
	         "scaleX",
	         "scaleY",
	         "scaleZ"]

	geo_data = tools.get_geometry_data(deformer)
	attrs_data = tools.get_attributes_data(deformer, attrs)

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "geometry": geo_data,
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
	attrs_data = data.get("attributes")

	method = tools.evaluate_method(geo_data, method) if method == "auto" else method
	full_shape = False if method in "vertex" else True

	# Create deformer
	if not cmds.objExists(deformer):
		deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=full_shape)
		deformer = cmds.deformer(deformed_cmpts, type=deformer_type, name=deformer)[0]

	# apply weights
	if method in "vertex":
		tools.set_weights(deformer, geo_data=geo_data)

	else:
		transfer_geos = tools.build_transfer_geos(geo_data)
		t_deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, transfer_geos)

		t_deformer = cmds.deformer(t_deformed_cmpts, type=deformer_type, name=deformer + "_TRANSFER")[0]
		tools.set_weights(t_deformer, value=1, geo_data=geo_data)

		tools.transfer_deformer_weights(t_deformer, deformer, transfer_geos, geo_data, method)
		cmds.delete(t_deformer, [t[0] for t in transfer_geos])

	# set attrs data
	tools.set_attributes_data(deformer, attrs_data)
