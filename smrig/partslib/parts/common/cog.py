# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import constraintslib
from smrig.lib import nodeslib
from smrig.lib import spaceslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.cog")


class Cog(basepart.Basepart):
	"""
	root rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Cog, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_root_JNT", value_required=True)

	@property
	def cog_control(self):
		return self.format_name("cog", node_type="animControl")

	@property
	def cog_joint(self):
		return self.format_name("cog", node_type="joint")

	@property
	def parent(self):
		return self.options.get("parent").get("value")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		plc = self.create_placer("cog")
		cog_joint = self.create_joint("cog", placer_driver=plc.path)

		self.create_control("cog",
		                    driver=cog_joint,
		                    shape="cog",
		                    color=self.primary_color,
		                    num_offset_controls=1,
		                    scale=3)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		cog_control = self.create_control_from_guide(self.cog_control, num_groups=2, animatable_pivot=True)
		constraintslib.matrix_constraint(cog_control.last_node, self.cog_joint, maintain_offset=True)
		cmds.parent(cog_control.groups[-1], self.get_control_group())

		for ctrl in cog_control.all_controls:
			nodeslib.display.create_uniform_scale_link(ctrl)

		spc_obj = spaceslib.Space(cog_control.path)
		spc_obj.add_target(self.parent, "parent")
		spc_obj.add_target("C_root_JNT", "world")
		spc_obj.add_target(self.noxform_group, "trueWorld")
		spc_obj.set_options(create_root_spaces=False)
		spc_obj.set_as_default()
