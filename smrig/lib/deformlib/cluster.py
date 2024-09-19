import maya.cmds as cmds

from smrig.lib import naminglib
from smrig.lib import selectionlib
from smrig.lib import utilslib


def create_cluster(components=None, name=None, weighted_node=None, prebind_node=None, relative=False):
	"""
	Create a cluster handle in the shape of a locator for the provided
	components.

	:param str name:
	:param str/list components:
	:param float/int local_scale:
	:param bool relative:
	:return: Cluster and cluster handle
	:rtype: tuple
	"""
	name = name if name else None
	name = name if name else weighted_node + "_CLS" if weighted_node else "cluster#"
	components = components if components else cmds.ls(sl=1, fl=1)

	if weighted_node:
		cluster, cluster_handle = cmds.cluster(components, bs=1, wn=[weighted_node] * 2, name=name, relative=relative)
	else:
		cluster, cluster_handle = cmds.cluster(components, name=name, relative=relative)

	if prebind_node:
		add_prebind_node_to_cluster(cluster, prebind_node)

	fix_clashing_handle_names()
	return cluster, weighted_node


def add_prebind_node_to_cluster(cluster, prebind_node):
	"""

	:param cluster:
	:param prebind_node:
	:return:
	"""
	cmds.connectAttr("{}.parentInverseMatrix".format(prebind_node), "{}.bindPreMatrix".format(cluster), f=True)


def cluster_curve_cvs(curve, start_index=None, end_index=None, grouping=1, relative=False):
	"""
	Clusters all or a range of CVs on the given curve.

	Example:
		.. code-block:: python

			cluster_curve_cvs(curve='C_spine_001_CRV', start_index=0, end_index=10, grouping=3)

	:param str curve: The curve to be clustered.
	:param int/None start_index:
	:param int/None end_index:
	:param int grouping:
	:param float/int local_scale:
	:param bool relative:
	:return: Locators
	:rtype: list
	"""
	# variable
	locators = []

	# get cvs
	cvs = cmds.ls("{}.cv[*]".format(curve), fl=True) or []
	cvs = cvs[start_index:end_index]
	cv_chunks = utilslib.conversion.as_chunks(cvs, grouping)

	# create clusters
	for num, cv_chunk in enumerate(cv_chunks):
		# define cluster name
		cluster_name = "{0}_{1:03d}_CLS".format(curve, num + 1)

		# create cluster
		_, locator = create_cluster(cv_chunk, cluster_name, relative)
		locators.append(locator)

	# TODO: add null group?
	# TODO: numeration from start number, ever run this function on the same curve twice?

	return locators


def set_soft_weights(cluster):
	"""
	Set soft selection weights.

	:return:
	"""
	from smrig.dataio.types.cluster import Cluster

	cls = Cluster(cluster)
	cls.set_soft_weights()

	print("Set soft weights on: " + cluster)


def fix_clashing_handle_names():
	"""

	:return:
	"""

	dup_handle_names = [h for h in cmds.ls(sn=1, type="clusterHandle") if "|" in h]
	for handle in dup_handle_names:
		parent = selectionlib.get_parent(handle)
		suffix = "clusterHandle"

		new_name = naminglib.construct_unique_name("{}#_{}".format(parent, suffix))
		if cmds.objExists(handle):
			cmds.rename(handle, new_name)
