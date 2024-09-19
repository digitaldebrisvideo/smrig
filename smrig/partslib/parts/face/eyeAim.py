# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import nodeslib
from smrig.lib import spaceslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.eyeAim")


class EyeAim(basepart.Basepart):
	"""
	eyeAim rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(EyeAim, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C")
		self.register_option("name", "string", "", value_required=False)
		self.register_option("parent", "parent_driver", "C_head_JNT", value_required=True)
		self.register_option("createSpaces", "bool", True)
		self.register_option("controlPositionRef", "selection", "['L_eye_aim_CTL']")

	@property
	def control_pos_ref(self):
		return self.find_stashed_nodes("controlPositionRef")

	@property
	def control(self):
		"""

		:return:
		"""
		return self.format_name("eyeAim", node_type="animControl")

	@property
	def create_spaces(self):
		"""

		:return:
		"""
		return self.options.get("createSpaces").get("value")

	@property
	def parent(self):
		"""

		:return:
		"""
		return self.options.get("parent").get("value")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:return:
		"""

		placer = self.create_placer("eyeAim")
		self.create_control("eyeAim", driver=placer.path, shape="jack", color=self.primary_color)

		if self.control_pos_ref:
			cmds.delete(cmds.pointConstraint(self.control_pos_ref, placer.path))
			cmds.setAttr(placer.path + ".tx", 0)

	def build_rig(self):
		"""

		:return:
		"""
		control = self.create_control_from_guide(self.control, num_groups=2, center_pivot_on_control=True)
		cmds.parent(control.groups[-1], self.get_control_group())

		for ctrl in control.all_controls:
			nodeslib.display.create_uniform_scale_link(ctrl)

		if self.create_spaces:
			spc_obj = spaceslib.Space(control.path)
			spc_obj.add_target(self.parent, "parent")
			spc_obj.set_as_default()

		attributeslib.set_attributes(control.all_controls, ["r", "ro"], lock=True, keyable=False, channel_box=False)
