import logging

import maya.cmds as cmds
from smrig.dataioo import tools
from smrig.dataioo import utils

deformer_type = "wire"
file_type = "pickle"

log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(deformer, **kwargs):
	"""

	:param deformer:
	:param kwargs:
	:return:
	"""
	attrs = ["envelope",
	         "scale[0]",
	         "dropoffDistance[0]",
	         "rotation",
	         "localInfluence",
	         "tension",
	         "crossingEffect"]

	geo_data = tools.get_geometry_data(deformer)
	attrs_data = tools.get_attributes_data(deformer, attrs)

	base = cmds.listConnections(deformer + ".baseWire[0]") or []
	shapes = cmds.wire(deformer, q=True, w=True) or []

	xform_data = tools.get_transform_data([utils.get_transform(s) for s in shapes])
	xform_data += tools.get_transform_data(base, required=False)

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "geometry": geo_data,
	        "transforms": xform_data,
	        "attributes": attrs_data}

	return data


def set_data(data, method="auto", **kwargs):
	"""

	:param data:
	:param method:
	:param kwargs:
	:return:
	"""
	deformer = data.get("name")
	geo_data = data.get("geometry")
	node_data = data.get("transforms")
	attrs_data = data.get("attributes")
	curve = node_data[0].get("name")

	method = tools.evaluate_method(geo_data, method) if method == "auto" else method

	full_shape = False if method in "vertex" else True
	deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=full_shape)

	# Create deformer
	if not cmds.objExists(deformer):
		deformer, curve = cmds.wire(deformed_cmpts, w=curve, gw=False, ce=0.0, li=0.0, en=1.0, n=deformer)

	# apply weights
	if method in "vertex":
		tools.set_weights(deformer, geo_data=geo_data)

	else:
		transfer_geos = tools.build_transfer_geos(geo_data)
		t_deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, transfer_geos)

		t_deformer, t_curve = cmds.wire(t_deformed_cmpts, w=curve, gw=False, ce=0.0, li=0.0, en=1.0,
		                                n=deformer + "_TRANSFER")
		tools.set_weights(t_deformer, value=1, geo_data=geo_data)

		tools.transfer_deformer_weights(t_deformer, deformer, transfer_geos, geo_data, method)
		cmds.delete(t_deformer, [t[0] for t in transfer_geos])

	# set attrs data
	tools.set_attributes_data(deformer, attrs_data)

	# parent base
	base = [utils.get_transform(n) for n in cmds.listConnections(deformer + ".baseWire[0]") or []]
	base_parent = node_data[1].get("parent")

	if base_parent and cmds.objExists(base_parent):
		cmds.parent(base, base_parent)
