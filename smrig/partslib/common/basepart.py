# -*- smrig: part  -*-
import logging

import maya.cmds as cmds
from smrig import env
from smrig.gui.mel import prompts
from smrig.lib import attributeslib
from smrig.lib import colorlib
from smrig.lib import constantlib
from smrig.lib import nodepathlib
from smrig.lib import nodeslib
from smrig.lib import selectionlib
from smrig.lib import utilslib
from smrig.lib.constantlib import *
from smrig.partslib.common import guidemixin
from smrig.partslib.common import rigmixin
from smrig.partslib.common import utils

log = logging.getLogger("smrig.partslib.basepart")
locator_suffix = naminglib.get_suffix("joint")
joint_suffix = naminglib.get_suffix("joint")
transform_suffix = naminglib.get_suffix("transform")
control_suffix = naminglib.get_suffix("animControl")


class Basepart(guidemixin.GuideMixin, rigmixin.RigMixin, object):
	"""
	This is the base part module which is inherited by all other parts.
	You should not import this part on its own. It is only meant to be inherited.
	"""

	BUILD_LAST = False

	docs = ""
	path = ""
	category = ""
	_control_group = {}
	_rig_group = {}

	def __init__(self, *input, **options):
		"""
		:param str input: Either the part type OR the guide node
		:param ** options:
		"""
		super(Basepart, self).__init__(*input, **options)

		self._guide_group = None
		self._options = {}

		self.register_option("side", "string", "C", value_required=True)
		self.register_option("name", "string", "")

		if input and cmds.objExists(input[0]):
			self.set_guide(input[0])

		elif options:
			self.update_options(**options)

		self.control_suffix = env.prefs.get_suffix("animControl")
		self.joint_suffix = env.prefs.get_suffix("joint")
		self.group_suffix = env.prefs.get_suffix("transform")
		self.placer_suffix = env.prefs.get_suffix("jointPlacer")

	def __str__(self):
		return "<part_type: '{}', guide_group: '{}'>".format(self.part_type, self._guide_group)

	def __repr__(self):
		return "<part_type: '{}', guide_group: '{}'>".format(self.part_type, self._guide_group)

	@property
	def part_type(self):
		"""
		:return: Rig part type.
		:rtype: str
		"""
		return naminglib.conversion.snake_to_lower_camel_case(self.__class__.__name__)

	@property
	def options(self):
		"""
		:return: Guide build options
		:rtype: dict
		"""
		return self._options

	@property
	def sorted_option_names(self):
		"""

		:return:
		"""
		return sorted(self._options, key=lambda x: self._options[x]['order_index'])

	@property
	def side(self):
		"""
		Side token

		:return:
		:rtype: str
		"""
		return self._options.get("side").get("value")

	@property
	def name(self):
		"""
		Name token

		:return:
		:rtype: str
		"""
		return self._options.get("name").get("value")

	@property
	def prefix(self):
		"""
		:return: Guide side and name prefix.
		:rtype: str
		"""
		return self.format_name("")

	@property
	def mirror_value(self):
		"""
		:return: Mirror value for mirroring, aim, upvector and scale values
		:rtype: int
		"""
		return -1 if self.side.startswith("R") else 1

	@property
	def namespace(self):
		"""
		Guide namespace.

		:return:
		:rtype: str
		"""
		return nodepathlib.get_namespace(self.guide_group) if self.guide_group else ""

	# Color properties --------------------------------------------------------------------------------------------

	@property
	def primary_color(self):
		"""
		:return: Primary color
		:rtype: str
		"""
		return colorlib.get_colors_from_side(self.side)[0]

	@property
	def secondary_color(self):
		"""
		:return: Primary color
		:rtype: str
		"""
		return colorlib.get_colors_from_side(self.side)[1]

	@property
	def detail_color(self):
		"""
		:return: Primary color
		:rtype: str
		"""
		return colorlib.get_colors_from_side(self.side)[2]

	# Guide properties -----------------------------------------------------------------------------------------

	def _format_guide_group_variables(self, index):
		"""
		:param int index:
		:return:
		:rtype: list
		"""
		grp = self.format_name([self.part_type, GUIDE_HIERARCHY[index]],
		                       node_type="transform",
		                       generate_new_index=False)

		if self.guide_group:
			namespace = nodepathlib.get_namespace(self.guide_group)
			grp = nodepathlib.add_namespace(grp, namespace) if namespace else grp

		return grp

	@property
	def guide_group(self):
		"""
		:return: Guide top node
		:rtype: str
		"""
		return self._guide_group if self._guide_group and cmds.objExists(self._guide_group) else ""

	@property
	def guide_scale_attribute(self):
		"""
		World scale attribute for guides.
		:return:
		"""
		return "{}.worldScale".format(self.guide_group) if self.guide_group else None

	@property
	def guide_control_group(self):
		"""
		Group for guide ctrls.

		:return:
		"""
		return self._format_guide_group_variables(0)

	@property
	def guide_placer_group(self):
		"""
		Group for guide locators.

		:return:
		"""
		return self._format_guide_group_variables(1)

	@property
	def guide_joint_group(self):
		"""
		Group for guide joints.

		:return:
		"""
		return self._format_guide_group_variables(2)

	@property
	def guide_geometry_group(self):
		"""
		Group for guide joints.

		:return:
		"""
		return self._format_guide_group_variables(3)

	@property
	def guide_noxform_group(self):
		"""
		Group for guide joints.

		:return:
		"""
		return self._format_guide_group_variables(4)

	@property
	def guide_nodes(self):
		"""
		Get all nodes in guide part hierarchy and all nodes connected to it.

		:return: All dag and nn dag nodes associated with the guide part.
		:rtype: list
		"""
		if not self.guide_group:
			return []

		namespace = self.namespace
		prefix = nodepathlib.add_namespace(self.prefix, namespace) if namespace else self.prefix
		nodes = selectionlib.get_children(self.guide_group, all_descendents=True)
		nodes.insert(0, self.guide_group)

		for node in list(nodes):
			history = cmds.listHistory(node, allConnections=1) or []
			history = [n for n in history if "dagNode" not in cmds.nodeType(n, inherited=1) and n not in nodes]
			nodes.extend(history)

		return cmds.ls(nodes)

	# rig properties ------------------------------------------------------------------------------------------

	@property
	def part_group(self):
		"""

		:return:
		"""
		return self.format_name([self.part_type, "part"], node_type="transform")

	@property
	def noxform_group(self):
		"""

		:return:
		"""
		return self.format_name([self.part_type, "noxform"], node_type="transform")

	def get_control_group(self, key=None):
		"""
		Get control groups based on parent_driver attribute name.

		:param key:
		:return:
		"""
		key = key if key else list(self._control_group.keys())[0]
		return self._control_group.get(key)

	def get_rig_group(self, key=None):
		"""
		Get rig groups based on parent_driver attribute name.

		:param key:
		:return:
		"""
		key = key if key else list(self._rig_group.keys())[0]
		return self._rig_group.get(key)

	def get_attribute_driver_group(self, key=None):
		"""

		:param key:
		:return:
		"""
		return self.format_name([self.part_type, key], node_type="transform")

	@property
	def rig_scale_attribute(self):
		"""
		World scale attribute for guides.
		:return:
		"""
		return "{}.worldScale".format(self.part_group) if self.part_group else None

	def get_selection_value(self, option_name):
		"""
		Get selection option type value as list

		:param option_name:
		:return:
		"""
		try:
			return eval(self.options.get(option_name).get("value") or [])

		except:
			return utilslib.conversion.as_list(self.options.get(option_name).get("value") or [])

	def find_stashed_nodes(self, option_name, stash_priority=True):
		"""
		Find a node stashed or not.

		:param option_name:
		:return:
		"""
		return cmds.ls(
			utilslib.scene.find_stashed_nodes(self.get_selection_value(option_name), stash_priority=stash_priority))

	# Option functions -----------------------------------------------------------------------------------------

	def register_option(self,
	                    name,
	                    data_type,
	                    default_value,
	                    min=None,
	                    max=None,
	                    enum="",
	                    tool_tip="",
	                    editable=True,
	                    rebuild_required=False,
	                    value_required=False,
	                    part_types=None):
		"""
		Register a new build option for part.

		Valid "data_type" values are:
			:int:
			:float:
			:bool:
			:string:
			:enum: Enum attribute (stored as a string "one:two:three")
			:single_selection: Single node selection attribute (stored list formated as a string)
			:selection: Selection attribute - stored list
			:parent_driver: Parent node attribute (stored as a string)
			:attribute_driver: Driver node for attribute connections (stored as a string)
			:rig_part: specify another rig part as an input

		:param str name: Option name
		:param str data_type: Option dataexporter type.
		:param multi default_value: Default value
		:param int/float min: Min value. (Ignored if data_type is not "int" or "float")
		:param int/float max: Min value. (Ignored if data_type is not "int" or "float")
		:param str enum: Enum values. (Ignored if data_type is not "enum")
		:param str tool_tip: Tool tip for Guides UI
		:param bool editable: Used for the world root part. If false the option is not editable in the UI.
		:param bool rebuild_required: If "True" part will need to be rebuild in order to modify the option.
		:param bool value_required: Value is required
		:param str/list part_types: IUf using a rig_part specify valid part types
		:rtype: None
		"""
		self.BUILD_LAST = True if data_type == "rig_part" else self.BUILD_LAST

		valid_data_types = ["int",
		                    "float",
		                    "bool",
		                    "string",
		                    "enum",
		                    "single_selection",
		                    "selection",
		                    "parent_driver",
		                    "attribute_driver",
		                    "rig_part"]

		# force default data_types for name and side options
		data_type = "string" if name in ["side", "name"] else data_type
		rebuild_required = False if name in ["side", "name"] else rebuild_required
		value_required = True if name == "side" else value_required
		tool_tip = tool_tip if tool_tip else " ".join(naminglib.conversion.split_camel_case(name)).capitalize() + "."

		# some error checking
		if data_type not in valid_data_types:
			message = "Data type: {} is not valid! See script editor for details.\n".format(data_type)
			log.error(message + self.register_option.__doc__)
			return

		if data_type == "enum" and not enum:
			message = "Enum type requires the 'enum' arguments! See script editor for details.\n"
			log.error(message + self.register_option.__doc__)
			return

		# Create option dict and add to __dict__
		order_idx = self._options.get(name).get("order_index") if name in self._options.keys() else len(
			self._options.keys())

		self._options[name] = {"order_index": order_idx,
		                       "data_type": data_type,
		                       "default": default_value,
		                       "value": default_value,
		                       "min": min,
		                       "max": max,
		                       "enum": enum,
		                       "part_types": utilslib.conversion.as_list(part_types),
		                       "tool_tip": tool_tip,
		                       "editable": editable,
		                       "require_rebuild": rebuild_required,
		                       "value_required": value_required}

		self.__dict__.update({name: default_value})

	def update_options(self, skip_rename=False, **kwargs):
		"""
		Update build option values.
		This method will also rename the guide parts hierarchy if side or name options are changed.

		:param bool skip_rename: Do not rename hierarchy
		:param kwargs: Option values to update.
		:rtype: None
		"""
		if "side" in kwargs.keys():
			side = kwargs.get("side")
			kwargs["side"] = side.upper() if env.prefs.get_capitalize_side() else side.lower()

		current_side = str(self.side)
		current_name = str(self.name)
		guide_nodes = utilslib.conversion.as_list(self.guide_nodes)

		for option_label, value in kwargs.items():
			if option_label in self.options.keys():
				if value == self._options.get(option_label).get("value"):
					continue

				if not self._options.get(option_label).get("editable"):
					log.error("Option is not editable: {}".format(option_label))
					continue

				# check value is required
				if self._options.get(option_label).get("value_required") and not value:
					log.error("A value is required for option: {}".format(option_label))
					continue

				# validation for strings
				if self._options.get(option_label).get("data_type") == "string":
					value = naminglib.clean_name(value)

				# validation for parent_drivers asnd selections
				if self._options.get(option_label).get("data_type") in ["parent_driver", "single_selection"]:
					value = value.replace(locator_suffix, joint_suffix) if value.endswith(locator_suffix) else value

				if self._options.get(option_label).get("data_type") == "selection":
					value = [v.replace(locator_suffix, joint_suffix) if v.endswith(locator_suffix) else v for v in
					         utilslib.conversion.as_list(value)]

				if self._options.get(option_label).get("data_type") == "rig_part":
					value = utils.find_guide_group_from_selection(value) if cmds.objExists(value) else value
					if cmds.objExists(value + ".partType"):
						part_types = self._options.get(option_label).get("part_types")
						part_type = cmds.getAttr(value + ".partType")

						if part_types and part_type not in part_types:
							log.warning("{} not of part type {}".format(value, part_types))
							continue

				# check floats and ints
				if self._options.get(option_label).get("data_type") in ["int", "float"]:
					min_value = self._options.get(option_label).get("min")
					max_value = self._options.get(option_label).get("max")

					if min_value is not None and value < min_value:
						msg = "Cannot set the option {} below its minimum value of {}.".format(option_label, min_value)
						log.error(msg)
						continue

					if max_value is not None and value < max_value:
						msg = "Cannot set the option {} above its maximum value of {}.".format(option_label, max_value)
						log.error(msg)
						continue

				# set the actual value and update __dict__
				self._options[option_label]["value"] = value
				self.__dict__.update({option_label: value})

				log.debug("Updated option values: {} = {}".format(option_label, value))

		if self.guide_group:
			if not skip_rename:
				new_side = self.side if self._options.get("side").get("editable") else current_side
				new_name = self.name if self._options.get("name").get("editable") else current_name

				if new_side != current_side or new_name != current_name:
					self.rename_guide_hierarchy(current_side, current_name, new_side, new_name, guide_nodes)

			# set options on guide node
			cmds.setAttr("{}.options".format(self.guide_group), str(self.options), type="string")

	def rename_guide_hierarchy(self, current_side, current_name, new_side, new_name, guide_nodes):
		"""
		Rename the gues hierarchy base on given side and name tokens.
		This will also attempt to rename any non-dag nodes that may have the same nameing prefix

		:param str current_side:
		:param str current_name:
		:param str new_side:
		:param str new_name:
		:param list guide_nodes:
		:return: Pass or failed
		:rtype: bool
		"""

		def replace_name(node, current_side, current_name, new_side, new_name):
			"""
			generate new names - remove temp build prefix, replace side and name token

			:param node:
			:param current_side:
			:param current_name:
			:param new_side:
			:param new_name:
			:return: new node name
			:rtype: str
			"""
			node_tokens = node.split("_")

			node_tokens[0] = node_tokens[0].replace(current_side, new_side, 1)
			node_tokens[1] = node_tokens[1].replace(current_name, new_name, 1)
			return naminglib.clean_name("_".join(node_tokens))

		def check_name_clashes(new_names):
			"""
			Check the list of new node names against current node names to check for clashes.

			:param list new_names: New node names that SHOULD not exist in scene
			:return: True if a clash is found. False if no clash.
			:rtype: bool
			"""
			stashed_nodes = list(set(cmds.ls()) - set(self.guide_nodes))
			stashed_nodes = [nodepathlib.remove_namespace(n) for n in stashed_nodes]
			clashing = [n for n in new_names if n in stashed_nodes]

			return True if clashing else False

		if not guide_nodes:
			return

		# get new side amd names
		guide_nodes = [n for n in guide_nodes if current_side in n and current_name in n]
		new_names = [replace_name(n, current_side, current_name, new_side, new_name) for n in guide_nodes]

		proceed = True
		while check_name_clashes(new_names):
			result = prompts.option_prompt(current_side, current_name)

			if result:
				proceed = True
				new_side, new_name = result
				new_names = [replace_name(n, current_side, current_name, new_side, new_name) for n in guide_nodes]

			else:
				proceed = False
				break

		if proceed:
			for i, node in enumerate(guide_nodes):
				if node != new_names[i]:
					guide_nodes[i] = cmds.rename(node, new_names[i])

		elif cmds.namespace(exists=utilslib.scene.STASH_NAMESPACE):
			self.delete_guide()
			self.set_guide(clear=True)
			return

		else:
			new_side = current_side
			new_name = current_name

		self._guide_group = guide_nodes[0]
		self._options["side"]["value"] = new_side
		self._options["name"]["value"] = new_name
		self.__dict__.update({"side": new_side, "name": new_name})
		cmds.setAttr("{}.options".format(self._guide_group), str(self.options), type="string")

		utilslib.scene.unstash_all_nodes()
		return proceed

	# Guide functions ---------------------------------------------------------------------------------------------
	def find_guide_from_options(self):
		"""
		Find and set the guide node based on current options IF it exists

		:return:
		"""
		guide_group_name = self.format_name([self.part_type, "guide"], node_type="transform")
		if cmds.objExists(guide_group_name):
			self.set_guide(guide_group_name)

	def set_guide(self, guide_group=None, clear=False):
		"""
		Set or clear guide node and options from specified guide node in scene.

		:param str guide_group: Node to set as guide.
		:param bool clear: Clear guide node and reset options to default
		:rtype: None
		"""
		self._guide_group = None
		self.update_options(skip_rename=True, **{k: v["default"] for (k, v) in self._options.items()})

		if clear:
			log.debug("Cleared guide node and reset options to default.")
			return

		if not guide_group:
			selection = cmds.ls(sl=1)
			nodes = selection + selectionlib.get_parents(selection, num=-1)
			guide_group = [n for n in nodes if n and cmds.attributeQuery("partType", node=n, exists=1)]
			guide_group = guide_group[0] if guide_group else ""

		if cmds.getAttr("{}.partType".format(guide_group)) == self.part_type:
			self._guide_group = guide_group
			options = eval(cmds.getAttr("{}.options".format(guide_group)))
			self.update_options(skip_rename=True, **{k: v["value"] for (k, v) in options.items()})

			log.debug("Set {} as guide for part: {}".format(guide_group, self.part_type))

		else:
			msg = "{0} is not of type: {1}. Instantiate {1} and re-run this command.".format(guide_group,
			                                                                                 self.part_type)
			log.error(msg)

	def start_guide(self):
		"""
		Create guide control group hierarchy.

		:return:
		"""
		utilslib.scene.stash_nodes(nodes=GUIDE_GRP, hierarchy=True)

		guide_group_name = self.format_name([self.part_type, "guide"], node_type="transform")

		if cmds.objExists(guide_group_name):
			error_message = "Guide node: {} already exists. Cannot continue.".format(guide_group_name)
			log.error(error_message)
			raise RuntimeError(error_message)

		self._guide_group = cmds.createNode("transform", name=guide_group_name)

		controls_grp = cmds.createNode("transform", p=self._guide_group, n=self.guide_control_group)
		locators_grp = cmds.createNode("transform", p=self._guide_group, n=self.guide_placer_group)
		joints_grp = cmds.createNode("transform", p=self._guide_group, n=self.guide_joint_group)
		geometry_grp = cmds.createNode("transform", p=self._guide_group, n=self.guide_geometry_group)
		notransform_grp = cmds.createNode("transform", p=self._guide_group, n=self.guide_noxform_group)

		# add display attrs
		cmds.addAttr(self._guide_group, ln="smrigGuideGroup", at="message")
		cmds.addAttr(self._guide_group, ln="partType", dt="string")
		cmds.addAttr(self._guide_group, ln="options", dt="string")
		cmds.addAttr(self._guide_group, ln="buildLast", at="bool", dv=self.BUILD_LAST)
		cmds.addAttr(self._guide_group, ln="skipBuild", at="bool", dv=False, k=True)

		attributeslib.add_spacer_attribute(self._guide_group, "VisSpacer")

		nodeslib.display.create_visibility_link(self._guide_group,
		                                        controls_grp,
		                                        attribute_name="controlsVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(self._guide_group,
		                                        locators_grp,
		                                        attribute_name="jointsVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(self._guide_group,
		                                        joints_grp,
		                                        attribute_name="jointsVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(self._guide_group,
		                                        geometry_grp,
		                                        attribute_name="geometryVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		attributeslib.add_spacer_attribute(self._guide_group, "DisplaySpacer")

		nodeslib.display.create_visibility_link(self._guide_group,
		                                        [],
		                                        attribute_name="controlDisplayLocalAxis",
		                                        shapes_only=False,
		                                        default_value=0)

		nodeslib.display.create_visibility_link(self._guide_group,
		                                        [],
		                                        attribute_name="jointDisplayLocalAxis",
		                                        shapes_only=False,
		                                        default_value=0)

		attributeslib.add_spacer_attribute(self._guide_group, "RefSpacer")

		nodeslib.display.create_display_type_link(self._guide_group,
		                                          joints_grp,
		                                          attribute_name="jointsDisplay",
		                                          display_type="reference")

		cmds.addAttr(self._guide_group, ln="worldScale", dv=1.0, k=1)

		# setup uniform scale
		nodeslib.display.create_uniform_scale_link(self._guide_group, min=0.001)

		# setup worldScale attribute
		dmx = nodeslib.create_node("decomposeMatrix", self._guide_group)
		cmds.connectAttr("{}.worldMatrix".format(self._guide_group), "{}.inputMatrix".format(dmx))
		cmds.connectAttr("{}.outputScaleY".format(dmx), "{}.worldScale".format(self._guide_group))

		# turn off inherit transforms on no transform grp
		cmds.setAttr("{}.it".format(notransform_grp), 0)
		cmds.hide(notransform_grp)

		# set part_type and options attributes
		cmds.setAttr("{}.partType".format(self._guide_group), self.part_type, type="string")
		cmds.setAttr("{}.options".format(self._guide_group), str(self.options), type="string")

		# cleanup and lock stuff
		attributeslib.common.set_attributes(notransform_grp, ["it"], lock=True, keyable=False)
		attributeslib.common.set_attributes(self._guide_group, ["worldScale"], lock=True, keyable=False)
		attributeslib.common.set_attributes(self._guide_group,
		                                    ["jointRadius", "placerRadius"],
		                                    channel_box=True,
		                                    keyable=False)

		# cmds.setAttr("{}.displayHandle".format(self._guide_group), 1)

		attributeslib.set_attributes(controls_grp, ["t", "r", "s", "v"], lock=True, keyable=False)
		attributeslib.set_attributes(locators_grp, ["t", "r", "s", "v"], lock=True, keyable=False)
		attributeslib.set_attributes(joints_grp, ["t", "r", "s", "v"], lock=True, keyable=False)
		attributeslib.set_attributes(geometry_grp, ["t", "r", "s", "v"], lock=True, keyable=False)
		attributeslib.set_attributes(notransform_grp, ["t", "r", "s", "v"], lock=True, keyable=False)

		cmds.select(self._guide_group)

		return self._guide_group

	def build_guide(self):
		"""
		This is an empty class that is useed to hold the actual guide build code for each part.

		:rtype: None
		"""
		pass

	def finish_guide(self):
		"""
		Finish guide build: This will remove the temp naming prefix from all guide nodes and
		parent the guide top notde to the guides group.

		:return: Wheter it successfully built the guide or not.
		:rtype: bool
		"""
		result = self.rename_guide_hierarchy(self.side, self.name, self.side, self.name, self.guide_nodes)

		if result:
			if not cmds.objExists(GUIDE_GRP):
				cmds.createNode("transform", n=GUIDE_GRP)
				cmds.connectAttr("{}.sy".format(GUIDE_GRP), "{}.sx".format(GUIDE_GRP))
				cmds.connectAttr("{}.sy".format(GUIDE_GRP), "{}.sz".format(GUIDE_GRP))
				cmds.aliasAttr("UniformScale", "{}.sy".format(GUIDE_GRP))
				attributeslib.set_attributes(GUIDE_GRP, ["sx", "sz"], keyable=False, lock=True)

			cmds.parent(self.guide_group, GUIDE_GRP)

		utilslib.scene.unstash_all_nodes()
		return result

	def delete_guide(self):
		"""
		Delete guide heriarchy and all connected non dag nodes from scene.

		:rtype: None
		"""
		error_prone_node_types = ["curveInfo"]

		nodes = self.guide_nodes
		if nodes:
			error_prone_nodes = [n for n in nodes if cmds.nodeType(n) in error_prone_node_types]
			cmds.delete(error_prone_nodes)
			cmds.delete(cmds.ls(nodes))

	def mirror_guide_pre(self):
		"""
		Custom pre mirror function

		:return:
		"""
		pass

	def mirror_guide_post(self):
		"""
		Custom post mirror function

		:return:
		"""
		pass

	# -----------------------------------------------------------------------------------------------------------------

	def parent_skeleton(self):
		"""
		Empty function for handling custom skeleton parenting.
		Its recommended to use try statements in this one.

		:return:
		"""
		pass

	# -----------------------------------------------------------------------------------------------------------------

	def start_rig(self):
		"""
		Create guide control group hierarchy.

		:return:
		"""

		if not cmds.objExists(RIG_GROUP):
			rig_grp = cmds.createNode("transform", n=RIG_GROUP)
			parts_grp = cmds.createNode("transform", n=PARTS_GROUP, p=RIG_GROUP)
			joints_grp = cmds.createNode("transform", n=JOINTS_GROUP, p=RIG_GROUP)
			model_grp = cmds.createNode("transform", n=MODEL_GROUP, p=RIG_GROUP)
			notransform_grp = cmds.createNode("transform", n=NO_TRANSFORM_GROUP, p=RIG_GROUP)

			cache_sel = cmds.sets(n=CACHE_SET, em=1)
			engine_sel = cmds.sets(n=ENGINE_SET, em=1)
			control_sel = cmds.sets(n=CONTROL_SET, em=1)
			cmds.sets(rig_grp, control_sel, cache_sel, engine_sel, n=RIG_SET)

			cmds.setAttr("{}.it".format(notransform_grp), 0)
			cmds.parent(ROOT_JOINT, joints_grp)

		if cmds.objExists(self.part_group):
			error_message = "Rig node: {} already exists. Cannot continue.".format(self.part_group)
			log.error(error_message)
			raise RuntimeError(error_message)

		part_grp = cmds.createNode("transform", n=self.part_group, p=PARTS_GROUP)
		cmds.createNode("transform", n=self.noxform_group, p=NO_TRANSFORM_GROUP)

		# create driver parent nodes
		parent_drivers = [(k, v.get("value")) for k, v in self.options.items()
		                  if v.get("data_type") in ["parent_driver", "attribute_driver"]] or [("", None)]

		self._control_group = {}
		self._rig_group = {}

		for token, driver in parent_drivers:
			if driver:
				driver_parent_name = self.format_name([self.part_type, token], node_type="transform")
				driver_parent = cmds.createNode("transform", n=driver_parent_name, p=part_grp)
				attributeslib.tag.add_tag_attribute(driver_parent, PART_PARENT_DRIVER_TAG, driver)
				driver_key = token

			else:
				driver_parent = part_grp
				driver_key = "parent"

			tokens = [self.part_type, token, "controls"]
			ctrl_group_name = self.create_node("transform", [tokens[0], tokens[1], tokens[2]], parent=driver_parent)

			tokens = [self.part_type, token, "rig"]
			rig_group_name = self.create_node("transform", [tokens[0], tokens[1], tokens[2]], parent=driver_parent)

			attributeslib.tag.add_tag_attribute(ctrl_group_name, PART_CONTROL_GROUP_TAG)
			attributeslib.tag.add_tag_attribute(rig_group_name, PART_RIG_GROUP_TAG)

			self._control_group[driver_key] = ctrl_group_name
			self._rig_group[driver_key] = rig_group_name

			# setup worldScale attribute
			if not cmds.objExists("{}.worldScale".format(part_grp)):
				dmx = nodeslib.create_node("decomposeMatrix", part_grp)
				cmds.addAttr(part_grp, ln="worldScale")

				cmds.connectAttr("{}.worldMatrix".format(ctrl_group_name), "{}.inputMatrix".format(dmx))
				cmds.connectAttr("{}.outputScaleY".format(dmx), "{}.worldScale".format(part_grp))

	def build_rig(self, *args, **kwargs):
		"""
		Placeholder for build code.

		:param args:
		:param kwargs:
		:return:
		"""
		pass

	def finish_rig(self):
		"""

		:return:
		"""
		parts_group_name = self.format_name([self.part_type, "part"], node_type="transform")
		notransform_grp = self.format_name([self.part_type, "noxform"], node_type="transform")

		ctrl_grps = [n for n in cmds.listRelatives(parts_group_name, ad=True) or []
		             if cmds.objExists(n + "." + PART_CONTROL_GROUP_TAG)]

		rig_grps = [n for n in cmds.listRelatives(parts_group_name, ad=True) or []
		            if cmds.objExists(n + "." + PART_RIG_GROUP_TAG)]

		nodeslib.display.create_visibility_link(constantlib.VISIBILITY_CONTROL,
		                                        ctrl_grps,
		                                        attribute_name="controlsVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

		nodeslib.display.create_visibility_link(constantlib.VISIBILITY_CONTROL,
		                                        rig_grps + [notransform_grp],
		                                        attribute_name="rigVisibility",
		                                        shapes_only=False,
		                                        default_value=1)

	# -----------------------------------------------------------------------------------------------------------------

	def format_name(self, name, node_type=None, generate_new_index=False, side=None):
		"""
		Prepend side and name tokens. Will also format to naming convention.

		:param name:
		:param node_type:
		:param generate_new_index:
		:param side:
		:return:
		"""
		name = utilslib.conversion.as_list(name)
		name.insert(0, self.name)
		name.insert(0, side if side else self.side)

		return naminglib.format_name(name, node_type=node_type, generate_new_index=generate_new_index)

	def create_node(self, node_type, name=None, generate_new_index=True, side=None, **kwargs):
		"""
		Create name formatted node.

		:param node_type:
		:param name:
		:param generate_new_index:
		:param side:
		:param kwargs:
		:return:
		"""
		name = self.format_name(name, node_type=node_type, generate_new_index=generate_new_index, side=side)
		return nodeslib.create_node(node_type, name, **kwargs)
