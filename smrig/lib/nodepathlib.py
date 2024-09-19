"""
Similar functionality is available in the commsmayalib package. Reason for
not using those is that not many people are aware of what is available in
other packages.
"""
import logging

import maya.cmds as cmds

from smrig.lib import decoratorslib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.nodepathlib")


def get_name(node):
	"""
	Returns the node name without hierarchy, but including namespace.

	:param str node:
	:return: Node name
	:rtype: str
	"""
	return node.rsplit("|", 1)[-1]


def get_leaf_name(node):
	"""
	Returns the node name without hierarchy and without namespace.

	:param str node:
	:return: Node leaf name
	:rtype: str
	"""
	return get_name(node).rsplit(":", 1)[-1]


def get_long_name(node):
	"""
	Returns the long name of a node.

	:param str node:
	:return: Node long name
	:rtype: string
	"""
	return cmds.ls(node, l=True)[0]


def get_partial_name(node):
	"""
	Get the shortest unique path of a full path node. The reason for not
	implementing retrieving it via the API is that it could be that the
	full path is invalid.

	:param str node:
	:return: Partial path
	:rtype: str
	"""
	split = node.split("|")
	split.reverse()

	partial = ""
	for i, s in enumerate(split):
		if i == 0:
			partial = s
		else:
			partial = "|".join([s, partial])

		if len(cmds.ls(partial) or []) == 1:
			return partial


def get_namespace(node):
	"""
	Returns the node namespace ignoring hierarchical parents.
	If no namespace is found None will be returned.

	Example:
		.. code-block:: python

			get_namespace("aaa:bbb|ccc:ddd")
			// "ccc"

	:param str node:
	:return: Namespace
	:rtype: str/None
	"""
	node_name = get_name(node)
	if node_name.count(":"):
		return node_name.rsplit(":", 1)[0]


def add_namespace(node, namespace):
	"""
	Add a namespace to the node path. The function is able to handle full path
	or single path nodes. The provided namespace should not contain the
	trailing semicolon as it will be added via the script.

	:param str node:
	:param str namespace:
	:return: Namespaced path
	:rtype: str
	"""
	path = ""
	sections = node.split("|")
	sections_num = len(sections)

	for i, section in enumerate(sections):
		if section:
			path += "{}:{}".format(namespace, section)

		if i < sections_num - 1:
			path += "|"

	return path


def remove_namespace(node):
	"""
	Remove the namespace from the node path. The function is able to handle
	full path or single path nodes.

	:param str node:
	:return: Namespace-less path
	:rtype: str
	"""
	path = ""
	sections = node.split("|")
	sections_num = len(sections)

	for i, section in enumerate(sections):
		if section:
			path += section.split(":")[-1]

		if i < sections_num - 1:
			path += "|"

	return path


@decoratorslib.memoize
def get_derived_node_types(types):
	"""
	Get the derived node types including the provided ones from a list
	of specific type.

	:param str/list types:
	:return: Derived types
	:rtype: list
	"""
	# variables
	derived_types = []
	types = utilslib.conversion.as_list(types)

	# get derived types
	for type_ in types:
		try:
			derived_types.extend(cmds.nodeType(type_, derived=True, isTypeName=True) or [])
		except RuntimeError as e:
			log.warning(str(e))

	return derived_types


def get_clashing_node_names():
	"""
	Get clashing non-unique node names.

	:return: All clashing node names in scene.
	:rtype: list
	"""
	return [n for n in cmds.ls(sn=1) if '|' in n]


def print_clashing_nodes_names():
	"""
	Print clashing non-unique node names.

		:rtype: None
	"""
	clashing_nodes = get_clashing_node_names()

	if clashing_nodes:
		message = 'Found non-unique node names in scene:\n\t'
		message += '\n\t'.join(clashing_nodes)
		cmds.select(clashing_nodes)

	else:
		message = 'All node names are unique :)'

	log.info(message)
