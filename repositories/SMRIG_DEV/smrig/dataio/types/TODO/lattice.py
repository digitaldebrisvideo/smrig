import os
import time

import maya.cmds as mc
from commsrigging2 import utils
from commsrigging2.gui import remapDialog

file_extention = '.ffd'
deformer_type = 'ffd'


class Lattice(object):
	"""Class for exporting, import and manipulating skin nonLinears"""

	def __init__(self, selection=None):

		deformer, shapes = utils.get_deformers_and_shapes(selection, deformer_type)

		if not deformer:
			raise ValueError('Deformer not found!')

		if not shapes:
			raise ValueError('Shapes not found for: {0}!'.format(deformer))

		self.deformer = deformer
		self.shapes = shapes

		self.handle = mc.listConnections(self.deformer + '.deformedLatticePoints')
		self.handle_base = mc.listConnections(self.deformer + '.baseLatticeMatrix')

		if not self.handle or not self.handle_base:
			raise RuntimeError('Not lattice shape or or base shape found!')

		self.handle = self.handle[0]
		self.handle_base = self.handle_base[0]

		self.def_set = mc.listConnections(self.deformer, type='objectSet')[0]
		self.def_cmpts = mc.ls(mc.sets(self.def_set, q=1), fl=1)

	def get_data(self):

		# Get attrs for handle
		handle_attrs = ['sd', 'td', 'ud']

		handle_attr_dict = {}
		for attr in handle_attrs:
			handle_attr_dict[attr] = round(mc.getAttr(self.handle + '.' + attr), 3)

		# get attrs for defomrer
		deformer_attrs = ['lis',
		                  'lit',
		                  'liu',
		                  'local',
		                  'localInfluenceS',
		                  'localInfluenceT',
		                  'localInfluenceU',
		                  'outsideLattice',
		                  'outsideFalloffDist',
		                  'usePartialResolution',
		                  'partialResolution',
		                  'freezeGeometry']

		deformer_attr_dict = {}
		for attr in deformer_attrs:
			deformer_attr_dict[attr] = round(mc.getAttr(self.deformer + '.' + attr), 3)

		# Get points and postioions
		points_dict = {}
		points = mc.ls(self.handle + '.pt[*]', fl=1)
		for point in points:
			xform = [round(x, 6) for x in mc.xform(point, q=1, ws=1, t=1)]
			points_dict[point.split('.')[-1]] = xform

		# Create dataexporter dict
		self.data = {
			'name': self.deformer,
			'shapes': self.shapes,
			'handle': self.handle,
			'baseHandle': self.handle_base,
			'handleParent': utils.get_parent(self.handle),
			'handleBaseParent': utils.get_parent(self.handle_base),
			'handleXformValues': utils.decompose_matrix(self.handle),
			'handleBaseXformValues': utils.decompose_matrix(self.handle_base),
			'handleAttrs': handle_attr_dict,
			'deformerAttrs': deformer_attr_dict,
			'points': points_dict,
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
	@utils.undoable
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
		handle_name = data.get('handle')
		handle_base_name = data.get('baseHandle')
		handle_parent = data.get('handleParent')
		handle_base_parent = data.get('handleBaseParent')
		handle_xforms = data.get('handleXformValues')
		handle_base_xforms = data.get('handleBaseXformValues')
		handle_attrs = data.get('handleAttrs')
		deformer_attrs = data.get('deformerAttrs')
		points_dict = data.get('points')
		orig_def_cmpts = data.get('setMembers')

		# check if this import has all the nodes it needs in scene
		test_shapes = len(shapes) == len(mc.ls(shapes))
		test_hnd_parent = True
		test_base_parent = True

		if handle_parent and not mc.objExists(handle_parent):
			test_hnd_parent = False

		if handle_base_parent and not mc.objExists(handle_base_parent):
			test_base_parent = False

		# set remap flag if needed
		if remap or not test_shapes or not test_hnd_parent or not test_base_parent:
			return data

		# delete existing deformer
		if mc.objExists(name):
			mc.delete(name)

		# Create lattice
		deformer, handle, base_handle = mc.lattice(shapes)

		# set_values
		for attr, value in handle_attrs.items():
			mc.setAttr(handle + '.' + attr, value)

		for attr, value in deformer_attrs.items():
			mc.setAttr(deformer + '.' + attr, value)

		# set xforms onb handle
		mc.setAttr(handle + '.rotateOrder', handle_xforms[3])
		mc.xform(handle, ws=1, t=handle_xforms[0])
		mc.xform(handle, ws=1, ro=handle_xforms[1])
		mc.xform(handle, a=1, s=handle_xforms[2])

		# set xforms on base
		mc.setAttr(base_handle + '.rotateOrder', handle_base_xforms[3])
		mc.xform(base_handle, ws=1, t=handle_base_xforms[0])
		mc.xform(base_handle, ws=1, ro=handle_base_xforms[1])
		mc.xform(base_handle, a=1, s=handle_base_xforms[2])

		# parent handle
		if handle_parent:
			parent = mc.ls(handle_parent)
			if parent:
				mc.parent(handle, parent[0])

		# parent handle
		if handle_base_parent:
			parent = mc.ls(handle_base_parent)
			if parent:
				mc.parent(base_handle, parent[0])

		# setr_points
		for point, pos in points_dict.items():
			mc.xform(handle + '.' + point, ws=2, t=pos)

		# remove cmpts from set
		new_obj = Lattice(deformer)
		rm_cmpts = []
		for cmpt in new_obj.def_cmpts:
			if cmpt not in orig_def_cmpts:
				rm_cmpts.append(cmpt)

		if rm_cmpts:
			mc.sets(rm_cmpts, rm=new_obj.def_set)

		# rename stuff
		deformer = mc.rename(deformer, name)
		handle = mc.rename(handle, handle_name)
		base_handle = mc.rename(base_handle, handle_base_name)

		print(time.time() - t)


class RemapLattice(remapDialog.RemapDialog):
	"""Remap UI for remapping shape and influences during import"""

	def __init__(self, nodes=[], ignore_missing=False, label=''):
		remapDialog.RemapDialog.__init__(self, nodes, False, 'Non-Linear Remap UI')

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
		handle_parent = self.data.get('handleParent') or ''
		if handle_parent in self.mapping.keys():
			self.data['handleParent'] = self.mapping[handle_parent]

		handle_base_parent = self.data.get('handleBaseParent') or ''
		if handle_base_parent in self.mapping.keys():
			self.data['handleBaseParent'] = self.mapping[handle_base_parent]

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
		result = Lattice.load(data=self.data)


def save(file_path, selection):
	"""Wrapper for class export call, Can export multiple and
		prompts for file path"""

	if not file_path.endswith(file_extention):
		file_path = os.path.splitext(file_path)[0] + file_extention

	# export single deformer
	obj = Lattice(selection=selection)
	obj.save(file_path)


def load(file_path, remap=False, **kwargs):
	"""Wrapper for importing weights"""

	if remap:
		data = Lattice.load(file_path, remap=True)

		if type(data) == dict:

			# get nodes to remap
			nodes = []
			if data.get('handleParent'):
				nodes.append(data.get('handleParent'))

			if data.get('baseHandleParent'):
				nodes.append(data.get('baseHandleParent'))

			nodes.extend(data.get('shapes'))

			remap_dialog = RemapLattice(nodes=nodes)
			remap_dialog.data = data
			remap_dialog.show()
			return

	# If not remap then load as usual
	else:
		result = Lattice.load(file_path)

		# warn and skip if a remap is needed.
		if type(result) == dict:
			mc.warning('{0} needs remapping! File path: {1}'.format(result['name'], file_path))
