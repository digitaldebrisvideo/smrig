import logging
import os

import maya.cmds as cmds

from smrig.env import utils
from smrig.env.constants import TYPE_SUFFIX
from smrig.userprefs import PATH_TEMPLATE, DEFAULT_EDITOR, DEFAULT_FILE_TYPE

log = logging.getLogger("smrig.env.prefs")

# system constant variables - DO NOT EDIT THESE - user prefs are now in smrig.env.userprefs.py

SYSTEM_PATH = utils.normpath(os.path.dirname(os.path.dirname(utils.__file__)))
PARTS_LIB_PATHS = [os.path.join(SYSTEM_PATH, "partslib")]
PREF_FILE = utils.join(cmds.internalVar(upd=True), "smrig.prefs")
SANDBOX_TEMPLATE = utils.join(cmds.internalVar(uwd=True), "{job}", "assets", "{asset}", "{user}", "rigbuild")
NAME_TEMPLATE = "{side}_{name}_{token1}{index1}_{token2}{index2}_{token3}{index3}_{unique_index}_{suffix}"
SIDES_DICT = {"left": "L", "right": "R", "center": "C"}
CAPITALIZE_SIDE = True
CAPITALIZE_SUFFIX = True
CACHE_DIRECTORY = utils.normpath(cmds.internalVar(utd=True))
CACHE = False
DEBUG_MODE = False
USE_NUMERICAL_INDEX = True
DEFAULT_FILE_TYPE = DEFAULT_FILE_TYPE


@utils.singleton
class Prefs():

	def __init__(self):
		self.reset()
		self.load()

	def __str__(self):
		data = self.data_dict
		return "\n".join(["{}: {}".format(k, data[k]) for k in sorted(data.keys()) if k != "type_suffix"])

	def __repr__(self):
		data = self.data_dict
		return "\n".join(["{}: {}".format(k, data[k]) for k in sorted(data.keys()) if k != "type_suffix"])

	# ------------------------------------------------------------------------

	@property
	def data_dict(self):
		"""
		Prefs in dict form.

		:return:
		:rtype: dict
		"""
		return {
			"name_template": self._name_template,
			"path_template": self._path_template,
			"sandbox_path_template": self._sandbox_path_template,
			"cache_directory": self._cache_directory,
			"cache": self._cache,
			"debug_mode": self._debug_mode,
			"capitalize_side": self._capitalize_side,
			"capitalize_suffix": self._capitalize_suffix,
			"side_tokens": self._side_tokens,
			"type_suffix": self._type_suffix,
			"use_numerical_index": self._use_numerical_index,
			"partslib_paths": self._partslib_paths,
			"editor": self._default_editor
		}

	def set_suffix(self, **kwargs):
		"""
		Update node type suffix values
		:param dict kwargs:
		:return:
		"""
		self._type_suffix.update({k: str(v).upper() for k, v in kwargs.items()})

	def get_suffix(self, node_type):
		"""
		Update node type suffix values
		:param dict kwargs:
		:return:
		"""
		return self._type_suffix.get(node_type, "")

	# ------------------------------------------------------------------------
	def get_sides(self):
		"""
		Get all side tokens.

		:return: In order: [left, right, center] tokens.
		:rtype: list
		"""
		sides = [self._side_tokens.get('left'), self._side_tokens.get('right'), self._side_tokens.get('center')]
		sides = [s.upper() if self.get_capitalize_side() else s.lower() for s in sides]
		return sides

	def get_side(self, key):
		"""
		Get side token.

		:param str key:
		:return: side token
		:rtype: str
		"""
		side = self._side_tokens.get(key, "")
		return side.upper() if self.get_capitalize_side() else side.lower()

	def set_side(self, **kwargs):
		"""
		Update side token dict values.
		:param dict kwargs:
		:return:
		"""
		self._side_tokens.update({k: str(v).upper() for k, v in kwargs.items()})

	# ------------------------------------------------------------------------

	def get_use_numerical_index(self):
		"""
		Get use numbers instead of letters for indexing node names.

		:return:
		:rtype: bool
		"""
		return self._use_numerical_index

	def set_use_numerical_index(self, value):
		"""
		set use numbers instead of letters for indexing node names.

		:param bool value:
		:return:
		"""
		self._use_numerical_index = bool(value)

	# ------------------------------------------------------------------------

	def get_capitalize_side(self):
		"""
		Use caps for side token.

		:return:
		:rtype: bool
		"""
		return self._capitalize_side

	def set_capitalize_side(self, value):
		"""
		Set use caps for side token.

		:param bool value:
		:return:
		"""
		self._capitalize_side = bool(value)

	# ------------------------------------------------------------------------

	def get_capitalize_suffix(self):
		"""
		Use caps for suffix token.

		:return:
		:rtype: bool
		"""
		return self._capitalize_suffix

	def set_capitalize_suffix(self, value):
		"""
		Set use caps for suffix token.

		:param bool value:
		:return:
		"""
		self._capitalize_suffix = bool(value)

	# ------------------------------------------------------------------------

	def get_name_template(self):
		"""
		:return: Name template
		:rtype: str
		"""
		return self._name_template

	def set_name_template(self, template):
		"""
		Node name template.

		Example:
			.. code-block:: python
				set_name_template("{side}_{name}_{token1}{index1}_{token2}{index2}_{suffix}")

		:param str template:
		"""
		self._name_template = template

	# ------------------------------------------------------------------------
	def get_editor(self):
		"""

		:return:
		"""
		return self._default_editor

	def get_path_template(self):
		"""
		:return: Path template
		:rtype: str
		"""
		return utils.normpath(self._path_template)

	def set_path_template(self, template):
		"""
		:param str template:
		"""
		self._path_template = utils.normpath(template)

	# ------------------------------------------------------------------------

	def get_sandbox_path_template(self):
		"""
		:return: Path template
		:rtype: str
		"""
		return utils.normpath(self._sandbox_path_template)

	def set_sandbox_path_template(self, template):
		"""
		:param str template:
		"""
		self._sandbox_path_template = utils.normpath(template)

	# ------------------------------------------------------------------------

	def get_debug_mode(self):
		"""
		:return: Debud mode state
		:rtype: bool
		"""
		return self._debug_mode

	def set_debug_mode(self, level):
		"""
		Set logging level.

		:param str level: "debug" / "info"
		"""
		log_level = logging.DEBUG if level.lower() == "debug" else logging.INFO
		loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

		for logger in loggers:
			logger.setLevel(log_level)

		self._debug_mode = level
		log.info("Set debug mode to: {}".format(self._debug_mode))

	# ------------------------------------------------------------------------

	def get_cache(self):
		"""
		:return: Use cache build state
		:rtype: bool
		"""
		return self._cache

	def set_cache(self, state):
		"""
		:param bool state:
		"""
		self._cache = state

	# ------------------------------------------------------------------------

	def get_cache_directory(self):
		"""
		:return: Path template
		:rtype: str
		"""
		return utils.normpath(self._cache_directory)

	def set_cache_directory(self, directory):
		"""
		:param str directory:
		"""
		self._cache_directory = utils.normpath(directory)

	# ------------------------------------------------------------------------

	def get_partslib_paths(self):
		"""
		Use caps for suffix token.

		:return:
		:rtype: bool
		"""
		return [utils.normpath(p) for p in self._partslib_paths]

	def set_partslib_paths(self, paths):
		"""
		Set use caps for suffix token.

		:param bool value:
		:return:
		"""
		self._partslib_paths = [utils.normpath(p) for p in paths]

	def set_editor(self, editor):
		"""

		:param editor:
		:return:
		"""
		self._default_editor = editor

	# ------------------------------------------------------------------------

	def load(self):
		"""
		Reload config dataexporter from disk.

		:return:
		"""
		if os.path.isfile(PREF_FILE):
			data = utils.read_json(PREF_FILE)
			self.set_debug_mode(data.get("debug_mode", self._debug_mode))
			self._name_template = data.get("name_template", self._name_template)
			self._path_template = data.get("path_template", self._path_template)
			self._sandbox_path_template = data.get("sandbox_path_template", self._sandbox_path_template)
			self._cache_directory = data.get("cache_directory", self._cache_directory)
			self._cache = data.get("cache", self._cache)
			self._side_tokens = data.get("side_tokens", self._side_tokens)
			self._capitalize_side = data.get("capitalize_side", self._capitalize_side)
			self._capitalize_suffix = data.get("capitalize_suffix", self._capitalize_suffix)
			self._use_numerical_index = data.get("use_numerical_index", self._use_numerical_index)
			self._partslib_paths = data.get("partslib_paths", self._partslib_paths)
			self._type_suffix.update(data.get("type_suffix", self._type_suffix))
			self._default_editor = data.get("editor", self._default_editor)

		else:
			log.debug("File does not exist: {}".format(PREF_FILE))

	def reset(self):
		"""
		Reset prefs to default

		:return:
		"""
		self._capitalize_side = CAPITALIZE_SIDE
		self._capitalize_suffix = CAPITALIZE_SUFFIX
		self._side_tokens = SIDES_DICT
		self._name_template = NAME_TEMPLATE
		self._path_template = PATH_TEMPLATE
		self._sandbox_path_template = SANDBOX_TEMPLATE
		self._cache_directory = CACHE_DIRECTORY
		self._cache = CACHE
		self._debug_mode = DEBUG_MODE
		self._type_suffix = TYPE_SUFFIX
		self._use_numerical_index = USE_NUMERICAL_INDEX
		self._partslib_paths = PARTS_LIB_PATHS
		self._default_editor = DEFAULT_EDITOR
		log.debug("Reset prefs to default.")

	def write(self):
		"""
		Write config dataexporter to disk.

		:return:
		"""
		try:
			utils.write_json(PREF_FILE, self.data_dict)

		except IOError as e:
			log.error("Cannot write to file: {}".format(PREF_FILE))
