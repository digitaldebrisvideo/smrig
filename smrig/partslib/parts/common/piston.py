# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import constraintslib
from smrig.lib import transformslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.piston")


class Piston(basepart.Basepart):
	"""
	piston rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Piston, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "C")
		self.register_option("name", "string", "myPiston", value_required=True)
		self.register_option("startParent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("endParent", "parent_driver", "C_root_JNT", value_required=True)
		self.register_option("startPositionRef", "selection", "")
		self.register_option("endPositionRef", "selection", "")

	@property
	def start_parent(self):
		return self.options.get("startParent").get("value")

	@property
	def end_parent(self):
		return self.options.get("endParent").get("value")

	@property
	def start_ref(self):
		return self.find_stashed_nodes("startPositionRef")

	@property
	def end_ref(self):
		return self.find_stashed_nodes("endPositionRef")

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		start_plc = self.create_placer(["start", 1])
		end_plc = self.create_placer(["end", 1])

		start_jnt = self.create_joint(["start", 1], placer_driver=start_plc, constraints="pointConstraint")
		end_jnt = self.create_joint(["end", 1], placer_driver=end_plc, constraints="pointConstraint")

		start_jnt2 = self.create_joint(["start", 2])
		end_jnt2 = self.create_joint(["end", 2])

		cmds.parent(start_jnt2, start_jnt)
		cmds.parent(end_jnt2, end_jnt)

		cmds.pointConstraint(start_jnt, end_jnt, start_jnt2)
		cmds.pointConstraint(start_jnt, end_jnt, end_jnt2)

		cmds.aimConstraint(start_jnt,
		                   end_jnt,
		                   wuo=start_plc,
		                   wut="objectRotation",
		                   aim=[-self.mirror_value, 0, 0],
		                   u=[0, 0, 1],
		                   wu=[0, 0, 1])

		cmds.aimConstraint(end_jnt,
		                   start_jnt,
		                   wuo=start_plc,
		                   wut="objectRotation",
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, 1],
		                   wu=[0, 0, 1])

		cmds.xform(start_plc.path, r=1, t=[0, 1, 0])
		cmds.xform(end_plc.path, r=1, t=[0, -1, 0])

		# This is where you snap stuff
		if self.start_ref and self.end_ref:
			tmp0 = transformslib.xform.match_locator(self.start_ref)
			tmp1 = transformslib.xform.match_locator(self.end_ref)

			cmds.delete(cmds.pointConstraint(tmp0, tmp1, self.guide_group))
			transformslib.xform.match(tmp0, start_plc.path)
			transformslib.xform.match(tmp1, end_plc.path)
			cmds.delete(tmp0, tmp1)

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		start_jnt = self.format_name(["start", 1], node_type="joint")
		end_jnt = self.format_name(["end", 1], node_type="joint")
		start_child_jnt = self.format_name(["start", 2], node_type="joint")
		end_child_jnt = self.format_name(["end", 2], node_type="joint")

		start_grp = cmds.createNode("transform", n=start_jnt + "_GRP", p=start_jnt)
		end_grp = cmds.createNode("transform", n=end_jnt + "_GRP", p=end_jnt)

		cmds.parent(start_grp, self.get_rig_group("startParent"))
		cmds.parent(end_grp, self.get_rig_group("endParent"))

		cmds.select(start_jnt, start_grp)

		# constraint
		constraintslib.matrix_constraint(start_grp, start_jnt, rotate=False)
		constraintslib.matrix_constraint(end_grp, end_jnt, rotate=False)

		cmds.aimConstraint(start_jnt,
		                   end_jnt,
		                   wuo=end_grp,
		                   wut="objectRotation",
		                   aim=[-self.mirror_value, 0, 0],
		                   u=[0, 0, 1],
		                   wu=[0, 0, 1],
		                   mo=True)

		cmds.aimConstraint(end_jnt,
		                   start_jnt,
		                   wuo=start_grp,
		                   wut="objectRotation",
		                   aim=[self.mirror_value, 0, 0],
		                   u=[0, 0, 1],
		                   wu=[0, 0, 1],
		                   mo=True)

		cmds.pointConstraint(start_jnt, end_jnt, start_child_jnt)
		oc = cmds.orientConstraint(start_jnt, end_jnt, start_child_jnt)
		cmds.setAttr(oc[0] + ".interpType", 2)

		constraintslib.matrix_constraint(start_child_jnt, end_child_jnt)
		cmds.hide(end_child_jnt)

	def parent_skeleton(self):
		"""

		:return:
		"""
		start_jnt = self.format_name(["start", 1], node_type="joint")
		end_jnt = self.format_name(["end", 1], node_type="joint")

		try:
			cmds.parent(start_jnt, self.start_parent)
		except:
			pass

		try:
			cmds.parent(end_jnt, self.end_parent)
		except:
			pass
