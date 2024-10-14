# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import constraintslib
from smrig.lib import spaceslib
from smrig.lib import transformslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.boilerplate")


class SingleControl(basepart.Basepart):
	"""
	singleControl rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(SingleControl, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C")
		self.register_option("name", "string", "myControl", value_required=True)
		self.register_option("parent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("animatablePivot", "bool", False)
		self.register_option("createSpaces", "bool", False)
		self.register_option("createControl", "bool", True)
		self.register_option("createJoint", "bool", True)
		self.register_option("positionRef", "selection", "")

	@property
	def position_ref(self):
		return self.find_stashed_nodes("positionRef")

	@property
	def control(self):
		"""

		:return:
		"""
		return self.format_name("", node_type="animControl")

	@property
	def joint(self):
		"""

		:return:
		"""
		return self.format_name("", node_type="joint")

	@property
	def create_anim_control(self):
		"""

		:return:
		"""
		return self.options.get("createControl").get("value")

	@property
	def create_bind_joint(self):
		"""

		:return:
		"""
		return self.options.get("createJoint").get("value")

	@property
	def create_animatable_pivot(self):
		"""

		:return:
		"""
		return self.options.get("animatablePivot").get("value")

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

		placer = self.create_placer("")

		if self.create_anim_control:
			self.create_control("", driver=placer.path, shape="cube", color=self.primary_color)

		if self.create_bind_joint:
			self.create_joint("", placer_driver=placer.path)

		if self.position_ref:
			tmp0 = transformslib.xform.match_locator(self.position_ref)
			transformslib.xform.match(tmp0, self.guide_group)
			cmds.delete(tmp0)

	def build_rig(self):
		"""

		:return:
		"""
		if self.create_anim_control:
			control = self.create_control_from_guide(self.control,
			                                         num_groups=2,
			                                         animatable_pivot=self.create_animatable_pivot)

			cmds.parent(control.groups[-1], self.get_control_group())

			if self.create_spaces:
				spc_obj = spaceslib.Space(control.path)
				spc_obj.add_target(self.parent, "parent")
				spc_obj.set_as_default()

			if self.create_bind_joint:
				constraintslib.matrix_constraint(control.last_node, self.joint, maintain_offset=True)
