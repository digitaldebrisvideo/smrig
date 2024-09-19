import logging

import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import geometrylib
from smrig.lib import iolib
from smrig.lib import nodepathlib
from smrig.lib import selectionlib

deformer_type = "skinCluster"
file_extension = utils.get_extension(deformer_type).lower()
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


class SkinCluster(object):
	weights = {}
	blend_weights = []
	data = {}

	def __init__(self, deformer):
		self.deformer = deformer
		self.shape = cmds.skinCluster(deformer, q=True, g=True)[0]
		# self.def_set = cmds.listConnections(self.deformer, type='objectSet')[0]
		self.def_set = cmds.listConnections(self.deformer)[0]
		self.def_cmpts = cmds.ls(cmds.sets(self.def_set, q=1), fl=1)
		self.skn_obj = om.MObject()
		self.skn_dag_path = om.MDagPath()
		self.skn_cmpts = om.MObject()
		self.skn_members = om.MSelectionList()

		sel_list = om.MSelectionList()
		sel_list.add(self.deformer)
		sel_list.getDependNode(0, self.skn_obj)

		self.fn_skn = oma.MFnSkinCluster(self.skn_obj)
		self.fn_set = om.MFnSet(self.fn_skn.deformerSet())
		self.fn_set.getMembers(self.skn_members, False)
		self.skn_members.getDagPath(0, self.skn_dag_path, self.skn_cmpts)

	def get_data(self):
		"""
		Gather all dataexporter for export

		:return:
		"""
		self.get_weights()
		self.get_blend_weights()

		if cmds.nodeType(self.shape) == "mesh":
			shape_orig = selectionlib.get_original_shape(self.shape, full_path=True)
			mesh_data = geometrylib.mesh.extract_mesh_creation_data(shape_orig)
		else:
			mesh_data = {
				"matrix": [],
				"points": [],
				"triangles": []
			}
			log.warning("This is not a mesh.. Cannot get creation data.")

		self.data = {
			'name': self.deformer,
			'shape': nodepathlib.remove_namespace(self.shape),
			'skinningMethod': cmds.getAttr("{}.skinningMethod".format(self.deformer)),
			'normalizeWeights': cmds.getAttr("{}.normalizeWeights".format(self.deformer)),
			'deformUserNormals': cmds.getAttr("{}.deformUserNormals".format(self.deformer)),
			'weights': self.weights,
			'blendWeights': list(self.blend_weights),
			'meshData': mesh_data
		}

	def get_blend_weights(self):
		"""
		Get DQ blend weights as MDoubleArray

		:return:
		"""
		self.blend_weights = om.MDoubleArray()
		self.fn_skn.getBlendWeights(self.skn_dag_path, self.skn_cmpts, self.blend_weights)

	def get_weights(self):
		"""
		Get weights dataexporter as dict.

		:return:
		"""
		weights = self.get_weights_array()
		inf_path_array = om.MDagPathArray()
		number_infs = self.fn_skn.influenceObjects(inf_path_array)
		number_cmpts_per_inf = int(weights.length() / number_infs)

		self.weights = {}
		for i in range(inf_path_array.length()):
			inf_name = cmds.ls(inf_path_array[i].fullPathName(), sn=1)[0]
			inf_name = nodepathlib.remove_namespace(inf_name)

			weight_list = [weights[ii * number_infs + i] for ii in range(number_cmpts_per_inf)]
			self.weights[inf_name] = weight_list

	def get_weights_array(self):
		"""
		Get weights array for single influence as MDoubleArray

		:return:
		"""
		weights = om.MDoubleArray()
		p_int_util = om.MScriptUtil()
		p_int_util.createFromInt(0)
		p_int = p_int_util.asUintPtr()

		self.fn_skn.getWeights(self.skn_dag_path, self.skn_cmpts, weights, p_int)
		return weights

	def save(self, file_path):
		"""
		Write weights file to disk as cPickle.

		:param file_path:
		:return:
		"""
		self.get_data()
		iolib.pickle.write(file_path, self.data)
		log.info("Saved {} to: {}".format(self.deformer, file_path))

	def set_data(self, data):
		"""
		Set skin cluster dataexporter, weights and blend weights from a dataexporter dict.

		:param data:
		:return:
		"""
		cmds.setAttr("{}.skinningMethod".format(self.deformer), data['skinningMethod'])
		cmds.setAttr("{}.normalizeWeights".format(self.deformer), data['normalizeWeights'])
		cmds.setAttr("{}.deformUserNormals".format(self.deformer), data['deformUserNormals'])

	def set_blend_weights(self, blend_weights):
		"""
		Set blend weights from a list of floats

		:param blend_weights:
		:return:
		"""
		blend_weights_array = om.MDoubleArray(len(blend_weights))
		for i, w in enumerate(blend_weights):
			blend_weights_array.set(w, i)

		self.fn_skn.setBlendWeights(self.skn_dag_path, self.skn_cmpts, blend_weights_array)
		self.blend_weights = blend_weights

	def set_weights(self, weights_dict):
		"""
		Set weights from weight dataexporter dict

		:param weights_dict:
		:return:
		"""
		weights = self.get_weights_array()
		inf_path_array = om.MDagPathArray()
		number_infs = self.fn_skn.influenceObjects(inf_path_array)
		number_cmpts_per_inf = weights.length() / number_infs

		try:
			for influence, weight_list in weights_dict.items():
				for i in range(inf_path_array.length()):
					inf_name = cmds.ls(inf_path_array[i].fullPathName(), sn=1)[0]
					inf_name = nodepathlib.remove_namespace(inf_name)

					if inf_name == influence:
						for ii in range(number_cmpts_per_inf):
							weights.set(weight_list[ii], ii * number_infs + i)
		except:
			return

		self.set_weights_array(weights)
		self.weights = weights_dict
		return True

	def set_weights_array(self, weights_array):
		"""
		This sets the weights from an MDoubleArray input object.

		:param weights_array:
		:return:
		"""
		inf_path_array = om.MDagPathArray()
		number_infs = self.fn_skn.influenceObjects(inf_path_array)
		inf_indecies = om.MIntArray(number_infs)

		for i in range(number_infs):
			inf_indecies.set(i, i)

		cmds.setAttr("{}.normalizeWeights".format(self.deformer), False)
		self.fn_skn.setWeights(self.skn_dag_path, self.skn_cmpts, inf_indecies, weights_array, False)

	@classmethod
	def load(cls, file_path=None, method="vertexID", remap=None):
		"""
		Load weights from file.

		:param file_path:
		:param method:
		:param remap:
		:return:
		"""
		data = remap_nodes(iolib.pickle.read(file_path), remap)

		name = data.get("name")
		shape = data.get("shape")
		weights = data.get("weights")
		blend_weights = data.get("blendWeights")
		mesh_data = data.get("meshData")

		if utils.check_missing_nodes(name, [shape] + list(weights.keys())):
			return (name, [shape] + list(weights.keys()))

		influences = selectionlib.sort_by_hierarchy(list(weights.keys()))

		# unbind current geo and create skin cluster
		if utils.get_deformers(shape, deformer_type):
			cmds.skinCluster(shape, e=True, ub=True)

		# Create new skin cluster
		deformer = cmds.skinCluster(shape, influences, tsb=1, n=name)[0]
		cmds.setAttr(selectionlib.get_transform(shape, full_path=True) + ".inheritsTransform", 0)
		skin = cls(deformer)

		if method == "vertexID":
			if skin.set_weights(weights):
				skin.set_blend_weights(blend_weights)

			else:
				method = "closestPoint"
				log.warning("Could not assign weights to {}. Trying 'closestPoint' method".format(shape))

		if method in ["closestPoint", "uvSpace"] and cmds.nodeType(shape) == "mesh":
			source_shape = geometrylib.mesh.create_mesh("origDataMesh", **mesh_data)
			source_deformer = cmds.skinCluster(source_shape[0], influences, tsb=1)[0]

			sourece_skn = cls(source_deformer)
			sourece_skn.set_blend_weights(blend_weights)
			sourece_skn.set_weights(weights)

			# Copy weights
			cmds.copySkinWeights(ss=source_deformer, ds=deformer, nm=True, sa=method, ia="oneToOne")
			cmds.copySkinWeights(ss=source_deformer, ds=deformer, nm=True, nbw=True, sa=method, ia="oneToOne")
			cmds.delete(source_deformer, source_shape)

		skin.set_data(data)
		log.debug("Loaded: {}".format(deformer))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.pickle.read(file_path)
	shape = data.get("shape")
	weights = data.get("weights")

	return [shape] + weights.keys()


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
	shape = data.get("shape")

	for search, replace in remap:

		# remap shape
		if search in shape:
			data["shape"] = shape.replace(search, replace)

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
	skin_obj = SkinCluster(deformer)
	skin_obj.save(file_path)


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
	SkinCluster.load(file_path, method=method, remap=remap)
