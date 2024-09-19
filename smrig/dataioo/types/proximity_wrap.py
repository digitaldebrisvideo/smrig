import maya.cmds as cmds

from smrig.dataioo import tools

deformer_type = "proximityWrap"
file_type = "pickle"

attr_list = ["wrapMode",
             "maxDrivers",
             "falloffScale",
             "dropoffRateScale",
             "smoothInfluences",
             "smoothNormals",
             "softNormalization",
             "spanSamples",
             "envelope"]

driver_attr_list = ["driverStrength",
                    "driverWrapMode",
                    "driverOverrideSmoothNormals",
                    "driverSmoothNormals",
                    "driverOverrideSpanSamples",
                    "driverSpanSamples",
                    "driverFalloffStart",
                    "driverFalloffEnd",
                    "driverDropoffRate",
                    "driverOverrideFalloffRamp"]


def get_data(deformer, **kwargs):
	"""

	:return:
	"""
	drivers = get_drivers(deformer)
	geo_data = tools.get_geometry_data(deformer)

	# get all xform and attr values
	driver_attrs = []
	for index, driver in zip(get_driver_indices(deformer), drivers):
		driver_attrs.extend(get_driver_attrs(deformer, index))

	attrs_data = tools.get_attributes_data(deformer, attr_list + driver_attrs)

	# Create dataexporter dict
	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "geometry": geo_data,
	        "drivers": drivers,
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
	drivers = data.get("drivers")
	attrs_data = data.get("attributes")

	method = tools.evaluate_method(geo_data, method) if method == "auto" else method
	deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=True)

	# Create deformer
	if not cmds.objExists(deformer):
		deformer = cmds.deformer(deformed_cmpts, type="proximityWrap", name=deformer)[0]

	cmds.proximityWrap(deformer, e=True, addDrivers=drivers)

	# apply weights
	if method in "vertex":
		tools.set_weights(deformer, geo_data=geo_data)

	else:
		transfer_geos = tools.build_transfer_geos(geo_data)
		t_deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, transfer_geos, full_shape=True)

		t_deformer = cmds.deformer(t_deformed_cmpts, type="proximityWrap", name=deformer)[0]
		tools.set_weights(t_deformer, geo_data=geo_data)

		tools.transfer_deformer_weights(t_deformer, deformer, transfer_geos, geo_data, method)
		cmds.delete(t_deformer, [t[0] for t in transfer_geos])

	# set attrs data
	tools.set_attributes_data(deformer, attrs_data)


def get_driver_attrs(wrap_node, index):
	"""

	:param wrap_node:
	:param index:
	:return:
	"""
	driver_attrs = []
	for attr in driver_attr_list:
		attr_plug = "{}.{}".format(get_driver_plug(wrap_node, index).split(".")[1], attr)
		driver_attrs.append(attr_plug)

	return driver_attrs


def get_driver_indices(wrap_node):
	"""
	Get list of infdicies

	:param wrap_node:
	:return:
	"""
	return cmds.proximityWrap(wrap_node, q=True, driverIndices=True) or []


def get_driver_plug(wrap_node, index):
	"""

	:param wrap_node:
	:param index:
	:return:
	"""
	return '{}.drivers[{}]'.format(wrap_node, index)


def get_drivers(wrap_node):
	"""

	:param wrap_node:
	:return:
	"""
	indices = get_driver_indices(wrap_node)
	lookup = []

	for index in indices:
		plug_base = get_driver_plug(wrap_node, index)

		for plugDriver in ['driverGeometry']:
			plug_name = u'{0}.{1}'.format(plug_base, plugDriver)
			cons = cmds.listConnections(plug_name, plugs=False, shapes=True, destination=False)

			if cons and len(cons) > 0:
				lookup.append(cons[0])

		for plugDriver in ['driverClusterMatrix']:
			plug_name = u'{0}.{1}'.format(plug_base, plugDriver)
			cons = cmds.listConnections(plug_name, plugs=False, destination=False)

			if cons and len(cons) > 0:
				lookup.append(cons[0])

	return lookup
