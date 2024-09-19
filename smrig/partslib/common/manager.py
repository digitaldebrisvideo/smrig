import imp
import logging
import os
import re
import shutil
import sys
import traceback

import maya.cmds as cmds
from smrig import env
from smrig.gui.mel import prompts
from smrig.lib import decoratorslib
from smrig.lib import iolib
from smrig.lib import pathlib
from smrig.lib import selectionlib
from smrig.lib.constantlib import GUIDE_GRP
from smrig.partslib.common import basepart
from smrig.partslib.common import guidemixin
from smrig.partslib.common import rigmixin
from smrig.partslib.common import utils

try:
	from importlib import reload
except:
	pass

log = logging.getLogger("smrig.partslib.manager")

template_extention = "tmpl"


@decoratorslib.singleton
class Manager():
	"""
	PartsLibrary class.
	"""

	def __init__(self):
		self._data = {}
		self.reload_lib()

	@property
	def parts(self):
		"""
		:return: available rig parts
		:rtype: list
		"""
		parts = [p for p in self._data.keys() if self._data[p].get("type") == "part"]
		parts = [p for p in parts if p not in ["basepart", "boilerplate"]]
		parts.sort()
		return parts

	@property
	def templates(self):
		"""
		:return: available rig templates
		:rtype: list
		"""
		templates = [p for p in self._data.keys() if self._data[p].get("type") == "template"]
		templates.sort()
		return templates

	@property
	def categories(self):
		"""
		:return: available rig part categories
		:rtype: list
		"""
		categories = list(set([self._data[k].get("category") for k in self._data.keys()]))
		categories = [c for c in categories if c not in ["partslib"]]
		categories.sort()

		if env.asset.get_asset() in categories:
			categories.remove(env.asset.get_asset())
			categories.insert(0, env.asset.get_asset())

		return categories

	@property
	def part_categories(self):
		"""

		:return:
		"""
		categories = [self._data[k].get("category") for k in self._data.keys() if self._data[k].get("type") == "part"]
		categories = [c for c in list(set(categories)) if c not in ["partslib"]]
		categories.sort()

		if env.asset.get_asset() in categories:
			categories.remove(env.asset.get_asset())
			categories.insert(0, env.asset.get_asset())

		return categories

	@property
	def template_categories(self):
		"""

		:return:
		"""
		categories = [self._data[k].get("category") for k in self._data.keys() if
		              self._data[k].get("type") == "template"]
		categories = [c for c in list(set(categories)) if c not in ["partslib"]]
		categories.sort()

		if env.asset.get_asset() in categories:
			categories.remove(env.asset.get_asset())
			categories.insert(0, env.asset.get_asset())

		return categories

	@property
	def paths(self):
		"""
		:return: All paths for rig parts on disc. This includes non-writable paths.
		:rtype: list
		"""
		part_paths = []
		part_paths.extend(env.asset.get_paths() or [])
		part_paths.extend([os.path.expandvars(p) for p in env.prefs.get_partslib_paths()])
		return part_paths

	@property
	def data(self):
		"""
		:return: All parts dataexporter
		:rtype: dict
		"""
		return self._data

	# ---------------------------------------------------------------------------------------------------------

	def get_type(self, part_type):
		"""
		Return the type specified part or template module.
		:param str part_type:
		:return:
		"""
		return self._data.get(part_type).get("type")

	def get_category(self, part_type):
		"""
		Return the doc strings for specified part module.
		:param str part_type:
		:return:
		"""
		return self._data.get(part_type).get("category")

	def get_path(self, part_type):
		"""
		Return the doc strings for specified part module.
		:param str part_type:
		:return:
		"""
		return self._data.get(part_type).get("path")

	# ---------------------------------------------------------------------------------------------------------

	def reload_lib(self):
		"""
		Reload the parts library. update paths, and docstrings

				"""
		reload(guidemixin)
		reload(rigmixin)
		reload(basepart)

		self._data = {}

		asset = env.asset.get_asset() or "%None%"
		paths = [p for p in self.paths if os.path.isdir(p)]

		all_paths = []
		discovered = []
		for part_path in paths:
			if os.path.isdir(part_path):
				all_paths.append(pathlib.normpath(part_path))

				if part_path not in env.asset.get_paths():
					for root, directories, filenames in os.walk(part_path):
						for directory in directories:
							sub_path = os.path.join(root, directory)
							if sub_path not in all_paths:
								all_paths.append(pathlib.normpath(sub_path))

		for directory in all_paths:
			modules = os.listdir(directory) or []
			modules = [module for module in modules if module not in discovered]
			modules = [f for f in modules if "_" not in f]
			modules = [f for f in modules if os.path.splitext(f)[1] in [".py", "." + template_extention]]

			if os.path.isdir(directory) and modules:
				for module in modules:
					module_path = os.path.join(directory, module)

					# Read python part modules
					if module.endswith(".py"):
						if os.path.isfile(module_path):
							with open(module_path, "r") as f:
								lines = f.readlines()

						if "#-*-smrig:" in re.sub(" +", "", lines[0]):
							discovered.append(module)

							if asset in module_path:
								category = asset
							else:
								category = os.path.basename(directory)

							part_name = module.split(".")[0]
							self._data[part_name] = {
								"type": "part",
								"category": category,
								"path": pathlib.normpath(module_path)
							}

					# read template jsons
					elif module.endswith("." + template_extention):
						discovered.append(module)
						category = os.path.basename(directory)
						part_name = module.split(".")[0]

						self._data[part_name] = {
							"type": "template",
							"category": category,
							"path": pathlib.normpath(module_path)
						}

		log.debug("Reloaded all parts.")

	# ---------------------------------------------------------------------------------------------------------

	def create_part(self, name, category, path=None):
		"""
		Create a new empty part python module at the specifed location.

		:name str: Name of new part
		:category str: Category for new part
		:path str: Path for new file
				"""
		class_name = name[0].upper() + name[1:]
		source = self._data.get("boilerplate").get("path")
		path = path if path else self.paths[-1]

		if env.asset.get_asset() and env.asset.get_asset() in path:
			destination = os.path.join(path, "{}.py".format(name))
		else:
			destination = os.path.join(path, "parts", category, "{}.py".format(name))

		if os.path.isfile(destination):
			log.error("Part already exists: {}".format(pathlib.normpath(destination)))
			return

		pathlib.make_dirs(os.path.dirname(destination))
		with open(source, "r") as f:
			lines = f.readlines()

		lines = [l.replace("Boilerplate", class_name).replace("boilerplate", name) for l in lines]
		lines = "".join(lines)

		with open(destination, "w") as f:
			f.write(lines)

		self.reload_lib()
		log.debug("Created new part module: {}".format(pathlib.normpath(destination)))

		return destination

	def create_template(self, name, category, path=None):
		"""

		:param name:
		:param category:
		:param path:
		:return:
		"""

		path = path if path else self.paths[-1]

		if env.asset.get_asset() and env.asset.get_asset() in path:
			destination = os.path.join(path, "{}.py".format(name))
		else:
			destination = os.path.join(path, "templates", category, "{}.{}".format(name, template_extention))

		data = get_template_data()
		iolib.json.write(destination, data)

	def migrate_part(self, part, path=None):
		"""
		Migrate part python module to specified location.

		:part str: Part to migrate
		:path str: Destination path
				"""
		path = path if path else prompts.migrate_prompt(self.paths)
		if not path:
			log.warning("Must choose a path!")
			return

		source = self._data.get(part, {}).get("path")
		category = self._data.get(part, {}).get("category")

		if env.asset.get_asset() in path:
			destination = os.path.join(path, part + ".py")
		else:
			destination = os.path.join(path, category, part + ".py")

		if os.path.isfile(destination):
			log.error("Partt already exists: {}".format(destination))
			return

		pathlib.make_dirs(os.path.dirname(destination))
		shutil.copyfile(source, destination)

		self.reload_lib()
		log.debug("Migrated part module: {}".format(destination))

	# ---------------------------------------------------------------------------------------------------------

	def instance_part(self, part):
		"""
		Instanciate a part object.

		:part str: Part type to instantiated
		:return: An instance of the specified part python module.class
		:rtype: python object
		"""
		if part not in self.data.keys():
			log.debug("{} not in partslib".format(part))
			return

		part = os.path.splitext(part)[0]
		class_name = part[0].upper() + part[1:]
		module_path = self._data.get(part).get("path")

		try:
			module = imp.load_source(part, module_path)
			module_class = getattr(module, class_name)
			return module_class()

		except Exception:
			raise Exception(traceback.format_exception(*sys.exc_info()))


def get_template_data():
	"""
	Get all parts guide build dataexporter.

	:return:
	"""
	if not cmds.objExists(GUIDE_GRP):
		log.warning("{} not in scene".format(GUIDE_GRP))
		return

	manager = Manager()
	parts = [n for n in selectionlib.get_children(GUIDE_GRP) if cmds.objExists("{}.partType".format(n))]
	template_data = {"template": []}

	for part in parts:
		part_type = cmds.getAttr("{}.partType".format(part))
		part_obj = manager.instance_part(part_type)
		part_obj.set_guide(part)
		part_data = utils.get_guide_data(part_obj)
		options = eval(cmds.getAttr("{}.options".format(part)))

		data = {"part_type": part_type,
		        "part_data": part_data,
		        "options": options}

		template_data["template"].append(data)

	return template_data
