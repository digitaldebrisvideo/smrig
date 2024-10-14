import json
import logging
import os
import re
import stat
import subprocess
import sys

# Compatibility for string types in both Python 2 and Python 3
if sys.version_info[0] < 3:
	string_types = (str, unicode)
else:
	string_types = (str,)

log = logging.getLogger ("smrig.env.utils")

FILE_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH
RE_ILLEGAL_CHARACTERS = re.compile ("[^a-zA-Z0-9#_]")
RE_UNDERSCORE_DUPLICATE = re.compile ("_+")

'''
class Singleton(type):
    """
    a singleton. Use as a decorator for python 2 and 3 compatability
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
'''


def singleton(class_):
	"""
	a singleton. Use as a decorator for python 2 and 3 compatability
	"""
	instances = {}

	def get_instance(*args, **kwargs):
		if class_ not in instances:
			instances[class_] = class_(*args, **kwargs)
		return instances[class_]

	return get_instance


def normpath(path):
	"""
	Converts "\\" to "/" in path string.

	:param str path:
	:return:
	"""
	return path.replace("\\", "/")


def join(*args):
	"""
	Wrapper for os.path.join with "\\" converted to "/"
	:param args:
	:return:
	"""
	return normpath(os.path.join(*args))


def make_dirs(paths):
	"""
	:param str/list paths:
	"""
	paths = conversion_as_list(paths)
	for path in paths:
		if os.path.exists(path):
			continue

		os.makedirs(path)
		log.debug("Created directory: {}.".format(path))


def read_json(file_path):
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


def write_json(file_path, data):
	"""
	:param str file_path:
	:param int/float/str/dict/list data:
	"""
	directory = os.path.dirname(file_path)
	make_dirs(directory)

	with open(file_path, "w") as f:
		json.dump(data, f, indent=4, sort_keys=True)

	change_permission(file_path)
	log.debug("Saved json dataexporter to '{}'.".format(file_path))


def change_permission(path):
	"""
	Change permissions on already created files to be readable and writable
	by everyone. You'll need permissions first of course. When this command
	is used on a windows machine it will be ignored but a info message
	notifies the user.

	:param str path:
	"""
	# TODO: allow permission input, need to be a util?
	if sys.platform != "win32":
		os.chmod(path, FILE_PERMISSIONS)


def conversion_as_list(data):
	"""
	Convert any dataexporter into a list.

	:param str/list/tuple/None data:
	:return: Selection
	:rtype: list
	:raise ValueError: When the provided type is not supported
	"""
	if data is None:
		return []
	elif isinstance(data, string_types):
		return [data]
	elif isinstance(data, list):
		return data
	elif isinstance(data, tuple):
		return list(data)

	error_message = "Unable to convert type '{}' to list.".format(type(data))
	log.error(error_message, exc_info=1)
	raise ValueError(error_message)


def construct_name(*name):
	"""
	Construct the provided name so it doesn't contain any characters other
	than a-z, A-Z, 0-9, # and _. Illegal characters will be replaced with an
	underscore after which any starting, ending or duplicating of underscores
	will be removed.

	:param name:
	:return: Constructed name
	:rtype: str
	"""
	# TODO: handle capitalization?
	# TODO: handle suffixes?

	# construct name
	name = "_".join([n for n in name if n])

	# conform name
	name_conformed = name
	name_conformed = RE_ILLEGAL_CHARACTERS.sub("_", name_conformed)
	name_conformed = RE_UNDERSCORE_DUPLICATE.sub("_", name_conformed)
	name_conformed = name_conformed.strip("_")

	# debug conforming
	if name != name_conformed:
		log.debug("Conformed provided name '{}' to '{}'.".format(name, name_conformed))

	return name_conformed


def get_hash():
	"""
	Return smrig git hash.

	:return:
	"""

	try:
		os.chdir(os.path.dirname(__file__))
		hash = subprocess.check_output(["git", "describe", "--always"]).strip().decode()
		print("# smrig git hash: {}".format(hash))

		return hash
	except:
		print("info")
		return None
