import logging

import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import deformlib
from smrig.lib import geometrylib
from smrig.lib import iolib
from smrig.lib import selectionlib

deformer_type = "cluster"
file_extension = utils.get_extension(deformer_type).lower()
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


class Cluster(object):
	data = {}
	shapes = []
	relative = False
	weighted_node = None
	prebind_node = None
	deformer_set = None
	deformer_cmpts = None
	cls_obj = None
	cls_dag_path = None
	cls_members = None
	fn_cls = None
	fn_set = None

	def __init__(self, deformer):

		self.deformer = deformer
		self.reinitialize_deformer()

	def reinitialize_deformer(self):
		"""

		:return:
		"""
		self.shapes = cmds.cluster(self.deformer, q=True, g=True)
		self.deformer_set = cmds.listConnections(self.deformer, type="objectSet")[0]
		self.deformer_cmpts = cmds.ls(cmds.sets(self.deformer_set, q=1), fl=1)

		# Get skin cluster api info
		self.cls_obj = om.MObject()
		self.cls_dag_path = om.MDagPath()
		self.cls_members = om.MSelectionList()

		sel_list = om.MSelectionList()
		sel_list.add(self.deformer)
		sel_list.getDependNode(0, self.cls_obj)

		self.fn_cls = oma.MFnWeightGeometryFilter(self.cls_obj)
		self.fn_set = om.MFnSet(self.fn_cls.deformerSet())
		self.fn_set.getMembers(self.cls_members, False)

	def get_data(self):
		"""
		Get cluster creation dataexporter

		:return:
		"""
		deformlib.cluster.fix_clashing_handle_names()

		# get weighted node and prebind node
		self.relative = cmds.getAttr(self.deformer + ".relative")
		self.weighted_node = cmds.cluster(self.deformer, q=1, wn=1)
		self.prebind_node = cmds.listConnections("{}.bindPreMatrix".format(self.deformer), s=True, d=False)

		if self.prebind_node:
			self.prebind_node = self.prebind_node[0]

		# get weights for each shape in cluster
		weights_dict = {}
		for i in range(self.cls_members.length()):
			cmpts = om.MObject()
			mesh_dag_path = om.MDagPath()
			weight_array = om.MFloatArray()

			self.cls_members.getDagPath(i, mesh_dag_path, cmpts)
			self.fn_cls.getWeights(mesh_dag_path, cmpts, weight_array)

			name = mesh_dag_path.partialPathName()
			weight_array = [weight_array[i] for i in range(weight_array.length())]
			weights_dict[name] = weight_array

		# get mesh_data
		mesh_data = {}
		for shape in self.shapes:
			if cmds.nodeType(shape) == "mesh":
				mesh_data[shape] = geometrylib.mesh.extract_mesh_creation_data(selectionlib.get_original_shape(shape))

		self.data = {
			"name": self.deformer,
			"shapes": self.shapes,
			"weights": weights_dict,
			"relative": self.relative,
			"weightedNode": self.weighted_node,
			"prebindNode": self.prebind_node,
			"meshData": mesh_data
		}

	def save(self, file_path):
		"""
		Write weights file to disk as cPickle.

		:param file_path:
		:return:
		"""
		self.get_data()
		iolib.pickle.write(file_path, self.data)
		log.info("Saved {} to: {}".format(self.deformer, file_path))

	def set_soft_weights(self):
		"""
		Set soft selection weights

		:return:
		"""
		self.get_data()
		soft_weights = selectionlib.get_soft_selection_weights()

		new_shapes = soft_weights["weights"].keys()
		for i, shape in enumerate(new_shapes):
			shapec = []
			if cmds.nodeType(shape) == "mesh":
				shapec = cmds.ls("{}.vtx[*]".format(shape))

			if cmds.nodeType(shape) in ["nurbsCurve", "bezierCurve", "nurbsSurface"]:
				shapec = cmds.ls("{}.cv[*]".format(shape))

			if cmds.nodeType(shape) == "lattice":
				shapec = cmds.ls("{}.pt[*]".format(shape))

			if shapec:
				new_shapes[i] = shapec[0]

		# remove old members from set
		rm_members = []
		members = cmds.sets(self.deformer_set, q=1)
		for m in members:
			for s in new_shapes:
				if m.split(".")[0] in s:
					rm_members.append(m)

		cmds.sets(rm_members, rm=self.deformer_set)
		cmds.sets(new_shapes, add=self.deformer_set)

		self.reinitialize_deformer()
		self.set_weights(weight=0.0)
		self.set_weights(data=soft_weights)

	def set_weights(self, weight=1.0, data=None, shape_node=None):
		"""

		:param weight:
		:param data:
		:param shape_node:
		:return:
		"""
		# Get cmpts effected by deformer PER mesh
		dag_path = om.MDagPath()
		cmpts = om.MObject()

		for i in range(self.cls_members.length()):

			self.cls_members.getDagPath(i, dag_path, cmpts)
			name = selectionlib.get_shapes(dag_path.partialPathName())[0] or ""
			name = cmds.ls(name)[0] if cmds.ls(name) else name

			if shape_node and name != shape_node:
				continue

			# create api indexed cmt based on geo type
			node_type = cmds.nodeType(name)
			if node_type in ["mesh", "nurbsCurve"]:
				fn_comp = om.MFnSingleIndexedComponent(cmpts)

			elif node_type == "nurbsSurface":
				fn_comp = om.MFnDoubleIndexedComponent(cmpts)

			elif node_type == "lattice":
				fn_comp = om.MFnTripleIndexedComponent(cmpts)

			else:
				continue

			# Create mfloat array with single weight value
			cmpt_count = fn_comp.elementCount()
			weight_mfloat_array = om.MFloatArray(cmpt_count, weight)

			if data:
				weight_array = data["weights"].get(name) or {}
				weight_mfloat_array = om.MFloatArray(len(weight_array))

				for i, w in enumerate(weight_array):
					weight_mfloat_array.set(w, i)

			self.fn_cls.setWeight(dag_path, cmpts, weight_mfloat_array)
		return True

	@classmethod
	def load(cls, file_path=None, method="vertexID", remap=None, create_weighted_node=True, **kwargs):
		"""
		Load weights from file.

		:param file_path:
		:param method:
		:param remap:
		:param create_weighted_node:
		:return:
		"""
		data = remap_nodes(iolib.pickle.read(file_path), remap)

		# get dataexporter
		name = data.get("name")
		shapes = data.get("shapes")
		relative = data.get("relative")
		weighted_node = data.get("weightedNode")
		prebind_node = data.get("prebindNode")
		mesh_data = data.get("meshData")

		nodes_to_check = [n for n in shapes + [prebind_node] if n] if create_weighted_node \
			else [n for n in shapes + [weighted_node, prebind_node] if n]

		if utils.check_missing_nodes(name, nodes_to_check):
			return

		if cmds.objExists(name):
			cmds.delete(name)

		# Create new cluster
		weighted_node = weighted_node if cmds.objExists(weighted_node) else None
		deformer = deformlib.cluster.create_cluster(name, shapes, weighted_node, prebind_node, relative=relative)[0]
		cmds.setAttr("{}.envelope".format(deformer), 0)

		# Recreate the mesh and coy weights
		if method == "closestPoint":

			# recreate the original mesh for all shapes
			for shape, mesh_info in mesh_data.items():

				tmp_mesh = geometrylib.mesh.create_mesh("origDataMesh", **mesh_info)

				if tmp_mesh:
					tmp_deformer = deformlib.cluster.create_cluster("tmp_cluster_CLS", tmp_mesh[0])[0]
					tmp_cls_obj = Cluster(tmp_deformer)

					tmp_weight_dict = {tmp_mesh[1]: data["weights"][shape]}
					tmp_data = {"weights": tmp_weight_dict}
					tmp_cls_obj.set_weights(data=tmp_data)

					dup_shape = cmds.duplicate(shape)[0]
					dup_shape_node = selectionlib.get_shapes(dup_shape)[0]
					dup_deformer = deformlib.cluster.create_cluster("dup_cluster_CLS", dup_shape)[0]

					cmds.copyDeformerWeights(sourceDeformer=tmp_deformer,
					                         destinationDeformer=dup_deformer,
					                         sourceShape=tmp_mesh[1],
					                         destinationShape=dup_shape,
					                         surfaceAssociation="closestPoint",
					                         noMirror=True)

					dup_obj = cls(dup_deformer)
					dup_obj.get_data()
					dup_obj.data["weights"][shape] = dup_obj.data["weights"].get(dup_shape_node)

					new_cls_obj = cls(deformer)
					new_cls_obj.set_weights(shape_node=shape, data=dup_obj.data)
					cmds.delete(tmp_deformer, dup_shape, tmp_mesh[0])

		else:
			new_cls_obj = cls(deformer)
			new_cls_obj.set_weights(data=data)

		cmds.setAttr("{}.envelope".format(deformer), 1)


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.pickle.read(file_path)

	# get dataexporter
	shapes = data.get("shapes")
	weighted_node = data.get("weightedNode")
	prebind_node = data.get("prebindNode")

	nodes_to_check = [n for n in shapes + [weighted_node, prebind_node] if n]
	return nodes_to_check


def remap_nodes(data, remap):
	"""

	:param data:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	data = dict(data)
	weights_dict = data.get("weights")
	shapes = data.get("shapes")
	weighted_node = data.get("weightedNode") or ""
	prebind_node = data.get("prebindNode") or ""

	for search, replace in remap:

		# remap shape
		for i, shape in enumerate(shapes):
			if search in shape:
				shapes[i] = shape.replace(search, replace)

		data["shapes"] = shapes

		if search in weighted_node:
			data["weightedNode"] = weighted_node.replace(search, replace)

		if search in prebind_node:
			data["prebindNode"] = prebind_node.replace(search, replace)

		# remap influences
		for influence, value in weights_dict.items():
			if search in influence:
				r_influence = influence.replace(search, replace)

				if r_influence != influence:
					data['weights'][r_influence] = value
					del data['weights'][influence]

	return data


def save(deformer, file_path):
	"""

	:param deformer:
	:param file_path:
	:return:
	"""
	cls_obj = Cluster(deformer)
	cls_obj.save(file_path)


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param method:
	:param args:
	:param kwargs:
	:return:
	"""
	Cluster.load(file_path, **kwargs)
