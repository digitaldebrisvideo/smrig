import glob
import logging
import os
import re
import stat
import subprocess
import sys
import webbrowser

from smrig.env import prefs
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.pathlib")

FILE_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH

VERSION_STRING = "v{:03d}"
VERSION_GLOB_STRING = "v[0-9][0-9][0-9]".format(VERSION_STRING)
VERSION_RE_STRING = r"v([0-9][0-9][0-9])"


def join(*args):
	"""
	Wrapper for os.path.join with "\\" converted to "/"
	:param args:
	:return:
	"""
	return normpath(os.path.join(*args))


def normpath(path):
	"""
	Converts "\\" to "/" in path string.

	:param str path:
	:return:
	"""
	return path.replace("\\", "/")


def make_dirs(paths):
	"""
	:param str/list paths:
	"""
	paths = utilslib.conversion.as_list(paths)
	for path in paths:
		if os.path.exists(path):
			continue

		os.makedirs(path)
		log.debug("Created directory: {}.".format(path))


def change_permission(path):
	"""
	Change permissions on already created files to be readable and writable
	by everyone. You'll need permissions first of course. When this command
	is used on a windows machine it will be ignored but a info message
	notifies the user.

	:param str path:
	"""
	# TODO: allow permission input, need to be a util?
	if sys.platform == "win32":
		log.debug("Warning: Unable to change permissions on '{}' on windows.".format(path))
		return

	os.chmod(path, FILE_PERMISSIONS)


def create_sym_link(source, destination, remove_existing=False):
	"""
	Create a symlink from the source to the destination. If the destination
	exists and the remove existing is disabled an OSError will be raised. If
	remove existing is allowed it will delete the destination path and perform
	the sym link creation after.

	:param str source:
	:param str destination:
	:param bool remove_existing:
	:raise OSError: When the source doesn't exist
	:raise OSError: When the destination exists and is not allowed to be removed.
	"""
	if not os.path.exists(source):
		error_message = "Source '{}' doesn't exist, cannot create symlink".format(source)
		log.error(error_message)
		raise OSError(error_message)

	if os.path.exists(destination):
		if not remove_existing:
			error_message = "Destination '{}' already exists, specify " \
			                "'remove_existing' if you would like to remove it".format(destination)

			log.error(error_message)
			raise OSError(error_message)
		else:
			os.remove(destination)

	os.symlink(source, destination)


# ----------------------------------------------------------------------------


def get_files(directory, search="*v"):
	"""
	Get a sorted list of all files in a directory that match the search
	string. Ideally used to find versioned files in the same folder.

	:param str directory:
	:param str search:
	"""
	files = glob.glob(os.path.join(directory, search))
	files.sort()

	return [
		join(directory, f)
		for f in files
	]


# ----------------------------------------------------------------------------


def open_in_text_editor(file_path):
	"""
	:param file_path:
	:raise OSError: When the file path doesn't exist
	"""
	if not os.path.exists(file_path):
		error_message = "File path '{}' doesn't exist, cannot be opened".format(file_path)
		log.warning(error_message)

	if sys.platform == "darwin":
		os.system("open {} ".format(file_path))

	elif sys.platform == "win32":
		os.system("{} {}".format(prefs.get_editor(), file_path))

	else:
		webbrowser.open(file_path)


def open_in_browser(directory):
	"""
	Open the provided directory in the file browser, this function will
	support multiple OS.

	:param str directory:
	:raise ValueError: When the provided directory is not a directory.
	"""
	if not os.path.isdir(directory):
		error_message = "Provided directory '{}' is not a directory.".format(directory)
		log.error(error_message)
		raise ValueError(error_message)

	if sys.platform == "linux2":
		subprocess.check_call(("xdg-open", directory))

	elif sys.platform == "darwin":
		subprocess.check_call(["open", "-R", directory])

	elif sys.platform == "win32":
		directory = os.path.normpath(directory)
		subprocess.Popen('explorer "{0}"'.format(directory))


def strip_ext(base_name):
	"""
	Strip file extension

	:param base_name:
	:return:
	"""
	return os.path.splitext(base_name)[0]


def split_path(path):
	"""
	Split into dir name and base name

	:param path:
	:return:
	:rtype: list
	"""
	return os.path.dirname(path), os.path.basename(path)


# ----------------------------------------------------------------------------


class Version(object):
	"""
	The Version class can be used to manage versioning of file paths or
	directories. It'll allow for querying of specific version paths using an
	integer or the latest available for easy access. It is also possible to
	generate a new version in case you would like to save a new file.

	:param str directory:
	:param str/None file_name:
	:param str/None file_ext:
	"""

	def __init__(self, directory, file_name=None, file_ext=None):
		self._directory = directory
		self._file_name = (file_name if not file_name or file_name.endswith("_") else "{}_".format(file_name)) or ""
		self._file_extension = (file_ext if not file_ext or file_ext.startswith(".") else ".{}".format(file_ext)) or ""
		self._glob_string = "{}{}{}".format(self._file_name, VERSION_GLOB_STRING, self._file_extension)

	# ------------------------------------------------------------------------

	@property
	def directory(self):
		"""
		:return: Directory
		:rtype: str
		"""
		return self._directory

	@property
	def file_name(self):
		"""
		:return: File name
		:rtype: str/None
		"""
		return self._file_name

	@property
	def file_extension(self):
		"""
		:return: File extension
		:rtype: str/None
		"""
		return self._file_extension

	# ------------------------------------------------------------------------

	def construct_version_path(self, version):
		"""
		:param int version:
		:return: Path to specific version
		:rtype: str
		"""
		version_string = VERSION_STRING.format(version)
		file_name = "{}{}{}".format(self.file_name, version_string, self.file_extension)
		return os.path.join(self.directory, file_name)

	@staticmethod
	def get_version_index(path):
		"""
		:param str path:
		:return: Version index
		:rtype: int
		:raise ValueError: When no version index can be found in the path.
		"""
		search = re.search(VERSION_RE_STRING, path)
		if not search:
			error_message = "Unable to extract version index from path " \
			                "'{}' using regex'{}'.".format(path, VERSION_RE_STRING)
			log.error(error_message)
			raise ValueError(error_message)

		return int(search.group(1))

	# ------------------------------------------------------------------------

	def get_load_version_path(self, version=None):
		"""
		Construct the version path and see if that path exists. If it doesn't
		a RuntimeError will be raised. This method is ideally used when
		loading of files to have that error checking in place when the version
		requested doesn't exist.

		:param int/None version:
		:return: Version path
		:rtype: str
		:raise RuntimeError: When specific version path cannot be found
		"""
		# get path
		if version is None:
			version_path = self.get_latest_version_path()
		else:
			version_path = self.construct_version_path(version)

		# validate path
		if not version_path or not os.path.exists(version_path):
			error_message = "Constructed path '{}' using version '{}' doesn't exist.".format(version_path, version)
			log.warning(error_message)
			return

		return version_path

	def get_save_version_path(self, version=None, new_version=False):
		"""
		Construct a version path using version and new version variable. This
		method can be used for saving of paths. It will not raise error if the
		path doesn't exist on disk.

		:param int/None version:
		:param bool new_version:
		:return: Version path
		:rtype: str
		"""
		if version is not None:
			return self.construct_version_path(version)

		version_path = self.get_latest_version_path()
		if not version_path:
			return self.construct_version_path(1)
		elif not new_version:
			return version_path
		else:
			version = self.get_version_index(version_path)
			return self.construct_version_path(version + 1)

	# ------------------------------------------------------------------------

	def get_latest_version_path(self):
		"""
		Get latest version path searching the directory using the glob search
		string. The files will be sorted and the full path to the latest
		version returned. If no files are found a None type will be returned.

		:return: Latest version path
		:rtype: str/None
		"""
		# get files
		files = get_files(self._directory, self._glob_string)
		files.sort()
		files.reverse()

		return utilslib.conversion.get_first(files)

	def get_new_version_path(self):
		"""
		Get a new version path by querying the latest version and increasing
		its version by one. A new path is constructed using the new version.
		If no latest version path is found it means that no versions have been
		created yet meaning the new version is version 1.

		:return: New version path
		:rtype: str
		"""
		version = 1
		version_path = self.get_latest_version_path()

		if version_path:
			version = self.get_version_index(version_path)
			version += 1

		return self.construct_version_path(version)

	def get_versions(self, as_integers=False):
		"""
		:return:
		"""
		files = get_files(self._directory, self._glob_string)
		if as_integers:
			return [int(f.split("_")[-1].split(".")[0].replace("v", "")) for f in reversed(files)]

		else:
			return [f.split("_")[-1].split(".")[0] for f in reversed(files)]
