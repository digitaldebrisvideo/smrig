# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import constraintslib
from smrig.lib import kinematicslib
from smrig.lib import spaceslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.fkChain")


class FkChain(basepart.Basepart):
	"""
	fkChain rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(FkChain, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "myChain", value_required=True)
		self.register_option("parent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("numJoints", "int", 3, min=1, value_required=True, rebuild_required=True)
		self.register_option("constraintMethod", "enum", "matrixConstraint", enum="matrixConstraint:aimConstraint")
		self.register_option("createSpaces", "bool", False)

	@property
	def num_joints(self):
		"""

		:return:
		"""
		return self.options.get("numJoints").get("value")

	@property
	def create_spaces(self):
		"""

		:return:
		"""
		return self.options.get("createSpaces").get("value")

	@property
	def constraint_method(self):
		"""
		:return:
		"""
		return self.options.get("constraintMethod").get("value")

	@property
	def parent(self):
		"""
		:return:
		"""
		return self.options.get("parent").get("value")

	@property
	def controls(self):
		"""

		:return:
		"""
		return [self.format_name(["fk", i + 1], node_type="animControl") for i in range(self.num_joints)]

	@property
	def joints(self):
		"""

		:return:
		"""
		return [self.format_name(["fk", i + 1], node_type="joint") for i in range(self.num_joints + 1)]

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		placers = self.create_placers("fk", num_placers=self.num_joints + 1)
		joints = self.create_joint_chain("fk",
		                                 num_joints=self.num_joints + 1,
		                                 placer_drivers=[p.path for p in placers],
		                                 constraints=["pointConstraint", "aimConstraint"])

		self.create_controls("fk",
		                     num=self.num_joints,
		                     drivers=joints,
		                     color=self.primary_color,
		                     axis="x",
		                     shape="circle")

		kinematicslib.joint.distribute_chain(placers, [5, 0, 0])

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		controls = self.create_control_chain_from_guide(self.controls, num_groups=2)

		for control, joint in zip(controls, self.joints[:-1]):
			rotate = True if self.constraint_method == "matrixConstraint" else False
			rotate = True if control == controls[-1] else rotate
			constraintslib.matrix_constraint(control.last_node, joint, rotate=rotate)

		cmds.parent(controls[0].groups[-1], self.get_control_group())

		if self.constraint_method == "aimConstraint":
			constraintslib.aim_constraint_chain([c.last_node for c in controls],
			                                    self.joints[:-1],
			                                    mo=True,
			                                    mirror_value=self.mirror_value)

		if self.create_spaces:
			for i, control in enumerate(controls):
				spc_obj = spaceslib.Space(control.path)

				if i > 0:
					spc_obj.add_target(controls[i - 1].path, "parentControl")
					spc_obj.add_target(self.parent, "parent")
				else:
					spc_obj.add_target(self.parent, "parent")

				spc_obj.set_as_default()
