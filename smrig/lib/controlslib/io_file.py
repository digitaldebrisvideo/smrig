import logging
import os

from smrig.lib import iolib

log = logging.getLogger("smrig.lib.controlslib.io_file")

__all__ = [
	"save_control_shapes_to_file",
	"load_control_shapes_from_file",
	"load_control_shapes_from_directory"
]


def save_control_shapes_to_file(file_path, control_shapes_data):
	"""
	:param str file_path:
	:param dict control_shapes_data:
	"""
	# create directory to path if it doesn't exist
	directory = os.path.dirname(file_path)
	if not os.path.exists(directory):
		os.makedirs(directory)

	iolib.json.write(file_path, control_shapes_data)
	log.info("Saved control shapes file: '{}'.".format(file_path))


def load_control_shapes_from_file(file_path):
	"""
	:param str file_path:
	:return: Control shapes dataexporter
	:rtype: dict
	:raise OSError: If the file path doesn't exist.
	"""
	if not os.path.exists(file_path):
		error_message = "File path '{}' doesn't exist.".format(file_path)
		log.error(error_message)
		raise OSError(error_message)

	# load from disk
	return iolib.json.read(file_path)


def load_control_shapes_from_directory(directory):
	"""
	:param str directory:
	:return: Control shapes dataexporter
	:rtype: dict
	:raise OSError: If the directory doesn't exist.
	"""
	if not os.path.exists(directory):
		error_message = "Directory '{}' doesn't exist.".format(directory)
		log.error(error_message)
		raise OSError(error_message)

	data = {}
	for f in os.listdir(directory):
		if not f.endswith("json"):
			continue

		file_path = os.path.join(directory, f)
		control_shape_data = load_control_shapes_from_file(file_path)
		data.update(control_shape_data)

	return data
