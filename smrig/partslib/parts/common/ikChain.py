# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import kinematicslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.ikChain")


class IkChain(basepart.Basepart):
	"""
	ikChainScSolver rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(IkChain, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "myChain", value_required=True)
		self.register_option("parent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("ikHandleparent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("numJoints", "int", 2, min=1, value_required=True, rebuild_required=True)
		self.register_option("solver", "enum", "SC", enum="SC:RP", value_required=True)

	@property
	def num_joints(self):
		"""

		:return:
		"""
		return self.options.get("numJoints").get("value")

	@property
	def parent(self):
		"""
		:return:
		"""
		return self.options.get("parent").get("value")

	@property
	def ik_handle_parent(self):
		"""
		:return:
		"""
		return self.options.get("ikHandleparent").get("value")

	@property
	def joints(self):
		"""

		:return:
		"""
		return [self.format_name(["ik", i + 1], node_type="joint") for i in range(self.num_joints + 1)]

	@property
	def solver(self):
		return self.options.get("solver").get("value")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		placers = self.create_placers("ik", num_placers=self.num_joints + 1)
		self.create_joint_chain("ik",
		                        num_joints=self.num_joints + 1,
		                        placer_drivers=[p.path for p in placers],
		                        constraints=["pointConstraint", "aimConstraint"])

		kinematicslib.joint.distribute_chain(placers, [5, 0, 0])

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		ik = kinematicslib.ik.create_ik_handle(self.joints[0], self.joints[-1], self.solver)
		cmds.parent(ik, self.get_rig_group("ikHandleparent"))

		node = cmds.createNode("transform", p=self.get_rig_group("ikHandleparent"), n=ik + "_GRP")
		cmds.pointConstraint(node, ik, mo=1)
