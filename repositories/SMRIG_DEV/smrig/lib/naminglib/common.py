import itertools
import logging
import re
import string

import maya.cmds as cmds
import sys

if sys.version_info[0] < 3:
    string_types = (str, unicode)
else:
    string_types = (str,)

from smrig.env import prefs
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.naminglib.common")

LETTERS = [''.join(l) for length in range(1, 4) for l in itertools.product(string.ascii_uppercase, repeat=length)]
NODE_TYPE_SUFFIX = prefs._type_suffix
RE_ILLEGAL_CHARACTERS = re.compile("[^a-zA-Z0-9#_]")
RE_UNDERSCORE_DUPLICATE = re.compile("_+")


def format_name(*args, **kwargs):
	"""
	Format name as default system name "L_prefix_name1_name2_name3_GRP".

	:param args:
	:param kwargs: "node_type", "generate_new_index"
	:return:
	"""
	tokens = utilslib.conversion.as_list(args)
	generate_new_index = kwargs.get("generate_new_index")
	node_type = kwargs.get("node_type")

	if generate_new_index:
		tokens.append("#")

	if node_type:
		suffix = NODE_TYPE_SUFFIX.get(node_type)
		if suffix:
			tokens.append(suffix.upper())

	name = "_".join([str(n) for n in tokens])
	for search in re.findall("[a-zA-Z]_[0-9]", name):
		name = name.replace(search, search.replace("_", ""))

	return construct_unique_name(name) if generate_new_index else clean_name(name)


def construct_unique_name(name):
	"""
	Construct a unique name where the # character will be replaced with a
	letter. When a # character is not present one will be added between the
	last and the section before last split by a '_' character.

	:param str name:
	:return: Constructed unique name
	:rtype: str, int
	:raise RuntimeError: When unique name cannot be generated.
	"""
	# construct name
	name = clean_name(name)
	unique_name = clean_name(name.replace("#", ""))

	if not cmds.objExists(unique_name):
		return unique_name

	# generate name with letter
	for index, letter in enumerate(LETTERS):
		unique_name = clean_name(name.replace("#", str(index + 1), 1).replace("#", ""))
		if not cmds.objExists(unique_name):
			return unique_name

	# raise error
	error_message = "Unable to generate unique name from name '{}'.".format(name)
	log.error(error_message)
	raise RuntimeError(error_message)


def clean_name(name, strip_pound=False):
	"""
	Construct the provided name so it doesn't contain any characters other
	than a-z, A-Z, 0-9, # and _. Illegal characters will be replaced with an
	underscore after which any starting, ending or duplicating of underscores
	will be removed.

	:param str name:
	:param bool strip_pound:
	:return: Constructed name
	:rtype: str
	"""
	# conform name
	name_conformed = name.replace("#", "") if strip_pound else name
	name_conformed = RE_ILLEGAL_CHARACTERS.sub("_", name_conformed)
	name_conformed = RE_UNDERSCORE_DUPLICATE.sub("_", name_conformed)
	name_conformed = name_conformed.strip("_")

	for search in re.findall("[a-zA-Z]_[0-9]", name_conformed):
		name_conformed = name_conformed.replace(search, search.replace("_", ""))

	# debug conforming
	if name != name_conformed:
		log.debug("Conformed provided name '{}' to '{}'.".format(name, name_conformed))

	return name_conformed


# ----------------------------------------------------------------------------

def get_side():
	"""
	Get the side based on env prefs

	:return:
	"""


def get_suffix(node_type=None, node=None):
	"""
	Get the suffix based on a node type. It is possible to provide an existing
	node to this function. This node will have its shapes checked as well to
	make sure the suffix reflects a transforms possible content. If a node
	type doesn't exist the first 3 elements of the node type name will be used
	and upper cased, a warning will be displayed when this is the case. The
	suffixes are retrieved from the NODE_TYPE_SUFFIX variable in the constants.
	The variable contains suffixed for maya's internal node types and made up
	node types used for the rigging system.

	:param str/None node_type:
	:param str/None node:
	:return: Suffix
	:rtype: str
	:raise RuntimeError: When no node type is provided or retrieved from the node.
	"""
	# get node type from shape or node if no shapes exist
	if node is not None and cmds.objExists(node):
		shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
		shape = utilslib.conversion.get_first(shapes)
		node_type = cmds.nodeType(shape if shape else node)

	# validate node type
	if not node_type:
		error_message = "Unable to retrieve node type from node '{}'.".format(node) \
			if node \
			else "No node type provided."

		log.error(error_message)
		raise RuntimeError(error_message)

	# get suffix
	suffix = NODE_TYPE_SUFFIX.get(node_type)

	# validate suffix
	if not suffix:
		suffix = node_type[:3].upper()
		warning_message = "Suffix for node type '{}' is not present in the " \
		                  "constants, defaulting to '{}'.".format(node_type, suffix)

		log.debug(warning_message)

	return suffix.upper()


# ----------------------------------------------------------------------------


def split_suffix(name):
	"""
	Split a name and its suffix. will return a list of two if the last token is in fact a suffix otherwise
	return a list of 1. ei. ["C_my_control", "CTL"] or [""L_random_node"]

	:param name:
	:return:
	:rtype: list
	"""
	tokens = name.rsplit("_", 1)
	return tokens if tokens[-1] in NODE_TYPE_SUFFIX.values() else [name]


def strip_suffix(name):
	"""
	Strip suffix from name

	:param name:
	:return:
	"""
	return split_suffix(name)[0]


def replace_suffix(name, new_suffix, rename=False):
	"""
	replace the suffix of a node name, optionally rename it.

	:param name:
	:param new_suffix:
	:param rename:
	:return:
	"""
	tokens = split_suffix(name)
	new_name = "{}_{}".format(name, new_suffix) if len(tokens) < 2 else name.replace(tokens[-1], new_suffix)

	if rename and cmds.objExists(name):
		return cmds.rename(name, new_name)

	return new_name


def append_to_name(name, *args):
	"""

	:param name:
	:param args:
	:return:
	"""
	tokens = format_name(args)
	split_name = split_suffix(name)

	if len(split_name) > 1:
		split_name.insert(-1, tokens)
	else:
		split_name.append(tokens)

	return format_name(split_name)


def capitalize_first(name):
	"""
	Capitalize first letter while maintaining camelCase

	:param name:
	:return:
	"""
	return name[0].upper() + name[1:]


def remove_namespace(nodes):
	"""
	Rename and remove namespace.

	:param nodes:
	:return:
	"""
	if isinstance(nodes, string_types):
		return cmds.rename(nodes, nodes.split(":")[-1])
	else:
		return [cmds.rename(n, n.split(":")[-1]) for n in utilslib.conversion.as_list(nodes)]
