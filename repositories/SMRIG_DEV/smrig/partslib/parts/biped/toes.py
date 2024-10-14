# -*- smrig: part  -*-
import logging

from smrig.partslib.common import basepart
from smrig.partslib.parts.biped import fingers

log = logging.getLogger("smrig.partslib.fingers")


class Toes(fingers.Fingers, basepart.Basepart):
	"""
	hand rig part module.
	"""

	def __init__(self, *guide_node, **options):
		super(Toes, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "", value_required=False)
		self.register_option("parent", "parent_driver", "L_ankle_JNT", value_required=True)
		self.register_option("ballParent", "parent_driver", "L_ball_JNT", value_required=True)
		self.register_option("numToes", "int", 5, value_required=True, rebuild_required=True, min=1)
		self.register_option("numToeJoints", "int", 4, value_required=True, rebuild_required=True, min=1)
		self.register_option("createToeThumb", "bool", False, rebuild_required=True)
		self.register_option("numToeThumbJoints", "int", 3, value_required=True, rebuild_required=True, min=1)

		# since we're inheriting another part, we need to hide that parts options
		self.register_option("knuckleParent", "parent_driver", "L_knuckle_JNT", editable=False)
		self.register_option("numFingers", "int", 4, min=1, editable=False)
		self.register_option("numFingerJoints", "int", 4, min=1, editable=False)
		self.register_option("createThumb", "bool", True, editable=False)
		self.register_option("numThumbJoints", "int", 3, editable=False)

		self._part_name_token = "toe"
		self._finger_names = ["thumb", "big", "index", "middle", "ring", "pinky"]
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
		return self.options.get("ballParent").get("value")

	@property
	def knuckle_parent_group(self):
		"""

		:return:
		"""
		return self.get_control_group("ballParent")

	@property
	def num_fingers(self):
		"""
		:return:
		"""
		return self.options.get("numToes").get("value")

	@property
	def num_finger_joints(self):
		"""
		:return:
		"""
		return self.options.get("numToeJoints").get("value")

	@property
	def create_thumb(self):
		"""
		:return:
		"""
		return self.options.get("createToeThumb").get("value")

	@property
	def num_thumb_joints(self):
		"""
		:return:
		"""
		return self.options.get("numToeThumbJoints").get("value")
