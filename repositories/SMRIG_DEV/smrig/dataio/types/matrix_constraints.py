import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import constraintslib
from smrig.lib import iolib
from smrig.lib import utilslib

deformer_type = "matrixConstraint"
file_extension = "mcon"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(constraints):
	"""

	:param constraints:
	:return:
	"""
	constraints = utilslib.conversion.as_list(constraints)
	constraints = [n for n in constraints if cmds.objExists("{}.rigBotMatrixConstraint".format(n))]

	data = {}
	for constraint in constraints:

		connections = [cmds.listConnections("{}.outputTranslate".format(constraint)),
		               cmds.listConnections("{}.outputRotate".format(constraint)),
		               cmds.listConnections("{}.outputScale".format(constraint))]

		translate = True if connections[0] else False
		rotate = True if connections[1] else False
		scale = True if connections[2] else False
		maintain_offset = cmds.getAttr("{}.maintainOffset".format(constraint))

		driven = [l for l in connections if l]
		driven = driven[0][0] if driven else None

		mmtx = cmds.listConnections("{}.inputMatrix".format(constraint))
		if not mmtx:
			log.warning("{} does not have the proper connections. Skipping...".format(constraint))
			continue

		driver = cmds.listConnections("{}.matrixIn[1]".format(mmtx[0]))
		if not driven or not driver:
			log.warning("{} does not have the proper connections. Skipping...".format(constraint))
			continue

		data[constraint] = {
			"driver": driver[0],
			"driven": driven,
			"translate": translate,
			"rotate": rotate,
			"scale": scale,
			"maintain_offset": maintain_offset
		}

	return data


def set_data(data):
	"""

	:param data:
	:return:
	"""

	for name, con_data in data.items():

		if utils.check_missing_nodes(name, [con_data.get("driver"), con_data.get("driven")]):
			continue

		constraintslib.matrix_constraint(**con_data)
		log.info("Loaded {}".format(name))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	nodes = []

	for name, cdata in data.items():
		nodes.extend([cdata.get("driver"), cdata.get("driven")])

	return nodes


def remap_nodes(data, remap):
	"""

	:param data:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	data = dict(data)
	driver = data.get("driver")
	driven = data.get("driven")

	for search, replace in remap:

		# remap shape
		if search in driver:
			data["shape"] = driver.replace(search, replace)

		if search in driven:
			data["weightedNode"] = driven.replace(search, replace)

	return data


def save(constraints, file_path):
	"""

	:param constraints:
	:param file_path:
	:return:
	"""
	iolib.json.write(file_path, get_data(constraints))
	log.info("Saved {} to: {}".format(constraints, file_path))


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param method:
	:param args:
	:param kwargs:
	:return:
	"""
	remap = kwargs.get("remap")
	data = iolib.json.read(file_path)
	set_data(remap_nodes(data, remap) if remap else data)
