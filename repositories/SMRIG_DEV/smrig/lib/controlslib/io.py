import logging

import maya.cmds as cmds

from smrig.lib import geometrylib
from smrig.lib import nodepathlib
from smrig.lib.controlslib import common
from smrig.lib.controlslib.io_file import *

log = logging.getLogger("smrig.lib.controlslib.io")


def save_control_shapes(file_path, controls):
	"""
	Save the shapes of the provided controls into a json file provided in the
	file_path variable. This file can be used later to restore the control
	shapes.

	:param str file_path:
	:param list controls:
	"""
	# variable
	control_shapes_data = {}

	# loop controls
	for control in controls:
		# initialize control
		if not isinstance(control, common.Control):
			control = common.Control(control)

		# store dataexporter
		control_name = str(nodepathlib.get_leaf_name(control.path))
		control_shapes_data[control_name] = {
			"color": control.color_string,
			"shape": geometrylib.curve.extract_curve_creation_data(control.path)
		}

	# save to disk
	save_control_shapes_to_file(file_path, control_shapes_data)


def save_control_shapes_wildcard(file_path, search="*_CTL"):
	"""
	Save the controls found based on the wild card provided in the search
	variable.

	:param str search:
	:param str file_path:
	:raise ValueError: When the wildcard contains no matches.
	"""
	# get controls
	controls = cmds.ls(search, l=True)

	# validate controls
	if not controls:
		error_message = "Wildcard '{}' provided no matches in the scene.".format(search)
		log.error(error_message)
		raise ValueError(error_message)

	# save control shapes
	save_control_shapes(file_path, controls)


def load_control_shapes(file_path, set_shape=True, set_color=True):
	"""
	Load the shapes stored in the json file path. It will delete existing
	shapes underneath the controls.

	:param bool set_shape:
	:param bool set_color:
	:param str file_path:
	:raise ValueError: When both shape and color are not meant to be set.
	"""
	# validate
	if not set_shape and not set_color:
		error_message = "Either color/shape or both have to be set."
		log.error(error_message)
		raise ValueError(error_message)

	# load from disk
	control_shapes_data = load_control_shapes_from_file(file_path)

	# replace curves
	for control, control_data in control_shapes_data.items():
		# validate control
		if not cmds.objExists(control):
			log.warning("Unable to load control shapes for control '{}', as it doesn't exist.".format(control))
			continue

		control = common.Control(control)
		control_color = control_data.get("color")

		if set_shape:
			control_shape = control_data.get("shape")
			control.set_shape_data(control_shape)

		if set_color and control_color:
			control.set_color(control_color)
