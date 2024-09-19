import logging
import os

import maya.cmds as cmds
import maya.mel as mel
from smrig.dataio import utils
from smrig.lib import decoratorslib

deformer_type = "blendShape"
file_extension = utils.get_extension(deformer_type).lower()
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))

mel.eval('source "setSculptTargetIndex.mel"')


class Blendshape(object):
	"""Class for exporting, import and manipulating skin nonLinears"""

	def __init__(self, deformer):

		self.deformer = deformer
		self.shapes = cmds.blendShape(self.deformer, q=True, g=True)

	@decoratorslib.preserve_selection
	def save(self, file_path):
		"""

		:param file_path:
		:return:
		"""
		if not self.shapes:
			raise RuntimeError("{} does not have any geometry".format(self.deformer))

		mel.eval('setSculptTargetIndex {} 0 0 0;'.format(self.deformer))

		export_node = cmds.duplicate(self.deformer, n="{}_data".format(self.deformer))[0]
		cmds.refresh()

		cmds.addAttr(export_node, ln="exportData", at="message")
		cmds.addAttr(export_node, ln="deformerName", dt="string")
		cmds.addAttr(export_node, ln="requiredShapes", dt="string")
		cmds.setAttr(export_node + ".deformerName", self.deformer, type="string")
		cmds.setAttr(export_node + ".requiredShapes", str(self.shapes), type="string")

		if os.path.isfile(file_path):
			os.remove(file_path)

		cmds.select(export_node)
		os.rename(cmds.file(file_path, f=1, op="", typ="mayaBinary", es=True), file_path)
		delete_export_data_nodes()

		log.info("Saved {} to: {}".format(self.deformer, file_path))

	@classmethod
	def load(cls, file_path=None, remap=None):
		"""
		Load weights from file.

		:param file_path:
		:param method:
		:param remap:
		:return:
		"""
		delete_export_data_nodes()

		# import the file
		snapshot = cmds.ls()
		try:
			imported_nodes = cmds.file(file_path, i=1, rnn=1, pmt=0, iv=1)

		except:
			imported_nodes = [n for n in cmds.ls() if n not in snapshot]
			pass

		if not imported_nodes:
			raise RuntimeError("This file contains no nodes. Cannot continue. {}".format(file_path))

		data_node = [n for n in imported_nodes if cmds.objExists("{}.exportData".format(n))]
		if not data_node:
			raise RuntimeError("This file contains no dataexporter node. Cannot continue. {}".format(file_path))

		# get dataexporter
		data_node = data_node[0]
		name = cmds.getAttr("{}.deformerName".format(data_node))
		shapes = eval(cmds.getAttr("{}.requiredShapes".format(data_node)))
		shapes = remap_nodes(shapes, remap) if remap else shapes

		if utils.check_missing_nodes(name, shapes):
			return

		# delete the original deformer if it exists
		if cmds.objExists(name):
			cmds.delete(name)

		# Recreate the blendshape node
		cmds.select(shapes[0])
		deformer = cmds.blendShape(shapes[0], automatic=1)

		# add extra geo if nessecary
		deformer = deformer[0]
		if len(shapes) > 1:
			cmds.blendShape(deformer, g=shapes[1:], e=1)

		# reconnect outgoing connections
		connections = cmds.listConnections(deformer, s=0, d=1, p=1)
		for cnn in connections:
			try:
				src = cmds.listConnections(cnn, d=0, s=1, p=1)
				if src:
					cmds.connectAttr(src[0].replace(deformer, data_node), cnn, f=1)

			except:
				pass

		# connect incoming connections
		connections = cmds.listConnections(deformer, s=1, d=0, p=1)
		for cnn in connections:
			try:
				src = cmds.listConnections(cnn, d=1, s=0, p=1)
				cmds.connectAttr(cnn, src[0].replace(deformer, data_node), f=1)

			except:
				pass

		cmds.delete(deformer)
		deformer = cmds.rename(data_node, name)

		cmds.deleteAttr("{}.exportData".format(deformer))
		cmds.deleteAttr("{}.requiredShapes".format(deformer))
		cmds.deleteAttr("{}.deformerName".format(deformer))
		delete_export_data_nodes()

		log.debug("Loaded: {}".format(deformer))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	delete_export_data_nodes()

	# import the file
	imported_nodes = cmds.file(file_path, i=1, rnn=1, pmt=0, iv=1)

	if not imported_nodes:
		log.warning("This file contains no nodes. Cannot continue. {}".format(file_path))

	data_node = [n for n in imported_nodes if cmds.objExists("{}.exportData".format(n))]
	if not data_node:
		log.warning("This file contains no dataexporter node. Cannot continue. {}".format(file_path))

	# get dataexporter
	data_node = data_node[0]
	shapes = eval(cmds.getAttr("{}.requiredShapes".format(data_node)))
	delete_export_data_nodes()

	return shapes


def remap_nodes(shapes, remap):
	"""

	:param shapes:
	:param remap:
	:return:
	"""
	if not remap:
		return shapes

	shapes = list(shapes)
	for search, replace in remap:
		for i, shape in enumerate(shapes):
			if search in shape:
				shapes[i] = shape.replace(search, replace)

	return shapes


def delete_export_data_nodes():
	"""Remove all imported ".exportData" nodes in scene."""

	nodes = cmds.ls('*.exportData')
	if nodes:
		cmds.delete([n.replace('.exportData', '') for n in nodes])


def save(deformer, file_path):
	"""

	:param deformer:
	:param file_path:
	:return:
	"""
	skin_obj = Blendshape(deformer)
	skin_obj.save(file_path)


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param method:
	:param args:
	:param kwargs:
	:return:
	"""
	remap = kwargs.get("remap")
	Blendshape.load(file_path, remap=remap)
