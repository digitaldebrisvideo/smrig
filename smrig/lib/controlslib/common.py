import logging

import maya.cmds as cmds

from smrig.lib import attributeslib
from smrig.lib import colorlib
from smrig.lib import decoratorslib
from smrig.lib import geometrylib
from smrig.lib import naminglib
from smrig.lib import nodeslib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.lib.controlslib import library

log = logging.getLogger("smrig.lib.controlslib.common")

TAG = "smrigControl"
TAG_SHAPE = "smrigControlShape"
TAG_GROUPS = "smrigControlGroups"
TAG_OFFSET_CONTROLS = "smrigControlOffsets"
TAG_PIVOT_CONTROL = "smrigPivotControl"
TAG_OFFSET_CONTROL = "smrigOffsetControl"
GROUP_NAMES = ["zero", "space", "offset"]


class Control(object):
	"""
	The Control class handles the creation and management of the control
	shapes. It makes it possible to alter the shapes, their color. And have
	access to its offset groups for easy parenting. It will also enforce the
	control naming convention.

	:param str path:
	"""

	CONTROL_TYPE = "animControl"
	SUFFIX = naminglib.get_suffix(CONTROL_TYPE)

	def __init__(self, path):
		if not cmds.objExists(path):
			error_message = "Control cannot be initialized as the provided path '{}' doesn't exist.".format(path)
			log.error(error_message)
			raise ValueError(error_message)

		self._path = path

	# ------------------------------------------------------------------------

	def __str__(self):
		return self.path

	def __repr__(self):
		return self.path

	# ------------------------------------------------------------------------

	@property
	def path(self):
		"""
		:return: Control path
		:rtype: str
		"""
		return str(self._path)

	@property
	def groups(self):
		"""
		:return: Control offset groups
		:rtype: list
		"""
		if not cmds.objExists("{}.{}".format(self.path, TAG_GROUPS)):
			return []

		num_offsets = cmds.getAttr("{}.{}".format(self.path, TAG_GROUPS))
		if not num_offsets:
			return []
		return selectionlib.get_parents(self.path, num_offsets)

	@property
	def offset_controls(self):
		"""
		:return: Control offset groups
		:rtype: list
		"""
		if not cmds.objExists("{}.{}".format(self.path, TAG_OFFSET_CONTROLS)):
			return []

		offset_ctrls = []
		offset_ctrl = self.path

		for i in range(cmds.getAttr("{}.{}".format(self.path, TAG_OFFSET_CONTROLS))):
			offset_ctrl = [c for c in selectionlib.get_children(offset_ctrl, all_descendents=False)
			               if cmds.objExists("{}.{}".format(c, TAG_OFFSET_CONTROL))]

			if offset_ctrl:
				offset_ctrls.append(Control(offset_ctrl[0]))

		return offset_ctrls

	@property
	def last_node(self):
		return self.offset_controls[-1].path if self.offset_controls else self.path

	@property
	def all_controls(self):
		"""
		list of control name and offset controls .

		:return:
		"""
		return [self.path] + [c.path for c in self.offset_controls]

	# ------------------------------------------------------------------------

	@property
	def color(self):
		"""
		:return: Control color
		:rtype: int/None
		"""
		return nodeslib.display.get_display_color(self.path) or 0

	@property
	def color_string(self):
		"""
		:return: Control color string
		:rtype: str
		"""
		return colorlib.get_color_name_from_index(self.color)

	def set_color(self, color, shape_only=False):
		"""

		:param color:
		:param shape_only:
		:return:
		"""
		if not isinstance(color, int):
			color = colorlib.get_color_index_from_name(color)

		nodeslib.display.set_display_color(self.path, color, shapes_only=shape_only)

		for offset_control in self.offset_controls:
			offset_control.set_color(color)

	# ------------------------------------------------------------------------

	@property
	def shape(self):
		"""
		:return: Control shape name
		:rtype: str
		"""
		return cmds.getAttr("{}.{}".format(self.path, TAG_SHAPE))

	@property
	def shapes(self):
		"""
		:return: Control shape nodes
		:rtype: list
		"""
		return cmds.listRelatives(self.path, shapes=True, fullPath=True) or []

	def set_shape_axis(self, axis):
		"""
		:param str axis:
		:raise ValueError: When provided axis has no associated rotation.
		"""
		axis_mapper = {"x": [0, 0, -90], "z": [90, 0, 0], "y": [0, 0, 0]}
		axis_rotation = axis_mapper.get(axis)

		if not axis_rotation:
			error_message = "Axis '{}' has not rotation associated.".format(axis)
			log.error(error_message)
			raise ValueError(error_message)

		shapes = selectionlib.filter_by_type(self.shapes, "nurbsCurve")

		for shape in shapes:
			shape = utilslib.conversion.as_list("{0}.cv[*]".format(shape))
			arguments = axis_rotation + shape

			cmds.rotate(
				*arguments,
				relative=True,
				rotateXYZ=True
			)

		for offset_control in self.offset_controls:
			offset_control.set_shape_axis(axis)

	def set_shape_mirror(self, axis):
		"""
		:param str axis:
		"""
		scale = [-1 if a == axis else 1 for a in ["x", "y", "z"]]
		shapes = selectionlib.filter_by_type(self.shapes, "nurbsCurve")

		for shape in shapes:
			arguments = scale[:]
			arguments.append("{}.cv[*]".format(shape))

			cmds.scale(
				*arguments,
				relative=True,
				scaleXYZ=True
			)
		for offset_control in self.offset_controls:
			offset_control.set_shape_mirror(axis)

	def set_shape_scale(self, scale):
		"""
		:param int/float scale:
		"""
		shapes = selectionlib.filter_by_type(self.shapes, "nurbsCurve")

		for shape in shapes:
			cmds.scale(
				scale, scale, scale,
				"{0}.cv[*]".format(shape),
				relative=True,
				scaleXYZ=True
			)

		for i, offset_control in enumerate(self.offset_controls):
			offset_control.set_shape_scale(scale)

	def set_shape(self, shape):
		"""
		:param str shape:
		"""
		shape_data = library.get_control_shape(shape)
		self.set_shape_data(shape_data.get("shape"))
		attributeslib.tag.add_tag_attribute(self.path, TAG_SHAPE, shape)

		for i, offset_control in enumerate(self.offset_controls):
			offset_control.set_shape(shape)
			offset_control.set_shape_scale(1.0 - (0.1 * (i + 1)))

	@decoratorslib.preserve_selection
	def set_shape_data(self, control_shape_data, world_space=False):
		"""
		Set the control shapes using the control_shape_data. Original shapes
		will be removed but visibility connections and color will be restored
		on the new shapes.

		:param list control_shape_data:
		:param bool world_space: set shape dataexporter in world space.
		"""
		# get original color + visibility connection connections
		color_index = self.color
		visibility_connection = cmds.listConnections(
			"{}.visibility".format(self.shapes[0]),
			plugs=True,
			source=True,
			destination=False,
		) if self.shapes else None

		# parent shapes
		temp_curves = [geometrylib.curve.create_curve(**shape) for shape in control_shape_data]
		if world_space:
			cmds.parent(temp_curves, self.path)
			cmds.makeIdentity(temp_curves, apply=1, t=1, r=1, s=1, n=0, pn=1)
			cmds.xform(temp_curves, piv=[0, 0, 0])
			cmds.parent(temp_curves, w=1)

		nodeslib.shape.parent_shapes(temp_curves, self.path, remove_source_shapes=True, remove_target_shapes=True)

		# set color
		if color_index is not None:
			self.set_color(color_index)

		# connect visibilities
		if visibility_connection is not None:
			node, attribute_name = visibility_connection[0].split(".")
			nodeslib.display.create_visibility_link(node, node, attribute_name, shapes_only=True)

		# set historically interesting
		for shape in self.shapes:
			cmds.setAttr("{}.isHistoricallyInteresting".format(shape), 0)

	# ------------------------------------------------------------------------

	@classmethod
	def create(cls,
	           name,
	           generate_new_index=False,
	           num_groups=2,
	           num_offset_controls=0,
	           node_type="transform"):
		"""
		Create a control node with the provided side name and index. It is
		possible to generate a new index when working with a look or are
		unsure which other controls have been created. The number of offsets
		can also be determined in the created function and it defaults to one.

		By default the control shape is a simple locator. This locator can be
		switched out using proper control curves, once the class is
		initialized.

		:param name:
		:param generate_new_index:
		:param num_groups:
		:param num_offset_controls:
		:param node_type:
		:return:
		"""
		name = naminglib.strip_suffix(name)
		ctrl_name = naminglib.format_name(name, node_type=cls.CONTROL_TYPE, generate_new_index=generate_new_index)

		if not ctrl_name or cmds.objExists(ctrl_name):
			error_message = "Control path '{}' already exists.".format(ctrl_name)
			log.error(error_message)
			raise ValueError(error_message)

		path = cmds.createNode(node_type, n=ctrl_name)
		cmds.setAttr("{}.rotateOrder".format(path), keyable=False, lock=False, cb=True)

		transformslib.hierarchy.null_grp_multi(node=path, num=num_groups)

		offset_ctrls = transformslib.hierarchy.null_grp_multi(name=path,
		                                                      parent=path,
		                                                      num=num_offset_controls,
		                                                      node_type=cls.CONTROL_TYPE,
		                                                      reverse_order=True)

		if node_type == "joint":
			cmds.setAttr(path + ".drawStyle", 2)
			cmds.setAttr(path + ".radius", lock=True, keyable=False, cb=False)

		# initialize control
		control = cls(path)
		attributeslib.tag.add_tag_attribute(path, TAG)
		attributeslib.tag.add_tag_attribute(path, TAG_GROUPS, num_groups)
		attributeslib.tag.add_tag_attribute(path, TAG_OFFSET_CONTROLS, num_offset_controls)
		control.set_shape("locator")

		for i, offset_ctrl in enumerate(offset_ctrls):
			offset_control = cls(offset_ctrl)
			cmds.setAttr(offset_ctrl + ".v", lock=True, keyable=False)
			attributeslib.tag.add_tag_attribute(offset_ctrl, TAG)
			attributeslib.tag.add_tag_attribute(offset_ctrl, TAG_OFFSET_CONTROL)
			attributeslib.tag.add_tag_attribute(offset_ctrl, TAG_GROUPS, num_groups + i + 1)

			offset_control.set_shape("locator")
			cmds.xform(["{}.cv[*]".format(s) for s in offset_control.shapes], r=1, s=[1.0 - (0.1 * (i + 1))] * 3)

		return control


def create_control(
		name,
		generate_new_index=False,
		num_groups=1,
		num_offset_controls=0,
		node_type="transform",
		shape=None,
		color=None,
		translate=None,
		rotate=None,
		axis="y",
		scale=1,
		animatable_pivot=False,
		control_type="animControl"
):
	"""
	Create a control.

	:param name:
	:param generate_new_index:
	:param num_groups:
	:param num_offset_controls:
	:param node_type:
	:param shape:
	:param color:
	:param translate:
	:param rotate:
	:param axis:
	:param scale:
	:param animatable_pivot:
	:param control_type:
	:return:
	"""
	obj = Control
	obj.CONTROL_TYPE = control_type

	control = obj.create(name,
	                     generate_new_index=generate_new_index,
	                     num_groups=num_groups,
	                     num_offset_controls=num_offset_controls,
	                     node_type=node_type)

	if shape == "selection_handle":
		cmds.xform([s + ".cv[*]" for s in selectionlib.get_shapes(control.path)], s=[0, 0, 0])
		cmds.setAttr(control.path + ".displayHandle", 1)

	elif shape:
		control.set_shape(shape)

	if scale != 1:
		control.set_shape_scale(scale)

	if axis != "y":
		control.set_shape_axis(axis)

	if color:
		if shape == "selection_handle":
			control.set_color(color, shape_only=False)
		else:
			control.set_color(color)

	if translate:
		node = control.groups[-1] if control.groups else control.path
		transformslib.xform.match(translate, node, pivot=True, rotate=False)

	if rotate:
		node = control.groups[-1] if control.groups else control.path
		transformslib.xform.match(rotate, node, translate=False, rotate=True)

	if animatable_pivot:
		create_animatable_pivot(control)

	return control


def create_animatable_pivot(control):
	"""

	:param control:
	:return:
	"""
	# Create pivot node
	control = Control(control)
	pivot_name = naminglib.append_to_name(control.path, "pivot")

	color = colorlib.get_color_name_from_index(control.color)
	pivot = create_control(name=pivot_name,
	                       color=color,
	                       shape="selection_handle",
	                       num_groups=0,
	                       num_offset_controls=0)

	cmds.setAttr(pivot.path + ".ro", cmds.getAttr(control.path + ".ro"))
	cmds.parent(pivot.path, control.path)
	cmds.xform(pivot.path, a=1, t=[0, 0, 0], ro=[0, 0, 0])

	nodeslib.display.create_visibility_link(control.path, pivot.path, attribute_name="animatablePivotVis")

	if cmds.nodeType(control) == "joint":
		par_grp = cmds.createNode("transform", p=control.groups[-1], n=pivot_name + "_GRP")
		neg_par_grp = cmds.createNode("transform", p=control.groups[-1], n=pivot_name + "_neg_GRP")
		neg_grp = cmds.createNode("transform", p=neg_par_grp, n=pivot_name + "_neg")
		neg_off_grp = cmds.createNode("transform", p=neg_grp, n=pivot_name + "_neg_offset_GRP")
		transformslib.xform.match(control.path, neg_off_grp)

		children = selectionlib.get_children(control.path)

		cmds.parent(control.groups[-2], par_grp)
		cmds.parent(neg_par_grp, control)
		cmds.parent(children, neg_off_grp)

		cmds.connectAttr(pivot.path + ".t", par_grp + ".t")
		attributeslib.connection.negative_connection(pivot.path + ".tx", neg_grp + ".tx")
		attributeslib.connection.negative_connection(pivot.path + ".ty", neg_grp + ".ty")
		attributeslib.connection.negative_connection(pivot.path + ".tz", neg_grp + ".tz")

		num_groups = cmds.getAttr("{}.{}".format(control.path, TAG_GROUPS)) + 1
		num_offset_controls = cmds.getAttr("{}.{}".format(control.path, TAG_OFFSET_CONTROLS)) + 3

		attributeslib.tag.add_tag_attribute(control.path, TAG_GROUPS, num_groups)
		attributeslib.tag.add_tag_attribute(control.path, TAG_OFFSET_CONTROLS, num_offset_controls)

		for node in [neg_grp, neg_par_grp, neg_off_grp]:
			attributeslib.tag.add_tag_attribute(node, TAG)
			attributeslib.tag.add_tag_attribute(node, TAG_OFFSET_CONTROL)

		attributeslib.set_attributes([par_grp, neg_par_grp, neg_off_grp, neg_grp],
		                             ["t", "r", "s", "v", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

	else:
		cmds.connectAttr(pivot.path + ".t", control.path + ".rotatePivot")
		cmds.connectAttr(pivot.path + ".t", control.path + ".scalePivot")

	attributeslib.tag.add_tag_attribute(pivot.path, TAG_PIVOT_CONTROL)
	attributeslib.set_attributes(pivot.path, ["r", "s", "ro", "v"], lock=True, keyable=False)
	return pivot
