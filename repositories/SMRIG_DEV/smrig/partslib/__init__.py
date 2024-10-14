import os
import logging
import maya.cmds as cmds

# Compatibility for string types in both Python 2 and Python 3
import sys

if sys.version_info[0] < 3:
	string_types = (str, unicode)
else:
	string_types = (str,)

from smrig.env import prefs
from smrig.gui import mel
from smrig.lib import constantlib
from smrig.lib import decoratorslib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.partslib.common import basepart
from smrig.partslib.common import utils
from smrig.partslib.common.manager import *

manager = Manager ()
reload_lib = manager.reload_lib
left_side, right_side = prefs.get_sides ()[0:2]
log = logging.getLogger ("smrig.partslib")

BIN_PATH = os.path.join (os.path.dirname (__file__), "bin")


def part(input=None, **options):
	"""
	Use this part function to instantiate the correct part for the specified guide group.

	:param str input: part_type OR guide_group
	:param ** options: Build options
	:return: An instance of the specified part python module.class
	:rtype: python object
	"""
	if isinstance(input, basepart.Basepart):
		return input

	found = utils.find_guide_group_from_selection(input) if input is None or cmds.objExists(input) else None
	input = found if found else input

	part_type = cmds.getAttr("{}.partType".format(input)) if cmds.objExists("{}.partType".format(input)) else input
	part_obj = manager.instance_part(part_type)

	if not part_obj:
		return

	if cmds.objExists("{}.partType".format(input)):
		part_obj.set_guide(input)

	elif options:
		part_obj.update_options(**options)

	part_obj.path = manager.get_path(part_type)
	part_obj.category = manager.get_category(part_type)

	return part_obj


# template functions -------------------------------------------------------------------------------------


def build_template(name, build=True, set_shapes=True, set_colors=True):
	"""
	Build a template

	:param name:
	:param build:
	:param set_shapes:
	:param set_colors:
	:return:
	"""
	module_path = manager._data.get(name, {}).get("path")

	if not module_path:
		raise ValueError("{} is not a valid template.".format(name))

	template_data = iolib.json.read(module_path)

	for item in template_data.get("template", {}):
		part_type = item.get("part_type")
		part_data = item.get("part_data")
		options = {o: utilslib.conversion.as_str(v.get("value")) for o, v in item.get("options").items()}

		if build and part_type != "root":
			build_guide(part_type, **options)

		else:
			part_obj = part(part_type, **options)
			part_obj.find_guide_from_options()

		utils.set_guide_data(part_data, set_shapes=set_shapes, set_colors=set_colors)


# guide functions ----------------------------------------------------------------------------------------


def build_root_guide():
	"""

	:return:
	"""
	root_jnt = cmds.ls(constantlib.ROOT_JOINT, "{}:{}".format(utilslib.scene.STASH_NAMESPACE, constantlib.ROOT_JOINT))
	if not root_jnt:
		root_obj = manager.instance_part("root")
		root_obj.start_guide()
		root_obj.build_guide()
		root_obj.finish_guide()


def build_guide(part_type, **options):
	"""
	Build and finalize a guide.

	:param str part_type:
	:param ** options:
	:return: An instance of the specified part python module.class
	:rtype: python object
	"""
	options = {k: utilslib.conversion.as_str(v) for k, v in options.items()}
	part_obj = part(part_type, **options)

	if not part_obj:
		raise ValueError("{} is not a valid part.".format(part_type))

	if part_obj.part_type != "root":
		build_root_guide()

	part_obj.start_guide()
	part_obj.build_guide()
	part_obj.finish_guide()

	return part_obj


def print_options(input=None):
	"""
	Print part options

	:param input:
	:return:
	"""
	source_part = part(input)
	if not source_part:
		raise ValueError("Cannot find part from: {}.".format(input))

	sorted_options = sorted((v.get("order_index"), k, v) for (k, v) in source_part.options.items())
	print("\n{}".format(source_part))

	for i, name, data in sorted_options:
		value = "'{}'".format(data.get("value")) if isinstance(data.get("value"), string_types) else data.get("value")
		print("\toption: '{}', type: '{}', value: {}".format(name, data.get("data_type"), value))


@decoratorslib.preserve_selection
def update_options(input=None, **options):
	"""
	Remove and rebuild guide part

	:param input:
	:param options:
	:return:
	"""
	source_part = part(input)
	options = {k: utilslib.conversion.as_str(v) for k, v in options.items()}

	if not source_part:
		raise ValueError("Cannot find part from: {}.".format(input))

	locked_options = [k for k, v in source_part.options.items() if v.get("require_rebuild")
	                  if k in options.keys()]

	if locked_options:
		if mel.prompts.confirm_dialog(message="Updating options requires rebuild, Continue?"):

			part_data = utils.get_guide_data(source_part, world_space=True)
			points = get_surface_points(source_part)

			source_part.delete_guide()
			source_part.update_options(**options)
			source_part.start_guide()
			source_part.build_guide()
			source_part.finish_guide()

			if not source_part.guide_group:
				return

			set_surface_points(source_part, points)
			utils.set_guide_data(part_data, None, True, True, world_space=True)
			log.info("Rebuilt guide & updated options: {}".format(source_part.guide_group))

			return source_part

	else:
		source_part.update_options(**options)

	return source_part


@decoratorslib.preserve_selection
def rebuild_guide(input=None, set_shapes=True, set_colors=True, world_space=False):
	"""
	Remove and rebuild guide part

	:param input:
	:param set_shapes:
	:param set_colors:
	:param world_space:
	:return:
	"""
	source_part = part(input)

	if not source_part:
		raise ValueError("Cannot find part from: {}.".format(input))

	part_data = utils.get_guide_data(source_part, world_space=world_space)
	points = get_surface_points(source_part)

	# rebuild
	source_part.delete_guide()
	source_part.start_guide()
	source_part.build_guide()
	source_part.finish_guide()

	if not source_part.guide_group:
		return

	set_surface_points(source_part, points)
	utils.set_guide_data(part_data, None, set_shapes, set_colors, world_space=world_space)
	log.info("Rebuilt guide: {}".format(source_part.guide_group))
	return source_part


def duplicate_guide(input=None, set_shapes=True, set_colors=True, **options):
	"""
	Mirror Guide part.

	:param input:
	:param set_shapes:
	:param set_colors:
	:param options:
	:return:
	"""
	source_part = part(input)
	options = {k: utilslib.conversion.as_str(v) for k, v in options.items()}

	if not source_part:
		raise ValueError("Cannot find part from: {}.".format(input))

	part_data = utils.get_guide_data(source_part)

	# get mirrorpart part and find mirro guide node if it exists
	target_options = {k: v.get("value") for k, v in source_part.options.items()}
	target_options.update(options)
	target_part = part(source_part.part_type, **target_options)

	# build it if it doesnt exist
	if not target_part.guide_group:
		target_part.start_guide()
		target_part.build_guide()
		target_part.finish_guide()

	if not target_part.guide_group:
		return

	match_surfaces(source_part, target_part)
	utils.set_guide_data(part_data, target_part, set_shapes, set_colors)
	log.info("Duplicated guide: {} from {}".format(target_part.guide_group, source_part.guide_group))
	return target_part


@decoratorslib.preserve_selection
def mirror_guide(input=None, mirror_mode="x", set_shapes=True, set_colors=False, **options):
	"""
	Mirror Guide part.

	:param input:
	:param mirror_mode:
	:param set_shapes:
	:param set_colors:
	:param options:
	:return:
	"""
	source_part = part(input)
	options = {k: utilslib.conversion.as_str(v) for k, v in options.items()}

	if not source_part:
		raise ValueError("Cannot find part from: {}.".format(input))

	part_data = utils.get_guide_data(source_part)

	if "side" not in options.keys():
		sides = prefs.get_sides()

		if source_part.side.startswith(sides[0]):
			options["side"] = source_part.side.replace(sides[0], sides[1], 1)

		elif source_part.side.startswith(sides[1]):
			options["side"] = source_part.side.replace(sides[1], sides[0], 1)

	# mirror options
	dtypes = ["parent_driver", "attribute_driver", "single_election", "rig_part"]
	mirror_options = {k: v for k, v in source_part.options.items() if v.get("data_type") in dtypes}

	for key, value in mirror_options.items():
		try:
			if value.get("value").startswith(sides[0]):
				options[key] = value.get("value").replace(sides[0], sides[1], 1)

			elif value.get("value").startswith(sides[1]):
				options[key] = value.get("value").replace(sides[1], sides[0], 1)
		except:
			pass

	# get mirrorpart part and find mirro guide node if it exists
	target_options = {k: v.get("value") for k, v in source_part.options.items()}
	target_options.update(options)
	target_part = part(source_part.part_type, **target_options)
	target_part.find_guide_from_options()

	# build it if it doesnt exist
	if not target_part.guide_group:
		target_part.start_guide()
		target_part.build_guide()
		target_part.finish_guide()

	if not target_part.guide_group:
		log.debug("Cancelled or no mirror part guide found.")
		return

	# if the source is the same as the target then mirrorpart left to right controls within the part.
	if target_part.guide_group == source_part.guide_group:
		return mirror_center_guide(source_part, mirror_mode, set_shapes, set_colors)

	target_part.mirror_guide_pre()
	mirror_surfaces(source_part, target_part)
	node_set = utils.set_guide_data(part_data, target_part, set_shapes, set_colors)
	t_guide_group, t_placers, t_pivots, t_controls, t_geometry, t_geometry_shapes = node_set
	s_guide_group, s_placers, s_pivots, s_controls, s_geometry, s_geomeretry_shapes = part_data["nodes"]

	s_nodes = [s_guide_group] + s_placers + s_pivots + s_controls + s_geometry
	t_nodes = [t_guide_group] + t_placers + t_pivots + t_controls + t_geometry

	# mirrorpart nodes
	for s_node, t_node in zip(s_nodes * 3, t_nodes * 3):
		transformslib.mirror.mirror_node(s_node, t_node, mirror=mirror_mode, translate=True, rotate=True, scale=False)

	# mirrorpart and set controls
	cmds.dgdirty(a=True)
	utils.mirror_controls(s_controls, t_controls + t_geometry, mirror_mode, set_shapes, set_colors)
	target_part.mirror_guide_post()

	log.info("Mirrored guide: {} from {}".format(target_part.guide_group, source_part.guide_group))
	return target_part


def mirror_center_guide(source_part=None, mirror_mode="x", set_shapes=True, set_colors=False):
	"""
	Mirror center sided parts with left and right controls .

	:param source_part:
	:param mirror_mode:
	:param set_shapes:
	:param set_colors:
	:return:
	"""
	if not [n for n in source_part.guide_nodes if n.startswith(left_side)]:
		log.warning("Cannot mirror this part: This is a center sided part without left or right nodes.")
		return

	part_data = utils.get_guide_data(source_part)
	s_guide_group, s_placers, s_pivots, s_controls, s_geometry, s_geomeretry_shapes = part_data["nodes"]
	s_nodes = [s_guide_group] + s_placers + s_pivots + s_controls + s_geometry

	mirror_center_surfaces(source_part)
	source_part.mirror_guide_pre()

	# mirrorpart nodes
	for s_node in s_nodes * 3:
		if s_node.startswith(left_side):
			t_node = s_node.replace(left_side, right_side, 1)
			transformslib.mirror.mirror_node(s_node, t_node,
			                                 mirror=mirror_mode,
			                                 translate=True,
			                                 rotate=True,
			                                 scale=False)

	# mirrorpart and set controls
	l_controls = [n for n in s_controls if n.startswith(left_side)]
	r_controls = [n.replace(left_side, right_side, 1) for n in l_controls]

	utils.mirror_controls(l_controls, r_controls, mirror_mode, set_shapes, set_colors)
	source_part.mirror_guide_post()

	log.info("Mirrored center sided guide: {}".format(source_part.guide_group))
	return source_part


def get_surface_points(source_part):
	"""
	Get surface shape for rebuilding later

	:param source_part:
	:return:
	"""
	geos = utils.get_guide_surfaces_from_part(source_part)
	points = {}

	for geo in geos:
		for v_idx in range(7):
			for u_idx in range(7):
				source_cv = "{}.cv[{}][{}]".format(geo, u_idx, v_idx)
				points[source_cv] = cmds.xform(source_cv, q=True, a=True, t=True)

	return points


def set_surface_points(source_part, points):
	"""

	:param source_part:
	:param points:
	:return:
	"""
	geos = utils.get_guide_surfaces_from_part(source_part)

	for geo in geos:
		for v_idx in range(7):
			for u_idx in range(7):
				source_cv = "{}.cv[{}][{}]".format(geo, u_idx, v_idx)
				pos = points.get(source_cv)
				if pos:
					cmds.xform(source_cv, a=True, t=pos)


def match_surfaces(source_part, target_part):
	"""
	mirros surfaces for left and right sides.
	Surfaces MUST havce 6 x 6 cvs

	:param source_part:
	:param target_part:
	:return:
	"""
	s_geos = utils.get_guide_surfaces_from_part(source_part)
	t_geos = utils.get_guide_surfaces_from_part(target_part)

	for s_geo, t_geo in zip(s_geos, t_geos):
		for v_idx in range(7):
			for u_idx in range(7):
				source_cv = "{}.cv[{}][{}]".format(s_geo, u_idx, v_idx)
				target_cv = "{}.cv[{}][{}]".format(t_geo, u_idx, v_idx)
				cmds.xform(target_cv, a=True, t=cmds.xform(source_cv, q=True, a=True, t=True))


def mirror_surfaces(source_part, target_part):
	"""
	mirros surfaces for left and right sides.
	Surfaces MUST havce 6 x 6 cvs

	:param source_part:
	:param target_part:
	:return:
	"""
	s_geos = utils.get_guide_surfaces_from_part(source_part)
	t_geos = utils.get_guide_surfaces_from_part(target_part)

	for s_geo, t_geo in zip(s_geos, t_geos):
		for v_idx in range(7):
			for u_idx in range(7):
				source_cv = "{}.cv[{}][{}]".format(s_geo, u_idx, v_idx)
				target_cv = "{}.cv[{}][{}]".format(t_geo, 6 - u_idx, 6 - v_idx)
				cmds.xform(target_cv, a=True, t=[-x for x in cmds.xform(source_cv, q=True, a=True, t=True)])


def mirror_center_surfaces(source_part):
	"""
	mirros surfaces for center side.
	Surfaces MUST havce 6 x 6 cvs

	:param source_part:
	:return:
	"""
	geos = utils.get_guide_surfaces_from_part(source_part)
	for geo in geos:
		for v_idx in range(7):
			for u_idx in range(3):
				source_cv = "{}.cv[{}][{}]".format(geo, 6 - u_idx, v_idx)
				target_cv = "{}.cv[{}][{}]".format(geo, u_idx, v_idx)

				pos = cmds.xform(source_cv, q=True, a=True, t=True)
				cmds.xform(target_cv, a=True, t=[-pos[0], pos[1], pos[2]])


def delete_guide(input=None):
	"""
	Delete guide nodes from scene.

	:param input:
	:return:
	"""
	source_part = part(input)
	if not source_part:
		raise ValueError("Cannot find part from: {}.".format(input))

	source_part.delete_guide()


# rig functions ----------------------------------------------------------------------------------------

@decoratorslib.undoable
def build_rig(part_node):
	"""
	Build rig part.

	:param part_type:
	:return:
	"""

	part_obj = part(part_node)

	if cmds.objExists(part_obj.guide_group + ".skipBuild") and cmds.getAttr(part_obj.guide_group + ".skipBuild"):
		return part_obj

	print("# ---------------------------------------------------------------------------")
	print("# Building: {}".format(part_obj))

	part_obj.start_rig()
	part_obj.build_rig()
	part_obj.finish_rig()

	# post cleanup for build
	hide_stuff()

	print("# Finished building: {}".format(part_obj))
	print("# ---------------------------------------------------------------------------\n")

	return part_obj


@decoratorslib.undoable
def build_rigs(exclude_types=None, build_last=True):
	"""
	Build all rig parts in scene.

	:param exclude_types:
	:param build_last:
	:return:
	"""
	parts = utils.get_guides_in_scene()
	root_parts = [p for p in parts if cmds.getAttr(p + ".partType") == "root"]
	remaining_parts = [p for p in parts if p not in root_parts]

	if exclude_types:
		exclude_types = utilslib.conversion.as_list(exclude_types)
		remaining_parts = [p for p in remaining_parts if cmds.getAttr(p + ".partType") not in exclude_types]

	last_parts = []
	for part_node in root_parts:
		build_rig(part_node)

	for part_node in remaining_parts:
		if cmds.objExists(part_node + ".buildLast") and cmds.getAttr(part_node + ".buildLast"):
			last_parts.append(part_node)
		else:
			build_rig(part_node)

	if build_last:
		for part_node in last_parts:
			build_rig(part_node)

	# post cleanup for build
	hide_stuff()


def hide_stuff():
	"""
	Hide ik handles and other junk

	:return:
	"""
	cmds.hide(cmds.ls(type="ikHandle"))
