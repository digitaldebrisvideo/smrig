import os

from smrig.lib import pathlib

try:
	import _pickle as pickle
except:
	import cPickle as pickle

import logging

log = logging.getLogger("smrig.lib.iolib.pickle")


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

	with open(file_path, "rb") as f:
		result = pickle.load(f)
		log.debug("Read pickle dataexporter from '{}'.".format(file_path))
		return result


def write(file_path, data):
	"""
	:param str file_path:
	:param int/float/str/dict/list data:
	"""
	directory = os.path.dirname(file_path)
	pathlib.make_dirs(directory)

	with open(file_path, "wb") as f:
		# pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
		pickle.dump(data, f, -1)

	pathlib.change_permission(file_path)
	log.debug("Saved pickled dataexporter to '{}'.".format(file_path))
