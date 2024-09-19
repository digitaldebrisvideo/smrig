import json
import logging
import os
import string

import maya.cmds as cmds
from smrig.dataioo import utils

try:
	# python 3
	import _pickle as pickle

except:
	# python 2.7
	import cPickle as pickle

log = logging.getLogger("deformerIO.io")


def make_dirs(paths):
	"""
	:param str/list paths:
	"""
	paths = utils.as_list(paths)
	for path in paths:
		if os.path.exists(path):
			continue

		os.makedirs(path)
		log.debug("Created directory: {}.".format(path))


def read_json(file_path):
	"""
	:param str file_path:
	:return: JSON deformerIO
	:raise OSError: When the provided file path doesn't exist.
	"""
	if not os.path.exists(file_path):
		error_message = "File path '{}' doesn't exist on disk".format(file_path)
		log.error(error_message)
		raise OSError(error_message)

	with open(file_path, "r") as f:
		result = json.load(f)
		log.debug("Read json data from '{}'.".format(file_path))
		return result


def write_json(file_path, data):
	"""
	:param str file_path:
	:param int/float/str/dict/list data:
	"""
	directory = os.path.dirname(file_path)
	make_dirs(directory)

	with open(file_path, "w") as f:
		json.dump(data, f, indent=4, sort_keys=True)

	log.debug("Saved json data to '{}'.".format(file_path))


def read_pickle(file_path):
	"""
	:param str file_path:
	:return: JSON deformerIO
	:raise OSError: When the provided file path doesn't exist.
	"""
	if not os.path.exists(file_path):
		error_message = "File path '{}' doesn't exist on disk".format(file_path)
		log.error(error_message)
		raise OSError(error_message)

	with open(file_path, "rb") as f:
		result = pickle.load(f)
		log.debug("Read pickle data from '{}'.".format(file_path))
		return result


def write_pickle(file_path, data):
	"""
	:param str file_path:
	:param int/float/str/dict/list data:
	"""
	directory = os.path.dirname(file_path)
	make_dirs(directory)

	with open(file_path, "wb") as f:
		try:
			pickle.dump(data, f, protocol=2)
		except:
			pickle.dump(data, f)

	log.debug("Saved pickled data to '{}'.".format(file_path))


def save_maya_file(file_path, nodes):
	"""

	:param file_path:
	:param nodes:
	:return:
	"""
	cmds.select(nodes)
	os.rename(cmds.file(file_path, f=1, op="", typ="mayaBinary", es=True), file_path)
	utils.delete_export_data_nodes()


def load_maya_file(file_path):
	"""

	:param file_path:
	:return:
	"""
	# import the file
	snapshot = cmds.ls()
	try:
		imported_nodes = cmds.file(file_path, i=1, rnn=1, pmt=0, iv=1)
	except:
		imported_nodes = [n for n in cmds.ls() if n not in snapshot]

	try:
		data_node = utils.get_export_data_nodes(imported_nodes)
		data = eval(cmds.getAttr(data_node[0] + ".exportData"))
		data["imported_nodes"] = imported_nodes
	except:
		data = {"imported_nodes": imported_nodes}

	return data


def write_file(file_path, data):
	"""
	Wrapper for writing either json or pickle based on file ext

	:param file_path:
	:param data:
	:return:
	"""
	if file_path.endswith(".pickle"):
		write_pickle(file_path, data)
	else:
		write_json(file_path, data)


def read_file(file_path):
	"""
	Wrapper for reading either json or pickle based on file ext


	:param file_path:
	:return:
	"""
	utils.delete_export_data_nodes()

	if file_path.endswith(".pickle"):
		return read_pickle(file_path)

	elif file_path.endswith(".json"):
		return read_json(file_path)

	elif file_path.endswith(".mb"):
		return load_maya_file(file_path)


def browser(action="import", extension=None, start_dir=None):
	"""
	:param action: Options are import, export
	:param str/None extension: file filter by file extension
	:param str start_dir: starting directory
	:return:
	"""
	extension = utils.as_list(extension)
	extension = extension if extension else ["json", "pickle", "mb", "pose"]

	fp = " ".join(["*.{}"] * len(extension))
	file_filter = "Weights Data ({})".format(fp).format(*extension)

	if action == "import":
		file_mode = 1
	elif action == "import multiple":
		file_mode = 4
	elif action == "export multiple":
		file_mode = 3
	else:
		file_mode = 0

	if start_dir:
		file_path = cmds.fileDialog2(fileFilter=file_filter, dir=start_dir, dialogStyle=2, okc=string.capwords(action),
		                             fm=file_mode)
	else:
		file_path = cmds.fileDialog2(fileFilter=file_filter, dialogStyle=2, okc=string.capwords(action), fm=file_mode)

	if file_path and file_mode in [0, 1]:
		return file_path[0]

	return file_path
