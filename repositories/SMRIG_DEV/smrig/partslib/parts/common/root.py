# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constantlib
from smrig.lib import constraintslib
from smrig.lib import nodeslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.root")


class Root(basepart.Basepart):
	"""
	root rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Root, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C", editable=False)
		self.register_option("name", "string", "", editable=False)

	@property
	def world_control(self):
		return self.format_name("world", node_type="animControl")

	@property
	def visibility_control(self):
		return self.format_name("visibility", node_type="animControl")

	@property
	def root_joint(self):
		return self.format_name("root", node_type="joint")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		plc = self.create_placer("root")
		root_joint = self.create_joint("root", placer_driver=plc.path)

		self.create_control("world",
		                    driver=root_joint,
		                    shape="global",
		                    color=self.primary_color,
		                    num_offset_controls=1,
		                    scale=3)

		self.create_control("visibility",
		                    driver=root_joint,
		                    shape="letter-v",
		                    color=self.primary_color,
		                    num_offset_controls=0,
		                    create_offset_controls=False)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		world_control = self.create_control_from_guide(self.world_control, num_groups=1, animatable_pivot=True)
		visibility_control = self.create_control_from_guide(self.visibility_control, num_groups=0)

		constraintslib.matrix_constraint(world_control.last_node, visibility_control.path, maintain_offset=True)
		constraintslib.matrix_constraint(world_control.last_node, self.root_joint, maintain_offset=True)

		cmds.parent(world_control.groups[0], self.get_control_group())
		cmds.parent(visibility_control.path, self.part_group)

		for ctrl in [c.path for c in [world_control] + world_control.offset_controls]:
			nodeslib.display.create_uniform_scale_link(ctrl)

		nodeslib.display.create_visibility_link(visibility_control.path,
		                                        [],
		                                        attribute_name="controlsVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(visibility_control.path,
		                                        [],
		                                        attribute_name="offsetControlsVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(visibility_control.path,
		                                        constantlib.MODEL_GROUP,
		                                        attribute_name="modelVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(visibility_control.path,
		                                        constantlib.JOINTS_GROUP,
		                                        attribute_name="jointsVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(visibility_control.path,
		                                        [],
		                                        attribute_name="rigVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		attributeslib.add_spacer_attribute(visibility_control.path, "DisplaySpacer")
		nodeslib.display.create_display_type_link(visibility_control.path,
		                                          constantlib.MODEL_GROUP,
		                                          attribute_name="modelDisplay",
		                                          display_type="normal")

		nodeslib.display.create_display_type_link(visibility_control.path,
		                                          constantlib.JOINTS_GROUP,
		                                          attribute_name="jointDisplay",
		                                          display_type="normal")

		attributeslib.add_spacer_attribute(visibility_control.path, "ResSpacer")
		nodeslib.display.create_resolution_link(visibility_control.path, [], "primary")
		cmds.setAttr(self.root_joint + ".drawStyle", 2)

		attributeslib.set_attributes(visibility_control.path,
		                             ["t", "r", "s", "v", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)
