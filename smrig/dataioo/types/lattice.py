from maya import cmds

from smrig.dataioo import tools

deformer_type = "ffd"
file_type = "pickle"


def get_data(deformer, **kwargs):
	"""
	Get deformer creation data.

	:param str deformer: deformer
	:return dict: creation data to export
	"""

	attrs = ["lis",
	         "lit",
	         "liu",
	         "local",
	         "localInfluenceS",
	         "localInfluenceT",
	         "localInfluenceU",
	         "outsideLattice",
	         "outsideFalloffDist",
	         "usePartialResolution",
	         "partialResolution",
	         "freezeGeometry"]

	geo_data = tools.get_geometry_data(deformer)
	attrs_data = tools.get_attributes_data(deformer, attrs)

	handle = cmds.listConnections(deformer + ".deformedLatticePoints")[0]
	base = cmds.listConnections(deformer + ".baseLatticeMatrix")[0]

	xforms_data = tools.get_transform_data([handle, base], required=False)
	handle_attrs_data = tools.get_attributes_data(handle, ["uDivisions", "sDivisions", "tDivisions"])

	handle_points = [cmds.xform(p, q=1, a=1, t=1) for p in cmds.ls(handle + ".pt[*]", fl=1)]

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "geometry": geo_data,
	        "transforms": xforms_data,
	        "attributes": attrs_data,
	        "handle_attributes": handle_attrs_data,
	        "handle_points": handle_points}

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
	handle_attrs_data = data.get("handle_attributes")
	handle_points = data.get("handle_points")

	handle_name = xforms_data[0].get("name")
	base_name = xforms_data[1].get("name")

	method = tools.evaluate_method(geo_data, method) if method == "auto" else method

	full_shape = False if method in "vertex" else True
	deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=full_shape)

	# Create deformer
	if not cmds.objExists(deformer):
		deformer, handle, base = cmds.lattice(deformed_cmpts, oc=True, n=deformer)
		handle = cmds.rename(handle, handle_name)
		base = cmds.rename(base_name, base_name)

	else:
		handle = handle_name
		base = base_name

	# apply weights
	if method in "vertex":
		tools.set_weights(deformer, geo_data=geo_data)

	else:
		transfer_geos = tools.build_transfer_geos(geo_data)
		t_deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, transfer_geos, full_shape=True)

		t_deformer = cmds.lattice(t_deformed_cmpts, n=deformer + "_TRANSFER")[0]
		tools.set_weights(t_deformer, geo_data=geo_data)

		tools.transfer_deformer_weights(t_deformer, deformer, transfer_geos, geo_data, method)
		cmds.delete(t_deformer, [t[0] for t in transfer_geos if t])

	# set attrs data
	tools.set_attributes_data(deformer, attrs_data)
	tools.set_attributes_data(handle, handle_attrs_data)
	tools.set_transforms_data(xforms_data, set_matrix=True, set_parent=True)

	# set lattice points
	for pos, pt in zip(handle_points, cmds.ls(handle + ".pt[*]", fl=1)):
		cmds.xform(pt, a=True, t=pos)
