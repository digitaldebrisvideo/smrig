import logging

import maya.cmds as cmds
from smrig.lib import constraintslib

deformer_type = "mayaConstraint"
file_type = "json"

log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(constraint, **kwargs):
	"""

	:param constraint:
	:param kwargs:
	:return:
	"""
	if not cmds.objExists("{}.rbMatrixConstraint".format(constraint)):
		return

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
		return

	driver = cmds.listConnections("{}.matrixIn[1]".format(mmtx[0]))
	if not driven or not driver:
		log.warning("{} does not have the proper connections. Skipping...".format(constraint))
		return

	data = {"name": constraint,
	        "drivers": [driver[0]],
	        "driven": [driven],
	        "translate": translate,
	        "rotate": rotate,
	        "scale": scale,
	        "maintain_offset": maintain_offset}

	return data


def set_data(data, **kwargs):
	"""

	:param data:
	:param kwargs:
	:return:
	"""
	data = dict(data)
	data["driver"] = data.get("drivers")[0]
	data["driven"] = data.get("driven")[0]

	constraintslib.matrix_constraint(**data)
	log.info("Loaded {}".format(data.get("name")))
