import logging

import maya.cmds as cmds
from smrig.env import prefs
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib.constantlib import GUIDE_GRP

log = logging.getLogger("smrig.partslib.utils")
ik_suffix = prefs.get_suffix("ikHandle")


def get_guides_in_scene(part_type=None):
	"""

	:return:
	"""
	guide_grp = cmds.ls(GUIDE_GRP, "*:" + GUIDE_GRP)
	if not guide_grp:
		return []

	nodes = selectionlib.get_children(guide_grp[0], all_descendents=True)
	part_nodes = [n for n in nodes if cmds.objExists("{}.partType".format(n))]

	return [n for n in part_nodes
	        if cmds.getAttr("{}.partType".format(n)) == part_type] if part_type else part_nodes


def get_nodes_from_part(part):
	"""

	:param obj part:
	:return:
	"""
	guide_nodes = part.guide_nodes
	placers = [n for n in guide_nodes if cmds.attributeQuery("smrigGuidePlacer", n=n, ex=True)]
	pivots = [n for n in guide_nodes if cmds.attributeQuery("smrigGuideControlPivot", n=n, ex=True)]
	controls = [n for n in guide_nodes if cmds.attributeQuery("smrigGuideControl", n=n, ex=True)]
	geometry_shapes = cmds.listRelatives(part.guide_geometry_group, ad=1, type=["nurbsSurface", "nurbsCurve"]) or []
	geometry = [selectionlib.get_parent(n) for n in geometry_shapes]

	return part.guide_group, placers, pivots, controls, geometry, geometry_shapes


def get_guide_surfaces_from_part(part):
	"""

	:param obj part:
	:return:
	"""
	geometry_shapes = cmds.listRelatives(part.guide_geometry_group, ad=1, type=["nurbsSurface", "nurbsCurve"]) or []
	geometry = [selectionlib.get_parent(n) for n in geometry_shapes]
	geometry = [g for g in geometry if cmds.objExists(g + ".rbGuideSurface")]
	return geometry


def mirror_controls(s_controls, t_controls, mirror_mode, set_shapes, set_colors):
	"""
	mirrorpart controls and shapes

	:param list s_controls:
	:param list t_controls:
	:param bool set_shapes:
	:param bool set_colors:
	:param str mirror_mode:
	:return:
	"""
	for s_node, t_node in zip(s_controls, t_controls):
		if cmds.objExists(s_node + ".mirrorMode"):
			mode = cmds.getAttr(s_node + ".mirrorMode")
		else:
			mode = 0

		s_pivot = selectionlib.get_parent(s_node)
		t_pivot = selectionlib.get_parent(t_node)

		s_control = controlslib.Control(s_node)
		t_control = controlslib.Control(t_node)

		s_control_and_offsets = [s_node] + [n.path for n in s_control.offset_controls]
		t_control_and_offsets = [t_node] + [n.path for n in t_control.offset_controls]

		control_data = get_control_data(s_control_and_offsets)

		if mode == 0:
			trans, rot, scale = False, False, True
		elif mode == 1:
			trans, rot, scale = True, True, False
		else:
			trans, rot, scale = True, False, False

		transformslib.mirror.mirror_node(s_pivot, t_pivot, mirror=mirror_mode, translate=trans, rotate=rot, scale=scale)

		for sn, tn in zip(s_control_and_offsets, t_control_and_offsets):
			transformslib.mirror.mirror_node(sn, tn, mirror=mirror_mode, translate=trans, rotate=rot, scale=scale)

			if mode == 1:
				data = control_data.get(sn).get("shape")
				data = geometrylib.curve.mirror_curve_data(data, "x")
				data = geometrylib.curve.mirror_curve_data(data, "y")
				data = geometrylib.curve.mirror_curve_data(data, "z")
				control_data[sn]["shape"] = data

			control_data[tn] = control_data.get(sn)
			if sn in control_data.keys():
				del control_data[sn]

		set_control_data(control_data, set_shapes, set_colors)


def get_control_data(controls):
	"""
	Get dataexporter for control shapes and colors

	:param list controls:
	:return: dataexporter
	:rtype: dict
	"""
	control_shapes_data = {}
	for control_name in controls:
		control = controlslib.Control(control_name)
		crv_data = geometrylib.curve.extract_curve_creation_data(control.path)
		if crv_data:
			control_shapes_data[control_name] = {
				"color": control.color_string,
				"shape": geometrylib.curve.extract_curve_creation_data(control.path)
			}

	return control_shapes_data


def set_control_data(control_shapes_data, set_shape=True, set_color=True):
	"""
	Set shapes dataexporter

	:param dict control_shapes_data:
	:param bool set_shape:
	:param bool set_color:
	:return:
	"""

	for control, control_data in control_shapes_data.items():

		if ik_suffix in control:
			continue

		if not control_data:
			continue

		# validate control
		if not cmds.objExists(control):
			log.debug("Unable to load control shapes for control '{}', as it doesn't exist.".format(control))
			continue

		control = controlslib.Control(control)
		control_color = control_data.get("color")

		if set_shape:
			control_shape = control_data.get("shape")
			control.set_shape_data(control_shape)

		if set_color and control_color:
			control.set_color(control_color)


def get_guide_data(source_part, world_space=False):
	"""
	Get all pertineent dataexporter for building a guide.

	:param obj source_part:
	:param world_space:
	:return: guides dataexporter
	:rtype dict:
	"""
	guide_group, placers, pivots, controls, geometry, geometry_shapes = get_nodes_from_part(source_part)

	# get attrs from guide group
	attrs = cmds.listAttr(guide_group, k=1) + cmds.listAttr(guide_group, cb=1)
	attr_data = {a: cmds.getAttr("{}.{}".format(guide_group, a)) for a in attrs}

	# get transforms from all nodes
	transform_data = {}
	for node in [guide_group] + placers + pivots + controls + geometry:
		mirror_mode = cmds.getAttr(node + ".mirrorMode") if cmds.objExists(node + ".mirrorMode") else None
		offset_ctrls = cmds.getAttr(node + ".numOffsetControls") if cmds.objExists(
			node + ".numOffsetControls") else None

		transform_data[node] = {
			"translate": cmds.xform(node, q=1, ws=1, t=1) if world_space else cmds.getAttr(node + ".t")[0],
			"rotate": cmds.xform(node, q=1, ws=1, ro=1) if world_space else cmds.getAttr(node + ".r")[0],
			"scale": cmds.getAttr(node + ".s")[0],
			"rotate_order": cmds.getAttr(node + ".ro"),
			"mirror_mode": mirror_mode,
			"offset_ctrls": offset_ctrls}
	# build dict
	part_data = {
		"attrs": attr_data,
		"transforms": transform_data,
		"shapes": get_control_data(controls + geometry),
		"nodes": (guide_group, placers, pivots, controls, geometry, geometry_shapes)}

	return part_data


def set_guide_data(part_data, target_part=None, set_shapes=True, set_colors=True, world_space=False):
	"""
	Set guide dataexporter.

	:param dict part_data:
	:param obj target_part:
	:param bool set_shapes:
	:param bool set_colors:
	:param bool world_space:
	:return:
	"""
	node_set = get_nodes_from_part(target_part) if target_part else part_data["nodes"]
	t_guide_group, t_placers, t_pivots, t_controls, t_geometry, t_geometry_shapes = node_set
	s_guide_group, s_placers, s_pivots, s_controls, s_geometry, s_geometry_shapes = part_data["nodes"]

	# set attrs on guide node
	for attr, value in part_data.get("attrs").items():
		if cmds.objExists("{}.{}".format(t_guide_group, attr)):
			cmds.setAttr("{}.{}".format(t_guide_group, attr), value)

	# set scales on pivots controls and geometry transforms
	s_nodes = s_pivots + s_controls + s_geometry
	t_nodes = t_pivots + t_controls + t_geometry

	for s_node, t_node in zip(s_nodes, t_nodes):
		if cmds.objExists(t_node) and s_node in part_data.get("transforms").keys():
			if cmds.getAttr("{}.s".format(t_node), lock=False):

				try:
					cmds.setAttr("{}.s".format(t_node), *part_data.get("transforms").get(s_node).get("scale"))
				except:
					pass

	s_nodes = [s_guide_group] + s_placers + s_pivots + s_controls + s_geometry
	t_nodes = [t_guide_group] + t_placers + t_pivots + t_controls + t_geometry

	loop = 4 if world_space else 1
	for s_node, t_node in zip(s_nodes * loop, t_nodes * loop):
		if cmds.objExists(t_node) and s_node in part_data.get("transforms").keys():

			if cmds.getAttr("{}.ro".format(t_node), lock=False):
				try:
					cmds.setAttr(t_node + ".ro", part_data.get("transforms").get(s_node).get("rotate_order"))
				except:
					pass

			if cmds.objExists(t_node + ".mirrorMode"):
				try:
					cmds.setAttr(t_node + ".mirrorMode", part_data.get("transforms").get(s_node).get("mirror_mode"))
				except:
					pass

			if cmds.objExists(t_node + ".numOffsetControls"):
				try:
					cmds.setAttr(t_node + ".numOffsetControls",
					             part_data.get("transforms").get(s_node).get("offset_ctrls"))
				except:
					pass

			if cmds.getAttr("{}.t".format(t_node), lock=False):
				if world_space:
					cmds.xform(t_node, ws=1, t=part_data.get("transforms").get(s_node).get("translate"))
				else:
					try:
						cmds.setAttr(t_node + ".t", *part_data.get("transforms").get(s_node).get("translate"))
					except:
						pass

			if cmds.getAttr("{}.r".format(t_node), lock=False):
				if world_space:
					cmds.xform(t_node, ws=1, ro=part_data.get("transforms").get(s_node).get("rotate"))
				else:
					try:
						cmds.setAttr(t_node + ".r", *part_data.get("transforms").get(s_node).get("rotate"))
					except:
						pass

	# set curve shapes and colors
	control_data = dict(part_data.get("shapes"))
	if target_part:
		for s_control, t_control in zip(s_controls, t_controls):
			control_data[t_control] = control_data.get(s_control)
			del control_data[s_control]

	set_control_data(control_data, set_shapes, set_colors)

	return node_set


def find_guide_group_from_selection(node=None):
	"""
	Find guide node from selecion or node
	:param str/None node:
	:return: Guide node
	:rtype: str
	"""
	selection = cmds.ls(node) if node else cmds.ls(sl=1)
	if not selection:
		log.debug("Node or selection not specified")
		return ""

	for node in reversed(selectionlib.get_parents(selection[0]) + [selection[0]]):
		if cmds.objExists("{}.smrigGuideGroup".format(node)):
			return node
