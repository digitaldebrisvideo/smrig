import logging
import os

from maya import cmds
from maya import mel

from smrig.lib import decoratorslib
from smrig.lib import geometrylib
from smrig.lib import mathlib
from smrig.lib import nodeslib
from smrig.lib.controlslib import io_file

log = logging.getLogger("smrig.lib.controlslib.library")

CONTROL_LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "bin")
CONTROL_LIBRARY_ICONS_PATH = os.path.join(CONTROL_LIBRARY_PATH, "icons")


@decoratorslib.memoize
def get_control_shape_library():
	"""
	:return: Control shape library
	:rtype: dict
	"""
	return io_file.load_control_shapes_from_directory(CONTROL_LIBRARY_PATH)


def get_control_shape(shape):
	"""
	Get the control shape from the library.

	:param str shape:
	:return: Control shape dataexporter
	:rtype: dict
	:raise ValueError: When the control shape doesn't exist in the library.
	"""
	control_shape_library = get_control_shape_library()
	control_shape_data = control_shape_library.get(shape)
	if not control_shape_data:
		error_message = "Control shape '{}' doesn't exist in the library, options are {}".format(
			shape,
			control_shape_library.keys()
		)

		log.error(error_message)
		raise ValueError(error_message)

	return control_shape_data


def get_all_control_shapes(print_list=False):
	"""
	:return: All available control shape names
	:rtype: list
	"""
	control_shapes = get_control_shape_library().keys()
	control_shapes.sort()

	if print_list:
		log.info("Valid control shapes")
		for shape in control_shapes:
			print("\t{}".format(shape))

	return control_shapes


def save_control_shape(name, control, note=None, normalize=True, create_icon=True):
	"""
	Save the control shape to the library using the provided key as a name.
	The name will be processed to make sure its friendly for saving. By default
	the controls will be normalized to fit a -1 to 1 cube.

	:param str name:
	:param str control:
	:param str note:
	:param str icon:
	:param bool normalize:
	"""
	# confirm name
	name_conform = name.lower()
	name_conform = name_conform.replace(" ", "-")
	name_conform = name_conform.replace("_", "-")

	icon = save_control_icon(name, control) if create_icon else None

	# validate name
	if name != name_conform:
		warning_message = "Provided name '{}' doesn't match conformed name '{}'.".format(name, name_conform)
		log.warning(warning_message)

	# get control dataexporter
	control_shape_data = geometrylib.curve.extract_curve_creation_data(control)

	# normalize point dataexporter
	if normalize:
		for i, data in enumerate(control_shape_data):
			# get point dataexporter
			points = data.get("point")
			bounding_box = mathlib.get_bounding_box(points)
			scale_factor = 1.0 / max([abs(bb) for bb in bounding_box])

			# set point dataexporter
			control_shape_data[i]["point"] = [
				[p * scale_factor for p in point]
				for point in points
			]

	# save to disk
	file_path = os.path.join(CONTROL_LIBRARY_PATH, "{}.json".format(name_conform))
	control_shape_data = {
		name_conform: {
			"shape": control_shape_data,
			"note": note or "",
			"icon": icon or ""
		}
	}

	io_file.save_control_shapes_to_file(file_path, control_shape_data)


def save_control_icon(name, control):
	"""
	Save a png to icon bin.

	:param control:
	:return:
	"""
	nodeslib.display.set_display_color(control, 16, shapes_only=False)

	file_path = os.path.join(CONTROL_LIBRARY_ICONS_PATH, name + ".png")
	mel.eval("FrameSelectedWithoutChildren")
	cmds.select(cl=True)
	cmds.refresh()

	cmds.playblast(fr=cmds.currentTime(q=1), cf=file_path,
	               format='image',
	               clearCache=0,
	               viewer=0,
	               showOrnaments=0,
	               offScreen=1,
	               percent=100,
	               compression='png',
	               quality=25,
	               widthHeight=[64, 64])

	return file_path
