import os
import time

import maya.cmds as mc
from commsrigging2 import utils
from commsrigging2.gui import remapDialog

file_extention = '.sculpt'
deformer_type = 'sculpt'


class Sculpt(object):
	"""Class for exporting, import and manipulating skin nonLinears"""

	def __init__(self, selection=None):

		deformer, shapes = utils.get_deformers_and_shapes(selection, deformer_type)

		if not deformer:
			raise ValueError('Deformer not found!')

		if not shapes:
			raise ValueError('Shapes not found for: {0}!'.format(deformer))

		self.deformer = deformer
		self.shapes = shapes

		self.sculptor = mc.listConnections(self.deformer + '.sculptObjectMatrix')
		self.origin = mc.listConnections(self.deformer + '.startPosition')

		if not self.sculptor or not self.origin:
			raise RuntimeError('Not sculpt deformer shape or or base shape found!')

		self.sculptor = self.sculptor[0]
		self.origin = self.origin[0]

		self.def_set = mc.listConnections(self.deformer, type='objectSet')[0]
		self.def_cmpts = mc.ls(mc.sets(self.def_set, q=1), fl=1)

	def get_data(self):

		# get attrs for defomrer
		deformer_attrs = ['mode',
		                  'insideMode',
		                  'maximumDisplacement',
		                  'dropoffType',
		                  'dropoffDistance']

		deformer_attr_dict = {}
		for attr in deformer_attrs:
			deformer_attr_dict[attr] = round(mc.getAttr(self.deformer + '.' + attr), 3)

		# Create dataexporter dict
		self.data = {
			'name': self.deformer,
			'shapes': self.shapes,
			'sculptor': self.sculptor,
			'origin': self.origin,
			'sculptorParent': utils.get_parent(self.sculptor),
			'originParent': utils.get_parent(self.origin),
			'sculptorXformValues': utils.decompose_matrix(self.sculptor),
			'originXformValues': utils.decompose_matrix(self.origin),
			'deformerAttrs': deformer_attr_dict,
			'setMembers': self.def_cmpts
		}

	def save(self, file_path):
		"""Export skin weights to disk"""

		if not file_path:
			return

		t = time.time()
		self.get_data()
		utils.write_pickle(file_path, self.data)

		print(time.time() - t)

	@classmethod
	def load(self, file_path=None, remap=False, data={}):
		"""import weights from disk"""

		# Start timer for load process
		t = time.time()

		if not data and not file_path:
			mc.warning('Must either specify a file path OR provide dataexporter.')
			return

		elif file_path and not data:
			data = utils.read_pickle(file_path)

		# get dataexporter
		name = data.get('name')
		shapes = data.get('shapes')
		sculptor_name = data.get('sculptor')
		origin_name = data.get('origin')
		sculptor_parent = data.get('sculptorParent')
		origin_parent = data.get('originParent')
		sculptor_xforms = data.get('sculptorXformValues')
		origin_xforms = data.get('originXformValues')
		deformer_attrs = data.get('deformerAttrs')
		orig_def_cmpts = data.get('setMembers')

		# check if this import has all the nodes it needs in scene
		test_shapes = len(shapes) == len(mc.ls(shapes))
		test_hnd_parent = True
		test_base_parent = True

		if sculptor_parent:
			if type(sculptor_parent) == list:
				tp = sculptor_parent
			else:
				tp = [sculptor_parent]

			test_hnd_parent = len(tp) == len(mc.ls(sculptor_parent))

		if origin_parent:
			if type(origin_parent) == list:
				tp = origin_parent
			else:
				tp = [origin_parent]

			test_base_parent = len(tp) == len(mc.ls(origin_parent))

		# set remap flag if needed
		if remap or not test_shapes or not test_hnd_parent or not test_base_parent:
			return data

		# delete existing deformer
		if mc.objExists(name):
			mc.delete(name)

		# Create sculpt
		deformer, sculptor, origin = mc.sculpt(shapes)

		# set_values
		for attr, value in deformer_attrs.items():
			mc.setAttr(deformer + '.' + attr, value)

		# set xforms onb sculptor
		mc.setAttr(sculptor + '.rotateOrder', sculptor_xforms[3])
		mc.xform(sculptor, ws=1, t=sculptor_xforms[0])
		mc.xform(sculptor, ws=1, ro=sculptor_xforms[1])
		mc.xform(sculptor, a=1, s=sculptor_xforms[2])

		# set xforms on base
		mc.setAttr(origin + '.rotateOrder', origin_xforms[3])
		mc.xform(origin, ws=1, t=origin_xforms[0])
		mc.xform(origin, ws=1, ro=origin_xforms[1])
		mc.xform(origin, a=1, s=origin_xforms[2])

		# parent sculptor
		if sculptor_parent:
			parent = mc.ls(sculptor_parent)
			if parent:
				mc.parent(sculptor, parent[0])

		# parent sculptor
		if origin_parent:
			parent = mc.ls(origin_parent)
			if parent:
				mc.parent(origin, parent[0])

		# remove cmpts from set
		new_obj = Sculpt(deformer)
		rm_cmpts = []
		for cmpt in new_obj.def_cmpts:
			if cmpt not in orig_def_cmpts:
				rm_cmpts.append(cmpt)

		if rm_cmpts:
			mc.sets(rm_cmpts, rm=new_obj.def_set)

		# rename stuff
		deformer = mc.rename(deformer, name)
		sculptor = mc.rename(sculptor, sculptor_name)
		origin = mc.rename(origin, origin_name)

		print(time.time() - t)


class RemapSculpt(remapDialog.RemapDialog):
	"""Remap UI for remapping shape and influences during import"""

	def __init__(self, nodes=[], ignore_missing=True, label=''):
		remapDialog.RemapDialog.__init__(self, nodes, True, 'Sculpt Deformer Remap UI')

		self.data = {}

	def map_selection(self):
		"""Map selectio nto node"""

		items = self.ui.node_tree.selectedItems() or []
		sel = mc.ls(sl=1)

		if items and sel:
			for item in items:
				if 'Shape' in item.text(0):
					shape = utils.get_shapes(sel[0])
					if not shape:
						mc.warning('This node needs a shape to remap!')
						return

					sel = shape

				node = item.text(0)
				item.setText(2, sel[0])
				self.mapping[node] = sel[0]

		elif not sel:
			mc.warning('Nothing selected!')

	def finish_command(self):
		"""update dataexporter dict with new mapping and load the dataexporter"""

		# remap parent
		sculptor_parent = self.data.get('sculptorParent') or ''
		if sculptor_parent in self.mapping.keys():
			self.data['sculptorParent'] = self.mapping[sculptor_parent]

		origin_parent = self.data.get('originParent') or ''
		if origin_parent in self.mapping.keys():
			self.data['originParent'] = self.mapping[origin_parent]

		# remap shapes and set members
		shapes_list = list(self.data.get('shapes') or [])
		set_members = list(self.data.get('setMembers') or [])

		for i, orig_shape in enumerate(shapes_list):
			if orig_shape in self.mapping.keys():

				# get new shape and get original transform name to test
				new_shape = self.mapping.get(orig_shape)
				test_orig_xform = orig_shape.replace('Shape', '')

				# first update set members then
				for ii, member in enumerate(set_members):
					if orig_shape in member:
						set_members[ii] = member.replace(orig_shape, new_shape)

					elif test_orig_xform in member:
						set_members[ii] = member.replace(test_orig_xform, utils.get_transform(new_shape))

				# finally update the shapes entry
				shapes_list[i] = new_shape

		self.data['shapes'] = shapes_list
		self.data['setMembers'] = set_members
		result = Sculpt.load(data=self.data)


def save(file_path, selection):
	"""Wrapper for class export call, Can export multiple and
		prompts for file path"""

	if not file_path.endswith(file_extention):
		file_path = os.path.splitext(file_path)[0] + file_extention

	# export single deformer
	obj = Sculpt(selection=selection)
	obj.save(file_path)


def load(file_path, remap=False, **kwargs):
	"""Wrapper for importing weights"""

	if remap:
		data = Sculpt.load(file_path, remap=True)

		if type(data) == dict:

			# get nodes to remap
			nodes = []
			if data.get('sculptorParent'):
				nodes.append(data.get('sculptorParent'))

			if data.get('originParent'):
				if data.get('sculptor') != data.get('originParent'):
					nodes.append(data.get('originParent'))

			nodes.extend(data.get('shapes'))

			remap_dialog = RemapSculpt(nodes=nodes)
			remap_dialog.data = data
			remap_dialog.show()
			return

	# If not remap then load as usual
	else:
		result = Sculpt.load(file_path)

		# warn and skip if a remap is needed.
		if type(result) == dict:
			mc.warning('{0} needs remapping! File path: {1}'.format(result['name'], file_path))
