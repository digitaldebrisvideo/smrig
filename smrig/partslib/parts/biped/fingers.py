# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import kinematicslib
from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.fingers")


class Fingers(basepart.Basepart):
	"""
	hand rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Fingers, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "", value_required=False)
		self.register_option("parent", "parent_driver", "L_wrist_JNT", value_required=True)
		self.register_option("knuckleParent", "parent_driver", "L_knuckle_JNT", value_required=True)
		self.register_option("numFingers", "int", 4, value_required=True, rebuild_required=True, min=1)
		self.register_option("numFingerJoints", "int", 4, value_required=True, rebuild_required=True, min=1)
		self.register_option("createThumb", "bool", True, rebuild_required=True)
		self.register_option("numThumbJoints", "int", 3, value_required=True, rebuild_required=True, min=1)

		self._part_name_token = "finger"
		self._finger_names = ["thumb", "index", "middle", "ring", "pinky"]
		self.hand_control = None
		self.finger_controls = []

	@property
	def parent(self):
		"""
		:return:
		"""
		return self.options.get("parent").get("value")

	@property
	def knuckle_parent(self):
		"""
		:return:
		"""
		return self.options.get("knuckleParent").get("value")

	@property
	def knuckle_parent_group(self):
		"""

		:return:
		"""
		return self.get_control_group("knuckleParent")

	@property
	def create_thumb(self):
		"""
		:return:
		"""
		return self.options.get("createThumb").get("value")

	@property
	def num_fingers(self):
		"""
		:return:
		"""
		return self.options.get("numFingers").get("value")

	@property
	def num_finger_joints(self):
		"""
		:return:
		"""
		return self.options.get("numFingerJoints").get("value")

	@property
	def num_thumb_joints(self):
		"""
		:return:
		"""
		return self.options.get("numThumbJoints").get("value")

	@property
	def finger_names(self):
		return self._finger_names + ["{}{}".format(self._finger_names[-1], i) for i in range(1, self.num_fingers)]

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		:rtype: None
		"""
		div = (self.num_finger_joints - 1) * 0.5
		colors = [self.primary_color, self.secondary_color] * self.num_fingers

		color_idx = 0
		if self.create_thumb:
			finger_placers = self.build_finger_guides(self.finger_names[0],
			                                          self.num_thumb_joints,
			                                          length=3,
			                                          color=colors[color_idx])

			cmds.xform(finger_placers, r=1, t=[0, 0, div + 1])
			color_idx = 2

		for i in range(1, self.num_fingers + 1):
			finger_placers = self.build_finger_guides(self.finger_names[i],
			                                          self.num_finger_joints,
			                                          color=colors[i + color_idx])

			cmds.xform(finger_placers, r=1, t=[0, 0, -(i - 1) + div])

		self.create_control(self._part_name_token + "s",
		                    shape="cube",
		                    color=self.detail_color,
		                    driver=self.guide_group,
		                    create_offset_controls=False)

	def build_finger_guides(self, finger_name, num_joints, length=4, color=None):
		"""
		Create each finger guide

		:param finger_name:
		:param num_joints:
		:param length:
		:return:
		"""
		placers = self.create_placers([finger_name, self._part_name_token, "fk"], num_placers=num_joints + 1)
		joints = self.create_joint_chain([finger_name, self._part_name_token, "fk"],
		                                 num_joints=num_joints + 1,
		                                 placer_drivers=[p.path for p in placers],
		                                 constraints=["pointConstraint", "aimConstraint"])

		self.create_controls([finger_name, self._part_name_token, "fk"],
		                     num=num_joints,
		                     drivers=joints,
		                     color=color,
		                     axis="x",
		                     shape="circle",
		                     create_offset_controls=False)

		kinematicslib.joint.distribute_chain(placers, [length, 0, 0])
		return placers

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		:rtype: None
		"""
		self.hand_control = self.create_control_from_guide(
			self.format_name(self._part_name_token + "s", node_type="animControl"))
		cmds.parent(self.hand_control.groups[-1], self.get_control_group("parent"))

		cmds.addAttr(self.hand_control.path, ln="smrigHandControl", at="message")
		cmds.addAttr(self.hand_control.path, ln="spread", k=1)
		cmds.addAttr(self.hand_control.path, ln="fist", k=1)
		cmds.addAttr(self.hand_control.path, ln="cup", k=1)
		cmds.addAttr(self.hand_control.path, ln="reverseCup", k=1)

		if self.create_thumb:
			cmds.addAttr(self.hand_control.path, ln="thumbCurl", k=1)

		for i in range(1, self.num_fingers + 1):
			cmds.addAttr(self.hand_control.path, ln="{}Curl".format(self._finger_names[i]), k=1)

		# build each finger
		if self.create_thumb:
			self.build_finger_rig(self._finger_names[0], self.num_thumb_joints, build_knuckle_aim=False)

		# build each finger
		for i in range(1, self.num_fingers + 1):
			self.build_finger_rig(self._finger_names[i], self.num_finger_joints, build_knuckle_aim=True)

		self.set_finger_poses()

		attributeslib.set_attributes(self.hand_control.path,
		                             ["t", "r", "s", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)

	def build_finger_rig(self, finger_name, num_joints, build_knuckle_aim=True):
		"""

		:param finger_name:
		:param num_joints:
		:param build_knuckle_aim:
		:return:
		"""
		joint_names = [self.format_name([finger_name, self._part_name_token, "fk", i + 1], node_type="joint")
		               for i in range(num_joints + 1)]

		control_names = [self.format_name([finger_name, self._part_name_token, "fk", i + 1], node_type="animControl")
		                 for i in range(num_joints)]

		controls = self.create_control_chain_from_guide(control_names, num_groups=3)
		self.finger_controls.append(controls)

		orient_grp = cmds.createNode("transform", n=controls[0].path + "_orient_GRP", p=controls[0])
		cmds.parent(orient_grp, self.get_control_group("parent"))
		cmds.parent(controls[0].groups[-1], orient_grp)

		for control, joint in zip(controls, joint_names[:-1]):
			constraintslib.matrix_constraint(control.path, joint)
			cmds.addAttr(control.groups[-2], ln="smrigFingerPoses", at="message")

			for i, token in enumerate(["spread", "fist", "cup", "reverseCup", finger_name + "Curl"]):
				attributeslib.create_float3_attribute(control.groups[-2], "{}Mult".format(token))

			for axis in ["x", "y", "z"]:
				blw = cmds.createNode("blendWeighted")
				cmds.connectAttr(blw + ".o", "{}.r{}".format(control.groups[-2], axis))

				for i, token in enumerate(["spread", "fist", "cup", "reverseCup", finger_name + "Curl"]):
					attributeslib.connection.multiply_connection("{}.{}".format(self.hand_control, token),
					                                             "{}.{}Mult{}".format(control.groups[-2],
					                                                                  token,
					                                                                  axis.upper()),

					                                             target_plug="{}.input[{}]".format(blw, i))
		if build_knuckle_aim:
			first_ctrl_group = controls[0].groups[-1]
			second_ctrl_group = controls[1].groups[-1]

			first_grp = cmds.duplicate(first_ctrl_group, po=1, n=first_ctrl_group + "_driver_GRP")[0]
			second_grp = cmds.duplicate(second_ctrl_group, po=1, n=second_ctrl_group + "_driver_GRP")[0]
			aim_grp = cmds.duplicate(second_ctrl_group, po=1, n=second_ctrl_group + "_aim_GRP")[0]

			cmds.parent(second_grp, first_grp)
			cmds.parent(aim_grp, self.knuckle_parent_group)

			cmds.aimConstraint(aim_grp,
			                   first_grp,
			                   aim=[1, 0, 0],
			                   u=[0, 1, 0],
			                   wu=[0, 1, 0],
			                   wut="objectRotation",
			                   wuo=orient_grp)

			constraintslib.matrix_constraint(aim_grp, second_grp)
			cmds.connectAttr(first_grp + ".r", first_ctrl_group + ".r")
			cmds.connectAttr(second_grp + ".t", second_ctrl_group + ".t")
			cmds.connectAttr(second_grp + ".r", second_ctrl_group + ".r")

	def set_finger_poses(self):
		"""

		:return:
		"""
		default_curl_value = 8.0

		# thumb
		if self.create_thumb:
			for ctrl in self.finger_controls[0][1:]:
				cmds.setAttr("{}.{}CurlMultZ".format(ctrl.groups[-2], self._finger_names[0]), -default_curl_value)

			for ctrl in self.finger_controls[0][1:]:
				cmds.setAttr("{}.fistMultZ".format(ctrl.groups[-2], self._finger_names[0]), -default_curl_value)

			f_value = -default_curl_value * 0.4
			cmds.setAttr("{}.fistMultX".format(self.finger_controls[0][0].groups[-2], self._finger_names[0]), 2)
			cmds.setAttr("{}.fistMultY".format(self.finger_controls[0][0].groups[-2], self._finger_names[0]), 1)
			cmds.setAttr("{}.fistMultZ".format(self.finger_controls[0][0].groups[-2], self._finger_names[0]), f_value)

		else:
			self.finger_controls.insert(0, [])

		# fist
		for i, ctrls in enumerate(reversed(self.finger_controls[1:])):
			for ctrl in ctrls[1:]:
				cmds.setAttr("{}.fistMultZ".format(ctrl.groups[-2]), -default_curl_value)

		# spread
		div = int(self.num_finger_joints / 2)
		for i, ctrls in enumerate(self.finger_controls[div + 1:], 1):
			value = default_curl_value * i * 0.5 if i == 1 else default_curl_value * i
			cmds.setAttr("{}.spreadMultY".format(ctrls[1].groups[-2]), value)

		for i, ctrls in enumerate(reversed(self.finger_controls[1: div + 1]), 1):
			value = -default_curl_value * i * 0.5 if i == 1 else -default_curl_value * i
			cmds.setAttr("{}.spreadMultY".format(ctrls[1].groups[-2]), value)

		# cup
		div = 1.0 / self.num_finger_joints
		for i, ctrls in enumerate(self.finger_controls[1:]):
			for ctrl in ctrls[1:]:
				cmds.setAttr("{}.cupMultZ".format(ctrl.groups[-2]), -default_curl_value * div * i)

		# reverse cup
		for i, ctrls in enumerate(reversed(self.finger_controls[1:])):
			for ctrl in ctrls[1:]:
				cmds.setAttr("{}.reverseCupMultZ".format(ctrl.groups[-2]), -default_curl_value * div * i)

		# finger curl
		for i, ctrls in enumerate(self.finger_controls[1:]):
			for ctrl in ctrls[1:]:
				cmds.setAttr("{}.{}CurlMultZ".format(ctrl.groups[-2], self._finger_names[i + 1]), -default_curl_value)
