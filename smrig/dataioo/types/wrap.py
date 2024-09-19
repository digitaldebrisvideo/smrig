from maya import cmds
from maya import mel

from smrig.dataioo import tools

deformer_type = "wrap"
file_type = "json"


def get_data(deformer, **kwargs):
	"""
	Get deformer creation data.

	:param str deformer: deformer
	:return dict: creation data to export
	"""

	attrs = ["envelope",
	         "weightThreshold",
	         "maxDistance",
	         "autoWeightThreshold",
	         "exclusiveBind",
	         "falloffMode"]

	driven = cmds.deformer(deformer, q=1, g=1)
	drivers = cmds.listConnections(deformer + ".driverPoints")
	attrs_data = tools.get_attributes_data(deformer, attrs)

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "drivers": drivers,
	        "driven": driven,
	        "attributes": attrs_data}

	return data


def set_data(data, **kwargs):
	"""
	Set / Create deformer from creation data.

	:param dict data:
	:param bool rebuild: recreate the deformer (if it exists in scene it deletes it and recreates it)
	:param kwargs:
	:return:
	"""
	deformer = data.get("name")
	drivers = data.get("drivers")
	driven = data.get("driven")
	attrs_data = data.get("attributes")

	# Create deformer
	cmds.select(driven, drivers)
	wrap = mel.eval('doWrapArgList "7"{"1","0","1","2","0","1","0","0"};')
	deformer = cmds.rename(wrap[0], deformer)

	# set attrs data
	tools.set_attributes_data(deformer, attrs_data)
