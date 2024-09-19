from maya import cmds

from smrig.dataioo import tools

deformer_type = "cluster"
file_type = "pickle"


class Cluster(object):
	attrs = ["envelope",
	         "relative",
	         "matrix",
	         "bindState"]

	def __init__(self, deformer):
		self.deformer = deformer
		self.data = {}

	def get_data(self):
		"""
		Get deformer creation data.

		:return dict: creation data to export
		"""
		weighted_node = cmds.cluster(self.deformer, q=1, wn=1)
		prebind_node = cmds.listConnections("{}.bindPreMatrix".format(self.deformer), s=True, d=False)
		prebind_node = prebind_node[0] if prebind_node else prebind_node

		geo_data = tools.get_geometry_data(self.deformer)
		attrs_data = tools.get_attributes_data(self.deformer, self.attrs)
		xform_data = tools.get_transform_data([weighted_node, prebind_node])

		self.data = {"name": self.deformer,
		             "deformer_type": deformer_type,
		             "geometry": geo_data,
		             "transforms": xform_data,
		             "attributes": attrs_data}

		return self.data

	@classmethod
	def set_data(cls, data, method="auto", **kwargs):
		"""
		Set / Create deformer from creation data.

		:param dict data:
		:param str method: auto, vertex, uv, closest (auto will default vertex first then closest if vert count is off)
		:param bool rebuild: recreate the deformer (if it exists in scene it deletes it and recreates it)
		:param kwargs:
		:return:
		"""
		deformer = data.get("name")
		geo_data = data.get("geometry")
		node_data = data.get("transforms")
		attrs_data = data.get("attributes")
		weighted_node = node_data[0].get("name")
		prebind_node = node_data[1].get("name")

		method = tools.evaluate_method(geo_data, method) if method == "auto" else method

		full_shape = False if method in "vertex" else True
		deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, full_shape=full_shape)

		# Create deformer
		if not cmds.objExists(deformer):
			deformer, handle = create_cluster(deformed_cmpts, deformer, weighted_node, attrs_data.get("bindState"))

		# connect prebind node
		if prebind_node and cmds.objExists(prebind_node):
			connect_prebind_node(deformer, prebind_node)

		# apply weights
		if method in "vertex":
			tools.set_weights(deformer, geo_data=geo_data)

		else:
			transfer_geos = tools.build_transfer_geos(geo_data)
			t_deformed_cmpts = tools.generate_deform_cmpts_list(geo_data, transfer_geos)

			t_deformer, t_handle = create_cluster(t_deformed_cmpts, deformer + "_TRANSFER",
			                                      bs=attrs_data.get("bindState"))
			tools.set_weights(t_deformer, value=1, geo_data=geo_data)

			tools.transfer_deformer_weights(t_deformer, deformer, transfer_geos, geo_data, method)
			cmds.delete(t_deformer, t_handle, [t[0] for t in transfer_geos])

		# set attrs data
		tools.set_attributes_data(deformer, attrs_data)


def get_data(deformer, **kwargs):
	"""
	Wrapper for gathering creation data for export.

	:param deformer:
	:return:
	"""
	obj = Cluster(deformer)
	return obj.get_data()


def set_data(data, method="auto", **kwargs):
	"""
	Wrapper for creating and setting deformer weights.

	:param file_path:
	:param method:
	:param kwargs:
	:return:
	"""
	Cluster.set_data(data, method=method, **kwargs)


def create_cluster(deformed_cmpts, name, weighted_node=None, bs=True):
	"""
	Cluster create

	:param deformed_cmpts:
	:param name:
	:param weighted_node:
	:param bs:
	:return:
	"""
	if weighted_node and cmds.objExists(weighted_node):
		return cmds.cluster(deformed_cmpts, name=name, bs=bs, wn=[weighted_node, weighted_node])

	else:
		return cmds.cluster(deformed_cmpts, name=name, bs=bs)


def connect_prebind_node(cluster, prebind_node):
	"""
	Connect a node to the bindPreMatrix attr of cluster

	:param cluster:
	:param prebind_node:
	:return:
	"""
	cmds.connectAttr("{}.parentInverseMatrix".format(prebind_node), "{}.bindPreMatrix".format(cluster), f=True)
