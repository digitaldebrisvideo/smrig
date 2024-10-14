import maya.cmds as cmds

from smrig.lib import selectionlib
from smrig.lib import utilslib


def parent_shapes(shapes, parent, remove_source_shapes=False, remove_target_shapes=False):
	"""
	Parent the shapes underneath the source of provided shapes under the
	target parent. It is possible to either remove the source or the
	original target shapes if desired.

	:param str/list shapes:
	:param str parent:
	:param bool remove_source_shapes:
	:param bool remove_target_shapes:
	"""
	# store target shapes
	target_shapes = cmds.listRelatives(parent, shapes=True)

	# get source shapes
	source_shapes = utilslib.conversion.as_list(shapes)
	source_shapes = selectionlib.extend_with_shapes(source_shapes)
	source_shapes = [shape for shape in source_shapes if cmds.nodeType(shape) != "transform"]

	# parent source shapes
	cmds.parent(source_shapes, parent, shape=True, add=True)

	# remove source shapes
	if remove_source_shapes:
		cmds.delete(shapes)

	# remove target shapes
	if remove_target_shapes and target_shapes:
		cmds.delete(target_shapes)

	# rename shapes
	for i, shape in enumerate(cmds.listRelatives(parent, shapes=True) or []):
		cmds.rename(shape, "{}Shape{}".format(parent, i + 1))
