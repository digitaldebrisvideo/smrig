import logging

import maya.OpenMaya as om
import maya.cmds as cmds

from smrig.lib import naminglib
from smrig.lib import nodepathlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.selectionlib")


def extend_with_shapes(selection, ignore_intermediate=True, full_path=True):
	"""
	:param str/list selection:
	:param bool ignore_intermediate:
	:param bool full_path:
	:return: Selection extended by its shape nodes
	:rtype: list
	"""
	extended_selection = utilslib.conversion.as_list(selection)[:]
	extended_selection = cmds.ls(extended_selection, l=full_path)
	extended_selection.extend(
		cmds.listRelatives(
			selection,
			shapes=True,
			noIntermediate=ignore_intermediate,
			path=True,
			fullPath=full_path
		) or []
	)

	return extended_selection


def filter_by_type(selection, types=None):
	"""
	:param str/list selection:
	:param str/list types:
	:return: Filtered selection
	:rtype: list
	"""
	types = utilslib.conversion.as_list(types)[:]
	types = nodepathlib.get_derived_node_types(types)
	selection = utilslib.conversion.as_list(selection)[:]

	return [
		sel
		for sel in selection
		if cmds.nodeType(sel) in types
	]


def filter_by_exist(selection):
	"""
	:param str/list selection:
	:return: Filtered selection
	:rtype: list
	"""
	selection = utilslib.conversion.as_list(selection)
	return [
		sel
		for sel in selection
		if cmds.objExists(sel)
	]


def exclude_type(selection, types=None):
	"""
	:param str/list selection:
	:param str/list types:
	:return: Filtered selection
	:rtype: list
	"""
	# variables
	types = utilslib.conversion.as_list(types)[:]
	types = nodepathlib.get_derived_node_types(types)
	selection = utilslib.conversion.as_list(selection)[:]

	return [
		sel
		for sel in selection
		if cmds.nodeType(sel) not in types
	]


# ----------------------------------------------------------------------------


def sort_by_hierarchy(selection):
	"""
	:param selection:
	:return: Ordered selection
	:rtype: list
	"""
	# TODO: find quicker way to sort?
	nodes = cmds.ls(l=True)
	selection = selection[:]
	selection.sort(key=lambda x: nodes.index(nodepathlib.get_long_name(x)))

	return selection


# ----------------------------------------------------------------------------


def get_parents(node, num=-1, full_path=False):
	"""
	Get the number of parent provided from the node returned as a list.
	If the number is higher than the amount of parents it will return
	all parents and not error.

	:param str node:
	:param int num: number of parents, if num is -1 all parents will be returned.
	:param bool full_path:
	:return: Parents
	:rtype: list
	"""
	num = num if num > 0 else len(nodepathlib.get_long_name(node).split('|'))

	parent = node
	parents = []

	for i in range(num):
		parent = cmds.listRelatives(parent, parent=True, fullPath=full_path)
		if not parent:
			return parents

		parents.extend(parent)

	return parents


def get_parent(node, full_path=False):
	"""
	Get the first parent of a node. If the node has no parents a None
	type will be returned.

	:param str node:
	:param bool full_path:
	:return: str/None
	"""
	parents = get_parents(node, num=1, full_path=full_path)
	return utilslib.conversion.get_first(parents)


def get_top_parent(node, full_path=False):
	"""
	Get top parent node in hierarchy. Returns node if no parent found
	:param node:
	:param full_path:
	:return:
	"""
	parents = get_parents(node, full_path=full_path)
	return parents[-1] if parents else cmds.ls(node, l=full_path)[0]


# ----------------------------------------------------------------------------


def get_transform(node, full_path=False):
	"""
	Get the transform of a provided shape. If the node provided is a transform
	or a joint the original node will be returned.

	:param str node:
	:param bool full_path:
	:return: Transform
	:rtype: str
	"""
	transform = filter_by_type(node, types=["transform", "joint"])
	if transform:
		return nodepathlib.get_long_name(transform[0])
	else:
		return get_parent(node, full_path=full_path)


def get_children(
		selection,
		all_descendents=False,
		ignore_shapes=True,
		ignore_intermediate=True,
		types=None,
		full_path=False
):
	"""
	Get the children from a selection with the possibility to filter it based
	on its arguments. All descendents can be taken into account. Shapes
	ignored and filtering certain types.

	:param str/list selection:
	:param bool all_descendents:
	:param bool ignore_shapes:
	:param bool ignore_intermediate:
	:param str/list types:
	:param bool full_path:
	:return: Children
	:rtype: list
	"""
	# convert selection
	selection = utilslib.conversion.as_list(selection)

	# validate selection
	for sel in selection[:]:
		if not cmds.objExists(sel):
			log.warning("Unable to retrieve children from node '{}' as it doesn't exist.".format(sel))
			selection.remove(sel)

	if not selection:
		return []

	# get children
	children = cmds.listRelatives(
		selection,
		children=True,
		allDescendents=all_descendents,
		noIntermediate=ignore_intermediate,
		path=True,
		fullPath=full_path
	) or []

	if ignore_shapes:
		shapes = get_shapes(children, ignore_intermediate=ignore_intermediate, full_path=full_path)
		children = [child for child in children if child not in shapes]

	if types:
		children = filter_by_type(children, types=types)

	return children


# ----------------------------------------------------------------------------


def get_shapes(selection, ignore_intermediate=True, full_path=True):
	"""
	Return shape from specified node, if the node IS a shape node then it
	returns the node itself.

	:param str/list selection:
	:param bool ignore_intermediate:
	:param bool full_path:
	:return: Shapes
	:rtype: list
	"""
	selection = utilslib.conversion.as_list(selection)
	selection = extend_with_shapes(selection, ignore_intermediate=ignore_intermediate, full_path=full_path)
	shapes = exclude_type(selection, types=["transform", "joint"])

	return shapes


def get_original_shape(node, full_path=True):
	"""
	Get the last intermediate shape, which is the original shape.

	:param str node:
	:param bool full_path:
	:return: Original shape
	:rtype: str
	:raise RuntimeError: When the provided node contains no shapes
	"""
	transform = get_transform(node, full_path=True)
	shapes = get_shapes(transform, ignore_intermediate=False, full_path=full_path)

	if not shapes:
		error_message = "Transform '{}' contains no shapes.".format(transform)
		log.error(error_message)
		raise RuntimeError(error_message)

	return shapes[-1]


# ----------------------------------------------------------------------------


def get_history(selection, include_shapes=False, types=None, full_path=False):
	"""
	Query the history of the selection filter the selection by the provided
	types. If no types are provided the entire history will be returned. It is
	possible to extend your selection with its shapes in case you expect the
	history to be present on its shapes.

	:param str/list selection:
	:param bool include_shapes:
	:param str/list types:
	:param bool full_path:
	:return: History
	:rtype: list
	"""
	# TODO: include history query options?

	if include_shapes:
		selection = extend_with_shapes(selection)

	history = cmds.listHistory(selection) or []
	history = filter_by_type(history, types=types)

	return cmds.ls(history, l=full_path)


# ----------------------------------------------------------------------------


def print_as_pylist(selection=None, num_columns=4):
	"""
	Print selection as a python list variable in a column formated list.

	:selection list/str/None: list of nodes to print
	:num_columns int: number of columns.
		:rtype: None
	"""

	selection = selection if selection else cmds.ls(sl=1)
	selection = ['"{}",'.format(s) for s in selection]

	indent = '\t'
	print('selection = [')
	for i, item in enumerate(selection, 1):
		print(indent + item),
		if i % num_columns == 0:
			indent = '\t'

		else:
			indent = ''
	print('\n]')


def reverse_list(selection=None):
	"""
	Reverse list or current selection.

	:selection list: List to reverse
	:return: Reversed list
	:rtype: list
	"""
	selection = selection if selection else cmds.ls(sl=1)
	return [item for item in reversed(selection)]


def reverse_selection(selection=None):
	"""

	:param selection:
	:return:
	"""
	cmds.select(reverse_list(selection))


def select_mirrored_nodes(selection=None, add=False):
	"""
	Select mirrored node names.

	:selection list/None: list of nodes to find mirrors
	:add bool: Add to current selection
		:rtype: None
	"""
	selection = selection if selection else cmds.ls(sl=1)
	selection = cmds.ls(selection)

	cmds.select(cmds.ls([naminglib.conversion.mirror_name(n) or '' for n in selection]), add=add)


def get_soft_selection_weights():
	"""
	Get the weight value for the current soft selection.

	:return:
	"""
	soft_weights = {"weights": {}}

	try:
		rich_sel = om.MRichSelection()
		om.MGlobal.getRichSelection(rich_sel)
		rich_sel_list = om.MSelectionList()
		rich_sel.getSelection(rich_sel_list)
		sel_count = rich_sel_list.length()

	except:
		return

	# get each soft sel from each object
	for x in range(sel_count):

		shape_dag_path = om.MDagPath()
		shape_comp = om.MObject()
		rich_sel_list.getDagPath(x, shape_dag_path, shape_comp)
		name = cmds.ls(shape_dag_path.fullPathName())[0]
		ntype = cmds.nodeType(name)

		weight_array = None

		if ntype in ["nurbsCurve", "mesh"]:
			cmpt_count = cmds.polyEvaluate(name, v=1) if ntype == "mesh" else len(cmds.ls(name + ".cv[*]", fl=1))
			weight_array = om.MFloatArray(cmpt_count, 0.0)
			comp_fn = om.MFnSingleIndexedComponent(shape_comp)

			# get weight value from each soft selected cmpt
			for i in range(comp_fn.elementCount()):
				vert_id = comp_fn.element(i)
				weight = comp_fn.weight(i).influence()
				weight_array[int(vert_id)] = weight

		elif ntype == "nurbsSurface":
			cmpt_sel = [c.split(".")[-1] for c in cmds.ls(name + ".cv[*]", fl=1)]
			weight_array = om.MFloatArray(len(cmpt_sel), 0.0)

			u_list = om.MIntArray()
			v_list = om.MIntArray()
			comp_fn = om.MFnDoubleIndexedComponent(shape_comp)
			comp_fn.getElements(u_list, v_list)

			# get weight value from each soft selected cmpt
			for i in range(comp_fn.elementCount()):
				weight = comp_fn.weight(i).influence()
				weight_array[cmpt_sel.index("cv[{0}][{1}]".format(u_list[i], v_list[i]))] = weight

		elif ntype == "lattice":
			cmpt_sel = [c.split(".")[-1] for c in cmds.ls(name + ".pt[*]", fl=1)]
			weight_array = om.MFloatArray(len(cmpt_sel), 0.0)

			u_list = om.MIntArray()
			v_list = om.MIntArray()
			w_list = om.MIntArray()
			comp_fn = om.MFnTripleIndexedComponent(shape_comp)
			comp_fn.getElements(u_list, v_list, w_list)

			for i in range(comp_fn.elementCount()):
				weight = comp_fn.weight(i).influence()
				weight_array[cmpt_sel.index("pt[{0}][{1}][{2}]".format(u_list[i], v_list[i], w_list[i]))] = weight

		elif ntype == "transform":
			shape = get_shapes(name)
			shape = shape[0] if shape else None

			if not shape:
				continue

			cmpt_count = cmds.polyEvaluate(name, v=1) if cmds.nodeType(shape) == "mesh" \
				else len(cmds.ls("{}.cv[*]".format(name), "{}.pt[*]".format(name), fl=1))

			if cmpt_count:
				weight_array = om.MFloatArray(cmpt_count, 1.0)

		name = get_shapes(name, full_path=False)
		if name and weight_array:
			soft_weights["weights"][name[0]] = weight_array

	return soft_weights
