# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib.utilslib import scene
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.bendHelpers")


class BendHelpers(basepart.Basepart):
	"""
	bendHelpers rig part module.
	"""

	BUILD_LAST = True

	def __init__(self, *guide_node, **options):
		super(BendHelpers, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "wrist")
		self.register_option("parent", "parent_driver", "L_wrist_JNT", value_required=True)
		self.register_option("aimAxis", "enum", "Y", enum="X:Y:Z", rebuild_required=True)
		self.register_option("rotateAxis", "enum", "Z", enum="X:Y:Z", rebuild_required=True)

	@property
	def aim_axis(self):
		return self.options.get("aimAxis").get("value").lower()

	@property
	def rot_axis(self):
		return self.options.get("aimAxis").get("value").lower()

	@property
	def parent_node(self):
		return self.options.get("parent").get("value")

	@property
	def pos_ref(self):
		"""

		:return:
		"""
		node = cmds.ls(scene.find_stashed_nodes(self.parent_node or ""))
		return node[0] if node else None

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		base_plc = self.create_placer(["helper", "base"])
		fr_plc = self.create_placer(["helper", "front"])
		bk_plc = self.create_placer(["helper", "back"])

		base_jnt = self.create_joint(["helper", "base"], placer_driver=base_plc)
		fr_jnt = self.create_joint(["helper", "front"], placer_driver=fr_plc)
		bk_jnt = self.create_joint(["helper", "back"], placer_driver=bk_plc)

		cmds.parent(fr_jnt, bk_jnt, base_jnt)

		if self.aim_axis == "z":
			trans = [0, 0, 1]
		elif self.aim_axis == "y":
			trans = [0, 1, 0]
		else:
			trans = [1, 0, 0]

		cmds.xform(fr_plc, a=True, t=trans)
		cmds.xform(bk_plc, a=True, t=[-x for x in trans])

		attributeslib.set_attributes(base_plc.all_controls + fr_plc.all_controls + bk_plc.all_controls,
		                             ["t", "r", "s"],
		                             lock=True,
		                             keyable=False)
		if self.pos_ref:
			cmds.delete(cmds.parentConstraint(self.pos_ref, self.guide_group))

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		base_jnt = self.format_name(["helper", "base"], node_type="joint")
		fr_jnt = self.format_name(["helper", "front"], node_type="joint")
		bk_jnt = self.format_name(["helper", "back"], node_type="joint")
		par = self.parent_node

		# base jnt mult ---------------------------------

		cmds.setAttr(base_jnt + ".ro", cmds.getAttr(par + ".ro"))
		attributeslib.connection.multiply_connection(par + ".rx", multiply_value=-0.5, target_plug=base_jnt + ".rx")
		attributeslib.connection.multiply_connection(par + ".ry", multiply_value=-0.5, target_plug=base_jnt + ".ry")
		attributeslib.connection.multiply_connection(par + ".rz", multiply_value=-0.5, target_plug=base_jnt + ".rz")

		# expand jnts ---------------------------------

		sr = cmds.createNode("setRange")
		dst = cmds.getAttr("{}.t{}".format(fr_jnt, self.aim_axis))

		cmds.connectAttr("{}.r{}".format(par, self.rot_axis), sr + ".valueX")
		cmds.setAttr(sr + ".oldMaxX", 90)

		cmds.setAttr(sr + ".minX", dst)
		cmds.setAttr(sr + ".maxX", 100 * dst)

		cmds.connectAttr(sr + ".outValueX", "{}.t{}".format(fr_jnt, self.aim_axis))
		attributeslib.connection.multiply_connection("{}.t{}".format(fr_jnt, self.aim_axis),
		                                             multiply_value=-1,
		                                             target_plug="{}.t{}".format(bk_jnt, self.aim_axis))
