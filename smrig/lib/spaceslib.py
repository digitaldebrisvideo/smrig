import logging

import maya.cmds as cmds
from six import string_types

from smrig.lib import constraintslib
from smrig.lib import controlslib

log = logging.getLogger("smrig.lib.spaceslib")

SPACE_TAG = "smrigSpaces"
SPACE_ATTRIBUTE = "space"

ROOT_TARGETS = ["C_cog_JNT", "C_root_JNT", "noxform_GRP"]
ROOT_TARGET_NAMES = ["cog", "world", "trueWorld"]


class Space(object):

	def __init__(self, control):
		"""

		:param control:
		"""
		self.control = control

		self._data = {
			"destination": None,
			"targets": [],
			"target_names": [],
			"translate": True,
			"rotate": True,
			"scale": False,
			"default_value": 0,
			"weighted": False,
			"split": True,
			"create_root_spaces": True
		}

		self.set_data_from_node()

	def set_data(self, data):
		"""
		Set data fed in as dict.
		:param data:
		:return:
		"""
		self._data = data
		self.save_data_to_node()

	def set_data_from_node(self):
		"""
		Get spaces data from node

		:return:
		"""
		if cmds.objExists("{}.{}".format(self.control, SPACE_TAG)):
			data = eval(cmds.getAttr("{}.{}".format(self.control, SPACE_TAG)))
			self._data = data if data else self._data

	def save_data_to_node(self):
		"""
		set spaces data to node

		:return:
		"""
		if not cmds.objExists("{}.{}".format(self.control, SPACE_TAG)):
			cmds.addAttr(self.control, ln=SPACE_TAG, dt="string")

		cmds.setAttr("{}.{}".format(self.control, SPACE_TAG), lock=False)
		cmds.setAttr("{}.{}".format(self.control, SPACE_TAG), self._data, type="string")

	def add_target(self, target, target_name=None):
		"""
		:param target:
		:param target_name:
		:return:
		"""
		target_name = target_name if target_name else target.split("|")[-1]
		self._data["targets"].append(target)
		self._data["target_names"].append(target_name)
		self.save_data_to_node()

	def insert_target(self, idx, target, target_name=None):
		"""
		:param idx:
		:param target:
		:param target_name:
		:return:
		"""
		target_name = target_name if target_name else target.split("|")[-1]
		self._data["targets"].insert(idx, target)
		self._data["target_names"].insert(idx, target_name)
		self.save_data_to_node()

	def remove_target(self, target_name):
		"""
		:param target_name:
		:return:
		"""
		idx = self._data.get("target_names").index(target_name)
		self._data["targets"].remove(self._data.get("targets")[idx])
		self._data["target_names"].remove(target_name)
		self.save_data_to_node()

	def set_destination(self, destination):
		"""
		:param destination:
		:return:
		"""
		self._data["destination"] = destination
		self.save_data_to_node()

	def set_options(self, translate=True,
	                rotate=True,
	                scale=False,
	                split=True,
	                default_value=0,
	                weighted=False,
	                create_root_spaces=True):
		"""
		:param translate:
		:param rotate:
		:param scale:
		:param split:
		:param default_value:
		:param weighted:
		:param create_root_spaces:
		:return:
		"""
		self._data["translate"] = translate
		self._data["rotate"] = rotate
		self._data["scale"] = scale
		self._data["split"] = split
		self._data["default_value"] = default_value
		self._data["weighted"] = weighted
		self._data["create_root_spaces"] = create_root_spaces
		self.save_data_to_node()

	def set_as_default(self, state=True):
		"""
		Lock the attribute to indicate it is a default settings

		:param state:
		:return:
		"""
		cmds.setAttr("{}.{}".format(self.control, SPACE_TAG), lock=state)

	def build_space(self):
		"""

		:return:
		"""
		targets = self._data.get("targets")
		target_names = self._data.get("target_names")
		destination = self._data.get("destination")
		translate = self._data.get("translate")
		rotate = self._data.get("rotate")
		scale = self._data.get("scale")

		split = self._data.get("split")
		weighted = self._data.get("weighted")
		default_value = self._data.get("default_value")

		if self._data.get("create_root_spaces"):
			root_targets, root_names = get_root_spaces()
			targets.extend(root_targets)
			target_names.extend(root_names)

		if not destination:
			ct_obj = controlslib.Control(self.control)
			destination = ct_obj.groups[-1]

		missing = [n for n in [self.control, destination] + targets if not cmds.objExists(n)]
		if missing:
			log.warning("Cannot create space for: {}\nMissing Nodes:{}".format(self.control, "\t\n{}".join(missing)))
			return

		create_space_swtich(targets,
		                    target_names,
		                    destination,
		                    self.control,
		                    translate=translate,
		                    rotate=rotate,
		                    scale=scale,
		                    split=split,
		                    default_value=default_value,
		                    weighted=weighted)


# ----------------------------------------------------------------------------------------------------


def get_root_spaces():
	"""
	:return:
	"""
	targets = []
	target_names = []
	for target, target_name in zip(ROOT_TARGETS, ROOT_TARGET_NAMES):
		if cmds.objExists(target):
			targets.append(target)
			target_names.append(target_name)

	return targets, target_names


def get_all_space_objects():
	"""
	Get all space nodes as space objects

	:return:
	"""
	return [Space(n.split(".")[0]) for n in cmds.ls("*." + SPACE_TAG)]


def build_all_spaces():
	"""
	Build all spaces in scene
	:return:
	"""
	for obj in get_all_space_objects():
		obj.build_space()


# ----------------------------------------------------------------------------------------------------


def create_space_swtich(targets,
                        target_names,
                        destination,
                        control,
                        translate=True,
                        rotate=True,
                        scale=False,
                        split=True,
                        default_value=0,
                        weighted=False):
	"""
	Create space switch on control using matrix_constrain_multi.

	:param targets:
	:param target_names:
	:param destination:
	:param control:
	:param translate:
	:param rotate:
	:param scale:
	:param split:
	:param default_value:
	:param weighted:
	:return:
	"""
	if isinstance(default_value, string_types):
		if default_value in target_names:
			default_value = target_names.index(default_value)
		else:
			default_value = 0

	result = constraintslib.matrix_constraint_multi(targets,
	                                                destination,
	                                                translate=translate,
	                                                rotate=rotate,
	                                                scale=scale,
	                                                weighted=weighted,
	                                                split=split)
	if split:
		translate_choice, rotate_choice = result
	else:
		translate_choice, rotate_choice = result, None

	# create attributes
	if weighted:
		if split:
			if translate:
				for i, attr_nane in enumerate(["{}TranslationSpace".format(n) for n in target_names]):
					dv = 1 if i == default_value else 0
					cmds.addAttr(control, ln=attr_nane, min=0, max=1, dv=dv, k=True)

			if rotate:
				for i, attr_nane in enumerate(["{}RotationSpace".format(n) for n in target_names]):
					dv = 1 if i == default_value else 0
					cmds.addAttr(control, ln=attr_nane, min=0, max=1, dv=dv, k=True)

		else:
			for i, attr_nane in enumerate(["{}Space".format(n) for n in target_names]):
				dv = 1 if i == default_value else 0
				cmds.addAttr(control, ln=attr_nane, min=0, max=1, dv=dv, k=True)
	else:
		if split:
			if cmds.objExists(control + ".translationSpace"):
				cmds.deleteAttr(control + ".translationSpace")

			if cmds.objExists(control + ".rotationSpace"):
				cmds.deleteAttr(control + ".rotationSpace")

			if translate:
				enum = ":".join(target_names)
				cmds.addAttr(control, ln="translationSpace", at="enum", en=enum, dv=default_value, k=True)

			if rotate:
				enum = ":".join(target_names)
				enum += ":matchTranslate" if translate else ""
				cmds.addAttr(control, ln="rotationSpace", at="enum", en=enum, dv=len(target_names), k=True)

		else:
			if cmds.objExists(control + ".space"):
				cmds.deleteAttr(control + ".space")

			enum = ":".join(target_names)
			cmds.addAttr(control, ln="space", at="enum", en=enum, dv=default_value, k=True)

	# connect attrs to matrix constraint choice nodes
	if weighted:
		if split:
			if translate:
				for i, target_data in enumerate(zip(["{}TranslationSpace".format(n) for n in target_names], targets)):
					attr_name, target = target_data
					cmds.connectAttr("{}.{}".format(control, attr_name), "{}.{}W{}".format(translate_choice, target, i))

			if rotate:
				for i, target_data in enumerate(zip(["{}RotationSpace".format(n) for n in target_names], targets)):
					attr_name, target = target_data
					cmds.connectAttr("{}.{}".format(control, attr_name), "{}.{}W{}".format(rotate_choice, target, i))

		else:
			for i, target_data in enumerate(zip(["{}Space".format(n) for n in target_names], targets)):
				attr_name, target = target_data
				cmds.connectAttr("{}.{}".format(control, attr_name), "{}.{}W{}".format(translate_choice, target, i))
	else:
		if split:
			if translate:
				cmds.connectAttr(control + ".translationSpace", translate_choice + ".selector")

			if rotate:
				cnd = cmds.createNode("condition")
				cmds.connectAttr(control + ".rotationSpace", cnd + ".firstTerm")
				if translate:
					cmds.connectAttr(control + ".translationSpace", cnd + ".colorIfTrueR")
				cmds.connectAttr(control + ".rotationSpace", cnd + ".colorIfFalseR")
				cmds.connectAttr(cnd + ".outColorR", rotate_choice + ".selector")
				cmds.setAttr(cnd + ".secondTerm", len(target_names))

		else:
			cmds.connectAttr(control + ".space", translate_choice + ".selector")
