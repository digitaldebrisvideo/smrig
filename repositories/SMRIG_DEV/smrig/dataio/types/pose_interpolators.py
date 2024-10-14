import logging

import maya.cmds as cmds
from smrig.lib import selectionlib

deformer_type = "poseInterpolators"
file_extension = "pose"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def save(null, file_path, *args, **kwargs):
	"""

	:param file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	pose_nodes = [selectionlib.get_transform(p) for p in cmds.ls(type='poseInterpolator')]
	cmds.poseInterpolator(pose_nodes, e=1, ex=file_path)
	log.info("Saved {} to: {}".format(pose_nodes, file_path))


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	cmds.poseInterpolator(im=file_path)
	log.info("Loaded poseInterpolators")
