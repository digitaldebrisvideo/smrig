import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.lib.constantlib import VISIBILITY_CONTROL


class RigMixin(object):
	"""
	This is a mixin for adding rig build functionality to a part module.
	"""
	side = ""
	name = ""
	error_message = "This is a mixin that should not be run on its own. Use basepart.py instead."

	def __init__(self):
		pass

	def format_name(self, *args, **kwargs):
		"""
		Placeholder for function in basepart.

		:param args:
		:param kwargs:
		:return:
		"""
		raise RuntimeError(self.error_message)

	def create_node(self, *args, **kwargs):
		"""
		Placeholder for function in basepart.

		:param args:
		:param kwargs:
		:return:
		"""
		raise RuntimeError(self.error_message)

	def get_guide_node(self, node):
		"""
		Prepend stash namespaace to given node.

		:param node:
		:return: Namespaced node name
		:rtype: str
		"""
		return node if node.startswith(utilslib.scene.STASH_NAMESPACE + ":") \
			else "{}:{}".format(utilslib.scene.STASH_NAMESPACE, node)

	def create_control_from_guide(self,
	                              name,
	                              translate=True,
	                              rotate=True,
	                              scale=False,
	                              num_groups=3,
	                              animatable_pivot=False,
	                              node_type="transform",
	                              center_pivot_on_control=False,
	                              ref_ctrl=None):
		"""
		:param name:
		:param translate:
		:param rotate:
		:param scale:
		:param num_groups:
		:param animatable_pivot:
		:param center_pivot_on_control:
		:return:
		"""
		stashed_guide_control_name = self.get_guide_node(ref_ctrl if ref_ctrl else name)
		stashed_guide_control = controlslib.Control(stashed_guide_control_name)

		num_offset_controls = cmds.getAttr("{}.numOffsetControls".format(stashed_guide_control.path)) \
			if cmds.objExists("{}.numOffsetControls".format(stashed_guide_control.path)) else 0

		if center_pivot_on_control:
			translate = stashed_guide_control_name

		elif translate is True:
			translate = stashed_guide_control.groups[0]

		elif cmds.objExists(translate):
			pass

		else:
			translate = None

		if rotate is True:
			rotate = stashed_guide_control.groups[0]

		elif cmds.objExists(rotate):
			pass

		else:
			rotate = None

		control = controlslib.create_control(
			name,
			shape=stashed_guide_control.shape,
			color=stashed_guide_control.color,
			generate_new_index=False,
			num_groups=num_groups,
			node_type=node_type,
			translate=translate,
			rotate=rotate,
			num_offset_controls=num_offset_controls,
			animatable_pivot=animatable_pivot
		)

		if scale and cmds.objExists(str(scale)):
			transformslib.xform.match(stashed_guide_control.groups[0],
			                          scale,
			                          translate=False,
			                          rotate=False,
			                          scale=True)

		elif scale and control.groups:
			transformslib.xform.match(stashed_guide_control.groups[0],
			                          control.groups[-1],
			                          translate=False,
			                          rotate=False,
			                          scale=True)
		elif control.groups:
			scale_values = [-1 if s < 0 else 1 for s in cmds.getAttr(stashed_guide_control.groups[0] + ".s")[0]]
			cmds.setAttr(control.groups[-1] + ".s", *scale_values)

		rotate_order = cmds.getAttr("{}.rotateOrder".format(stashed_guide_control.path))
		curve_data = geometrylib.curve.extract_curve_creation_data(stashed_guide_control.path, world_space=True)
		control.set_shape_data(curve_data, world_space=True)
		cmds.setAttr("{}.rotateOrder".format(control.path), rotate_order)
		attributeslib.set_attributes(control.path, ["v"], lock=True, keyable=False)

		attributeslib.set_attributes(control.path, ["rotateOrder"], lock=False, keyable=False, channel_box=True)

		for i in range(num_offset_controls):
			stashed_offset_ctrl = stashed_guide_control.offset_controls[i]
			curve_data = geometrylib.curve.extract_curve_creation_data(stashed_offset_ctrl.path, world_space=True)
			control.offset_controls[i].set_shape_data(curve_data, world_space=True)
			cmds.setAttr("{}.rotateOrder".format(control.offset_controls[i].path), rotate_order)
			attributeslib.set_attributes(control.offset_controls[i].path, ["rotateOrder"],
			                             lock=False,
			                             keyable=False,
			                             channel_box=True)

			shapes = selectionlib.get_shapes(control.offset_controls[i].path)
			if shapes and cmds.objExists(VISIBILITY_CONTROL):
				for shape in shapes:
					cmds.connectAttr(VISIBILITY_CONTROL + ".offsetControlsVisibility", shape + ".v", f=True)

		return control

	def create_controls_from_guide(self,
	                               names,
	                               translate=True,
	                               rotate=True,
	                               scale=False,
	                               num_groups=3,
	                               animatable_pivot=False):
		"""
		:param names:
		:param translate:
		:param rotate:
		:param scale:
		:param num_groups:
		:param animatable_pivot:
		:return:
		"""
		controls = []
		for name in names:
			controls.append(
				self.create_control_from_guide(name, translate, rotate, scale, num_groups, animatable_pivot))

		return controls

	def create_control_chain_from_guide(self,
	                                    names,
	                                    translate=True,
	                                    rotate=True,
	                                    scale=False,
	                                    num_groups=3,
	                                    animatable_pivot=False):
		"""
		:param names:
		:param translate:
		:param rotate:
		:param scale:
		:param num_groups:
		:param animatable_pivot:
		:return:
		"""
		controls = []
		for name in names:
			controls.append(
				self.create_control_from_guide(name, translate, rotate, scale, num_groups, animatable_pivot))

		for i, control in enumerate(controls[1:], 1):
			cmds.parent(control.groups[-1] if control.groups else control.path, controls[i - 1].path)

		return controls
