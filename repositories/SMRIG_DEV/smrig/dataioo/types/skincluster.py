from maya import cmds

from smrig.dataioo import tools

deformer_type = "skinCluster"
file_type = "pickle"


def get_data(deformer, **kwargs):
	"""
	Get deformer creation data.

	:param str deformer: deformer
	:return dict: creation data to export
	"""

	attrs = ["envelope",
	         "skinningMethod",
	         "useComponents",
	         "deformUserNormals",
	         "dqsSupportNonRigid",
	         "dqsScaleX",
	         "dqsScaleY",
	         "dqsScaleZ",
	         "normalizeWeights",
	         "weightDistribution",
	         "maintainMaxInfluences",
	         "maxInfluences"]

	geo_data = tools.get_geometry_data(deformer)
	joints = cmds.skinCluster(deformer, q=True, inf=True)
	attrs_data = tools.get_attributes_data(deformer, attrs)

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "geometry": geo_data,
	        "joints": joints,
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
	joints = data.get("joints")
	attrs_data = data.get("attributes")

	method = tools.evaluate_method(geo_data, method) if method == "auto" else method
	deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=True)

	# Create deformer
	if not cmds.objExists(deformer):
		deformer = cmds.skinCluster(deformed_cmpts, joints, n=deformer, tsb=True)[0]

	# apply weights
	if method in "vertex":
		tools.set_skin_weights(deformer, geo_data=geo_data)

	else:
		transfer_geos = tools.build_transfer_geos(geo_data)
		t_deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, transfer_geos, full_shape=True)

		t_deformer = cmds.skinCluster(t_deformed_cmpts, joints, n=deformer + "_TRANSFER", tsb=True)[0]
		tools.set_skin_weights(t_deformer, geo_data=geo_data)

		tools.transfer_deformer_weights(t_deformer, deformer, transfer_geos, geo_data, method)
		cmds.delete(t_deformer, [t[0] for t in transfer_geos])

	# set attrs data
	tools.set_attributes_data(deformer, attrs_data)
