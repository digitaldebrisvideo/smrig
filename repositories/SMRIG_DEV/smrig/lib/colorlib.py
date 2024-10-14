import logging

from maya import cmds

from smrig import env
from smrig.lib import mathlib, nodeslib, utilslib

log = logging.getLogger("smrig.lib.colorlib")

COLOR_NAMES = {
	"none": 0, "black": 1, "darkgrey": 2, "lightgrey": 3, "darkred": 4,
	"darkblue": 5, "blue": 6, "darkgreen": 7, "darkpurple": 8, "brightpink": 9,
	"darkorange": 10, "darkbrown": 11, "mediumred": 12, "red": 13, "green": 14,
	"mediumblue": 15, "white": 16, "yellow": 17, "lightblue": 18, "lightgreen": 19,
	"pink": 20, "lightbrown": 21, "lightyellow": 22, "mediumgreen": 23, "brown": 24,
	"darkyellow": 25, "leafgreen": 26, "mintgreen": 27, "turquoise": 28, "navyblue": 29,
	"purple": 30, "winered": 31,
}

COLOR_SIDE_MAPPER = {
	env.prefs.get_sides()[0]: ["green", "mediumgreen", "lightblue", "mediumgreen", "green"],
	env.prefs.get_sides()[1]: ["red", "mediumred", "pink", "mediumred", "red"],
	env.prefs.get_sides()[2]: ["yellow", "lightbrown", "brown", "pink", "yellow"],
}


def get_colors_from_side(side):
	"""
	Get the primary, secondary, detail and fk color names from a side. If a
	side is not defined the default colors will be returned and a warning
	message displayed.

	:param str side:
	:return: Primary, secondary, detail and FK color names
	:rtype: list
	"""
	key = [k for k in COLOR_SIDE_MAPPER.keys() if k in side]
	if key:
		colors = COLOR_SIDE_MAPPER.get(key[0])

	else:
		warning_message = "No color mapping found for side '{}', options are {}.".format(
			side,
			COLOR_SIDE_MAPPER.keys()
		)
		log.warning(warning_message)
		colors = COLOR_SIDE_MAPPER.get("C")

	return colors


def get_color_index_from_name(name):
	"""
	Get the color index that can be used as a index color override in the
	drawing overrides menu.

	:param str name:
	:return: color index
	:rtype: int
	"""
	index = COLOR_NAMES.get(name)

	if index is None:
		error_message = "No color index is linked to name '{}'.".format(name)
		for key in COLOR_NAMES.keys():
			log.info(key)
		log.error(error_message)
		raise ValueError(error_message)

	return index


def get_color_name_from_index(index):
	"""
	Get the color name from an index. The index relates to the color override
	attribute in the drawing overrides menu.

	:param int/None index:
	:return: color name
	:rtype: str
	"""
	name = list(COLOR_NAMES.keys())[list(COLOR_NAMES.values()).index(index)]

	if name is None:
		error_message = "No color name is linked to index '{}'.".format(index)
		log.error(error_message)
		raise ValueError(error_message)

	return name


def get_color_rbg_from_index(index, color_range=(0, 1)):
	"""
	Get the color rgb value from a color index. The cmds.colorIndex command
	will be used to retrieve the RGB value. The value for grey does not exist
	and will be returned manually.

	:param int index:
	:param tuple color_range:
	:return: color RGB
	:rtype: list
	"""
	color_rgb = [0.5, 0.5, 0.5] if index == 0 else cmds.colorIndex(index, query=True)
	color_rgb = [mathlib.remap(v, 0, 1, *color_range) for v in color_rgb]
	return color_rgb


def get_all_colors():
	"""
	:return: All available color names
	:rtype: list
	"""
	colors = COLOR_NAMES.keys()
	colors.sort()
	return colors


def set_color(nodes, color, shape_only=False):
	"""

	:param color:
	:param shape_only:
	:return:
	"""
	if not isinstance(color, int):
		color = get_color_index_from_name(color)

	for node in utilslib.conversion.as_list(nodes):
		nodeslib.display.set_display_color(node, color, shapes_only=shape_only)
