# -*- smrig: part  -*-
import logging

from maya import cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.shoulder")


class Shoulder(basepart.Basepart):
	"""
	shoulder rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Shoulder, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_chest_JNT", value_required=True)
		self.register_option("createScapula", "bool", True, rebuild_required=True)
		self.register_option("createPectoral", "bool", True, rebuild_required=True)
		self.register_option("createTrapezius", "bool", True, rebuild_required=True)
		self.register_option("createLats", "bool", True, rebuild_required=True)

	@property
	def control(self):
		return self.format_name("shoulder", node_type="animControl")

	@property
	def joint(self):
		return self.format_name("shoulder", node_type="joint")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:return:
		"""

		shd_plc = self.create_placer("shoulder")
		shd_jnt = self.create_joint("shoulder", placer_driver=shd_plc)

		self.create_control("shoulder",
		                    color=self.primary_color,
		                    shape="semi-circle",
		                    driver=shd_jnt,
		                    rotate_cvs=[0, -90 * self.mirror_value, 0])

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		control = self.create_control_from_guide(self.control, num_groups=2)
		constraintslib.matrix_constraint(control.last_node, self.joint, maintain_offset=True)
		cmds.parent(control.groups[-1], self.get_control_group())
		attributeslib.set_attributes(control.all_controls, "s", lock=True, keyable=True)
