import json
import logging
import os

from smrig.lib import pathlib

log = logging.getLogger("smrig.lib.iolib.json")


def read(file_path):
	"""
	:param str file_path:
	:return: JSON dataexporter
	:raise OSError: When the provided file path doesn't exist.
	"""
	if not os.path.exists(file_path):
		error_message = "File path '{}' doesn't exist on disk".format(file_path)
		log.error(error_message)
		raise OSError(error_message)

	with open(file_path, "r") as f:
		result = json.load(f)
		log.debug("Read json dataexporter from '{}'.".format(file_path))
		return result


def write(file_path, data):
	"""
	:param str file_path:
	:param int/float/str/dict/list data:
	"""
	directory = os.path.dirname(file_path)
	pathlib.make_dirs(directory)

	with open(file_path, "w") as f:
		json.dump(data, f, indent=4, sort_keys=True)

	pathlib.change_permission(file_path)
	log.debug("Saved json dataexporter to '{}'.".format(file_path))
