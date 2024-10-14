import maya.cmds as cmds
import maya.mel as mel

from smrig.dataioo import utils

deformer_type = "blendShape"
file_type = "mayaBinary"

mel.eval('source "setSculptTargetIndex.mel"')


def get_data(deformer, **kwargs):
	"""

	:param deformer:
	:param kwargs:
	:return:
	"""
	shapes = cmds.blendShape(deformer, q=True, g=True)

	if not shapes:
		raise RuntimeError("{} does not have any geometry".format(deformer))

	mel.eval('setSculptTargetIndex {} 0 0 0;'.format(deformer))
	refresh_targets(deformer)

	export_node = cmds.duplicate(deformer, n="{}_data".format(deformer))[0]
	cmds.refresh()

	data = {"name": deformer,
	        "deformer_type": deformer_type,
	        "driven": shapes}

	utils.tag_export_data_nodes(export_node, data=data)
	return export_node


def set_data(data, **kwargs):
	"""
	Load weights from file.

	:param data:
	:param kwargs:
	:return:
	"""
	name = data.get("name")
	shapes = data.get("driven")
	data_node = utils.get_export_data_nodes()[0]

	# Recreate the blendshape node
	deformer = cmds.blendShape(shapes, automatic=1)[0]

	# add extra geo if nessecary
	if len(shapes) > 1:
		cmds.blendShape(deformer, g=shapes[1:], e=1)

	# reconnect outgoing connections
	utils.swap_node_connections(deformer, data_node, delete_source=True)
	deformer = cmds.rename(data_node, name)
	utils.untag_export_data_nodes(deformer)


def refresh_targets(blendshape):
	"""

	:param blendshape:
	:return:
	"""
	targets = cmds.aliasAttr(blendshape, query=True)
	values = [cmds.getAttr("{}.{}".format(blendshape, t)) for t in targets]

	for trg in targets:
		try:
			if cmds.objExists("{}.{}".format(blendshape, trg)):
				cmds.setAttr("{}.{}".format(blendshape, trg), 1)
		except:
			pass

	cmds.refresh()

	for trg, value in zip(targets, values):
		try:
			if cmds.objExists("{}.{}".format(blendshape, trg)):
				cmds.setAttr("{}.{}".format(blendshape, trg), value)
		except:
			pass
