import maya.cmds as cmds
from smrig.dataioo import utils

deformer_type = "poseInterpolator"
file_type = "pose"


def get_data(null=None, file_path=None, *args, **kwargs):
	"""

	:param null:
	:param file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	pose_nodes = [utils.get_transform(p) for p in cmds.ls(type='poseInterpolator')]
	cmds.poseInterpolator(pose_nodes, e=1, ex=file_path)


def set_data(null=None, file_path=None, *args, **kwargs):
	"""

	:param null:
	:param file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	cmds.poseInterpolator(im=file_path)
