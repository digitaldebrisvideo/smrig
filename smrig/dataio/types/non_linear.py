import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import api2lib
from smrig.lib import geometrylib
from smrig.lib import iolib
from smrig.lib import selectionlib

deformer_type = "nonLinear"
file_extension = utils.get_extension(deformer_type).lower() or "nonl"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


class NonLinear(object):
	def __init__(self, deformer):
		self.deformer = deformer
		self.shapes = cmds.nonLinear(deformer, q=True, g=True)

		self.def_set = cmds.listConnections(self.deformer, type="objectSet")[0]
		self.def_cmpts = cmds.ls(cmds.sets(self.def_set, q=1), fl=1)
		self.data = {}

	def get_data(self):
		"""

		:return:
		"""
		handle = cmds.listConnections(self.deformer + ".deformerData", s=1, d=0)[0]
		handle_shape = selectionlib.get_shapes(handle)
		nonl_type = cmds.nodeType(handle_shape).replace("deform", "").lower()

		# get all xform and attr values
		deformer_attrs = ["en", "mnr", "ea", "fac", "es", "efx",
		                  "efz", "lb", "cur", "wav", "sfz", "sfx",
		                  "mxr", "hb", "off", "dr", "dp", "crv",
		                  "amp", "ss", "mp", "exp", "sa"]
		attr_dict = {}
		for attr in deformer_attrs:
			if cmds.objExists(self.deformer + "." + attr):
				attr_dict[attr] = round(cmds.getAttr(self.deformer + "." + attr), 3)

		# get weights
		weights = []
		for i in range(len(self.shapes)):
			try:
				index_weight = list(cmds.getAttr("{0}.weightList[{1}].weights".format(self.deformer, i))[0])

			except:
				index_weight = []

			weights.append(index_weight)

		# get mesh dataexporter
		mesh_data = {}

		for shape in self.shapes:
			mesh_data[shape] = geometrylib.mesh.extract_mesh_creation_data(selectionlib.get_original_shape(shape))

		# Create dataexporter dict
		self.data = {
			"type": nonl_type,
			"name": self.deformer,
			"shapes": self.shapes,
			"setMembers": self.def_cmpts,
			"handle": handle,
			"parent": selectionlib.get_parent(handle),
			"xformValues": api2lib.matrix.decompose_node(handle),
			"attrValues": attr_dict,
			"weights": weights,
			"meshData": mesh_data
		}

	def save(self, file_path):
		"""

		:param file_path:
		:return:
		"""
		self.get_data()
		iolib.pickle.write(file_path, self.data)
		log.info("Saved {} to: {}".format(self.deformer, file_path))

	@classmethod
	def load(cls, file_path, method="vertexID", remap=None):
		"""

		:param file_path:
		:param method:
		:param remap:
		:return:
		"""

		def set_weights(deformer, data):
			"""
			:param deformer:
			:param data:
			:return:
			"""
			if data.get("weights"):
				for i in range(len(data.get("weights"))):
					index_weight = data.get("weights")[i]
					if index_weight:
						attr = ".weightList[{0}].weights[0:{1}]".format(i, len(index_weight) - 1)
						cmds.setAttr(deformer + attr, *index_weight)

		def set_data(deformer, handle, data):
			"""

			:param deformer:
			:param handle:
			:param data:
			:return:
			"""
			parent = data.get("parent") or ""
			xform_vals = data.get("xformValues")
			attr_vals = data.get("attrValues")

			# set xfroms
			cmds.setAttr(handle + ".rotateOrder", xform_vals[-1])
			cmds.xform(handle, ws=1, t=xform_vals[0])
			cmds.xform(handle, ws=1, ro=xform_vals[1])
			cmds.xform(handle, a=1, s=xform_vals[2])

			# parent
			if cmds.objExists(parent):
				cmds.parent(handle, parent)

			# set handle attr values
			for attr, val in attr_vals.items():
				cmds.setAttr(deformer + "." + attr, val)

		data = remap_nodes(iolib.pickle.read(file_path), remap)

		name = data.get("name")
		handle_name = data.get("handle")
		nonl_type = data.get("type")
		shapes = data.get("shapes") or []
		parent = data.get("parent")
		set_members = data.get("setMembers") or []
		weights = data.get("weights")

		check_nodes = shapes
		if parent:
			check_nodes.append(parent)

		if utils.check_missing_nodes(name, check_nodes):
			return

		# delete existing deformer
		if cmds.objExists(name):
			cmds.delete(name)

		tmp_shapes = {}
		tmp_set_members = list(set_members)
		mesh_data = data.get("meshData")

		if len(weights) and method == "closestPoint":

			# recreate the original mesh for all shapes
			for shape, mesh_info in mesh_data.items():
				tmp_shapes[shape] = geometrylib.mesh.create_mesh("origDataMesh", **mesh_data)

			# generate a new set members list for creating the tmp deformer
			for i, member in enumerate(tmp_set_members):
				for shape in shapes:
					transform = selectionlib.get_transform(shape)

					if tmp_shapes[shape]:
						if shape in member:
							tmp_set_members[i] = member.replace(shape, tmp_shapes[shape])

						elif transform in member:
							tmp_set_members[i] = member.replace(transform, tmp_shapes[shape])

			# Creat REAL deformer on recreated mesh
			result = cmds.nonLinear(shapes, type=nonl_type)
			deformer = cmds.rename(result[0], name)
			handle = cmds.rename(result[1], handle_name)

			# Create the temp deformer and apply weights
			tmp_deformer, tmp_handle = cmds.nonLinear(tmp_set_members, type=nonl_type)
			set_weights(tmp_deformer, data)

			# copy defomer weights from tem pto real
			for shape, tmp_shape in tmp_shapes.items():
				cmds.copyDeformerWeights(sourceDeformer=tmp_deformer,
				                         destinationDeformer=deformer,
				                         sourceShape=tmp_shape,
				                         destinationShape=shape,
				                         surfaceAssociation="closestPoint",
				                         noMirror=1)

			# Delete all the temp junk
			cmds.delete(tmp_deformer, tmp_handle)
			cmds.delete(tmp_shapes.values())

			# set dataexporter on the real deformer
			set_data(deformer, handle, data)

		else:

			if method == "closestPoint":
				set_members = shapes

			result = cmds.nonLinear(set_members, type=nonl_type)
			deformer = cmds.rename(result[0], name)
			handle = cmds.rename(result[1], handle_name)

			# set dataexporter and weights on the real deformer
			set_weights(deformer, data)
			set_data(deformer, handle, data)

		log.debug("Loaded: {}".format(deformer))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.pickle.read(file_path)
	shapes = data.get("shapes") or []
	parent = data.get("parent")

	check_nodes = shapes
	if parent:
		check_nodes.append(parent)

	return check_nodes


def remap_nodes(data, remap):
	"""

	:param shapes:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	data = dict(data)
	shapes = list(data.get("shapes"))
	set_members = list(data.get("setMembers"))
	parent = data.get("parent")

	for search, replace in remap:
		for i, shape in enumerate(shapes):
			if search in shape:
				shapes[i] = shape.replace(search, replace)

		for i, set_member in enumerate(set_members):
			if search in set_member:
				set_members[i] = set_member.replace(search, replace)

		if parent and search in parent:
			data["parent"] = parent.replace(search, replace)

		data["shapes"] = shapes
		data["setMembers"] = set_members

	return data


def save(deformer, file_path):
	"""

	:param deformer:
	:param file_path:
	:return:
	"""
	obj = NonLinear(deformer)
	obj.save(file_path)


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param method:
	:param args:
	:param kwargs:
	:return:
	"""
	method = kwargs.get("method", "vertexID")
	remap = kwargs.get("remap")
	NonLinear.load(file_path, method=method, remap=remap)
