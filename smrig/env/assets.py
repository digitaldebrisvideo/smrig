import datetime
import getpass
import logging
import shutil
import sys

import maya.mel as mel

from smrig.env import job
from smrig.env import prefs_
from smrig.env import utils
from smrig.userprefs import *

_job = job.Job()
prefs = prefs_.Prefs()

log = logging.getLogger("smrig.env.assets")

INFO_FILE_NAME = "asset.json"
BUILD_FILE_NAME = "build.json"
DEFAULT_VARIANT = "primary"
EXCLUDE_ASSETS = ["common", "config", "tools"]

try:
	from visional_pipeline_api1.asset import get_assets
except:
	pass


@utils.singleton
class Assets():

	def __init__(self):
		# variables
		self._asset_obj = {}
		self._assets_dict = {}
		self._assets_list = []

		# load assets
		self.reload_assets()

	def __getitem__(self, item):
		return self.verify_asset(item)

	# ------------------------------------------------------------------------

	@property
	def asset(self):
		"""
		:return: Active asset
		:rtype: Asset/None
		"""
		return self._asset_obj

	def verify_asset(self, name):
		"""
		:param str name:
		:return: Asset
		:rtype: Asset
		:raise RuntimeError: When asset with provided name doesn't exist.
		"""
		# get asset
		asset = self._assets_dict.get(name)

		# validate asset
		if not asset:
			error_message = "Unable to get asset by name '{}', " \
			                "options are {}".format(name, sorted(self._assets_dict.keys()))

			log.error(error_message)
			raise RuntimeError(error_message)

		return asset

	# ------------------------------------------------------------------------

	def get_assets(self):
		"""
		:return: Assets related to the current project
		:rtype: list[Asset]
		"""
		return self._assets_list

	def reload_assets(self):
		"""
		Clear the cache on the assets function, which means that next time the
		assets are queried
		"""
		if not _job.get_job():
			error_message = "Job not set. use env.set_job."
			log.debug(error_message)
			return

		if USE_FACILITY_PIPELINE:
			try:
				path = PATH_TEMPLATE.split("{job}")[0] + _job.get_job()
				assets_list = [os.path.basename(d) for d in get_assets(path)]
				self._assets_list = sorted(assets_list)
				return

			except:
				pass

		base_directory = prefs.get_path_template().split("{asset}")[0].replace("{job}", _job.get_job())

		if not os.path.isdir(base_directory):
			self._assets_list = []
			log.debug("Reloaded Assets")
			return

		assets_list = [d for d in os.listdir(base_directory) if d not in EXCLUDE_ASSETS
		               and not d.startswith(".") and os.path.isdir(utils.join(base_directory, d))]

		assets_dirs = [utils.join(base_directory, d) for d in assets_list]

		for asset, directory in zip(assets_list, assets_dirs):
			files = [utils.join(directory, f) for f in os.listdir(directory) if f == INFO_FILE_NAME]
			info_file = files[0] if files else None
			self._assets_dict[asset] = {"directory": directory, "info_file": info_file}

		self._assets_list = sorted(assets_list)

		log.debug("Reloaded Assets")

	def create_asset_directory(self, name):
		"""
		Make a new asset on disk and create all relevant rig files.

		:return:
		"""
		if not _job.get_job():
			log.debug("Job not set. use env.set_job.")
			return

		name = utils.construct_name(name)
		base_directory = prefs.get_path_template().split("{asset}")[0].replace("{job}", _job.get_job())
		directory = utils.join(base_directory, name)
		utils.make_dirs(directory)

		self.reload_assets()
		return name


@utils.singleton
class Asset():
	"""
	Asset class. This is a singleton class that manages your current asset environment.
	"""

	def __init__(self):
		# variables
		self._asset = ""
		self._variant = ""
		self._variants = []
		self._inheritance = []
		self._use_plugin = True
		self._sandbox = False
		self._sandbox_user = getpass.getuser()
		self._info = {}
		self._default_options = {"use_plugins": False,
		                         "guides": [{"asset": None,
		                                     "description": "primary",
		                                     "version": None,
		                                     "inherited": False}],

		                         "models": [{"asset": None,
		                                     "description": "primary",
		                                     "version": None,
		                                     "file_path": None,
		                                     "soft_normals": False,
		                                     "unlock_normals": False}]
		                         }
		# get job and assets object
		self.sys_path = AssetSysPath()
		self.assets = Assets()

	def set_asset(self, asset):
		"""
		Set rig asset.

		:param str asset: Asset name to set.
				"""
		if asset is not None and asset not in self.assets.get_assets():
			error_message = "{} is not an asset. Assets: {}".format(asset, self.assets.get_assets())
			log.error(error_message)
			raise NameError(error_message)

		# Clear variants, inheritance and read dataexporter from disk if it exists.
		self._asset = asset
		self._variant = DEFAULT_VARIANT if asset else None
		self._variants = [DEFAULT_VARIANT] if asset else None
		self._inheritance = []

		self.read_info_file()

		# set default variant or add it if it doesnt exist
		if self._asset and DEFAULT_VARIANT in self._variants:
			self.set_variant(DEFAULT_VARIANT)

		self.sys_path.insert_paths(self.get_paths())

		workspace_path = os.path.dirname(self.get_rigbuild_path())
		workspace_file = os.path.join(workspace_path, 'workspace.mel')

		if not os.path.isfile(workspace_file):
			create_workspace_file(workspace_file)

		if os.path.isfile(workspace_file) and not USE_FACILITY_PIPELINE:
			mel.eval('setProject "{0}"'.format(workspace_path))

		log.debug("Set asset: {}".format(asset))

	def set_variant(self, variant):
		"""
		Set rig variant.

		:param str variant: Variant to set.
				"""
		if variant is not None and variant not in self._variants:
			error_message = "{} is not a registered rig variant.".format(variant)
			log.error(error_message)
			raise NameError(error_message)

		self._variant = variant
		log.debug("Set variant: {}".format(variant))

	def add_variant(self, variant):
		"""
		Add new rig variant.

		:param str variant: New variant to add.
				"""
		if variant in self._variants:
			error_message = "Variant: {} already exist.".format(variant)
			log.warning(error_message)

			variant = utils.construct_name(variant)
			self.set_variant(variant)
			utils.make_dirs(self.get_data_path())

		variant = utils.construct_name(variant)

		self._variants.append(variant)
		self._info.get("build_options")[variant] = self._default_options
		self.write_info_file()

		# Insert new class for new variant into asset custom.py
		bin_path = utils.join(os.path.dirname(job.__file__), "bin")

		file_name = "custom.py"
		source_class = "Default" if variant == "mocap" else "InheritDefault"
		source_file_name = file_name if variant == "mocap" else "inherited.py"
		source = utils.join(bin_path, source_file_name)

		destination = utils.join(self.get_rigbuild_path(), "{}_{}".format(self.get_asset(), file_name))

		destination_class = "{}{}".format(variant[0].upper(), variant[1:])
		copy_class_to_file(source, destination, source_class, destination_class)

		# Update build list json
		source = utils.join(bin_path, "build.json")
		source_data = utils.read_json(source)
		source_variant_data = source_data.get(variant, source_data.get(DEFAULT_VARIANT))

		destination = self.get_build_file()
		destination_data = utils.read_json(destination)
		destination_data[variant] = source_variant_data
		utils.write_json(destination, destination_data)

		sub_variable_for_asset_name(self.get_asset(), destination)

		self.set_variant(variant)
		utils.make_dirs(self.get_data_path())
		log.debug("Added new rig variant: {}".format(variant))

	def remove_variant(self, variant):
		"""
		Remove new rig variant.

		:param str variant: New variant to remove.
				"""
		if variant not in self._variants:
			error_message = "Variant: {} does not exist.".format(variant)
			log.warning(error_message)
			return

		self._variants.remove(variant)
		self.write_info_file()

		log.debug("Removed rig variant: {}".format(variant))

	def add_inheritance(self, asset, build_list=False):
		"""
		Set sys.path inheritance from another asset. The rigbuild path for the specified asset will be inserted AFTER
		the rigbuild path for the current asset. The sys path will be inserted as the sencond index in the sys.path.

		:param str asset: Asset to name to inherit.
		:param bool build_list: Inherit the build list.
				"""
		if asset not in self.assets.get_assets():
			error_message = "{} is not an asset.".format(asset)
			log.warning(error_message)
			raise NameError(error_message)

		if asset == self.get_asset():
			error_message = "Asset cannot inherit itself!".format(asset)
			log.warning(error_message)
			raise NameError(error_message)

		# clear the build list inheritance for all other assets
		if build_list:
			self._inheritance = [[a[0], False] for a in self._inheritance]

		if asset in [a[0] for a in self._inheritance]:
			idx = [a[0] for a in self._inheritance].index(asset)
			self._inheritance[idx] = [self._inheritance[idx][0], build_list]
			self.write_info_file()
			return

		self._inheritance.append([asset, build_list])
		self.write_info_file()

		log.debug("Added asset inheritance: {}".format(asset))

	def remove_inheritance(self, asset):
		"""
		Remove sys.path inheritance from another asset.

		:param str asset: Asset to name to remove inheritance.
				"""
		if asset not in [a[0] for a in self._inheritance]:
			error_message = "{} is not inherited.".format(asset)
			log.warning(error_message)

		self._inheritance.remove(self._inheritance[[a[0] for a in self._inheritance].index(asset)])
		self.write_info_file()

		log.debug("Removed asset inheritance: {}".format(asset))

	def set_sandbox(self, value):
		"""
		Set to use user sandbox rigbuild paths. Use this option when working with GIT controlled rigbuild paths.
		:param bool value: switch between live rigbuild paths OR sandbox paths

				"""
		self._sandbox = bool(value)
		log.debug("Set sandbox: {}".format(value))

	def set_sandbox_user(self, user=None):
		"""
		Set user for sanbox build mode.

		:param str user: User namne ot set.
				"""
		if user is None:
			user = getpass.getuser()

		self._sandbox_user = user
		log.debug("Set sandbox: {}".format(user))

	def get_asset(self):
		"""
		:return str: Current asset name.
		"""
		return self._asset

	def get_variant(self):
		"""
		:return str: Current Rig variant.
		"""
		return self._variant

	def get_variants(self):
		"""
		:return list: All available rig variants for current asset.
		"""
		return self._variants

	def get_inheritance(self):
		"""
		:return list: Assets to inherit paths for current asset.
		"""
		return self._inheritance

	def get_sandbox(self):
		"""
		:return bool: Current sandbox mode.
		"""
		return self._sandbox

	def get_sandbox_user(self):
		"""
		:return str: Current sandbox user.
		"""
		return self._sandbox_user

	def get_paths(self):
		"""
		:return: List of rigbuild paths. (Including inherited paths)
		:rtype: list
		"""
		paths = []

		if self._asset:
			for asset in [self._asset] + [a[0] for a in self._inheritance]:
				p = get_rigbuild_path(asset, self._sandbox_user, self._sandbox)

				# Froce non-sandbox path IF sandbvox dir doesnt exist
				if self._sandbox and not os.path.isdir(p):
					p = get_rigbuild_path(asset, self._sandbox_user, False)

				paths.append(p)

		return paths

	def get_rigbuild_path(self):
		"""
		:return: rigbuild/dataexporter/variant path.
		:rtype: str
		"""
		paths = self.get_paths()
		if paths:
			return paths[0]
		else:
			return ""

	def get_data_path(self):
		"""
		:return: rigbuild/dataexporter/variant path.
		:rtype: str
		"""
		paths = self.get_paths()
		if paths and self.get_variant():
			return utils.join(paths[0], "dataio", self.get_variant())
		else:
			return ""

	def get_info_file(self):
		"""
		:return: File path for info.json
		:rtype: str
		"""
		path = ""
		paths = self.get_paths()
		if paths and self.get_variant():
			p = utils.join(paths[0], INFO_FILE_NAME)
			if os.path.isfile(p):
				path = p

		return utils.normpath(path)

	def get_build_file(self):
		"""
		:return: File path for build.json
		:rtype: str
		"""
		path = ""
		paths = self.get_paths()
		if paths and self.get_variant():
			p = utils.join(paths[0], BUILD_FILE_NAME)
			if os.path.isfile(p):
				path = p

		inherited_asset = [a[0] for a in self._inheritance if a[1]]
		if inherited_asset:
			inherited_path = [p for p in paths if inherited_asset[0] in p]
			if inherited_path:
				p = utils.join(inherited_path[0], BUILD_FILE_NAME)
				if os.path.isfile(p):
					path = p

		return utils.normpath(path)

	def get_info(self):
		"""
		:return: Data read from info file on disk.
		:rtype: dict
		"""
		return self._info

	def get_use_plugin(self, variant=None):
		"""
		:variant str: Rig variant to query.
		:return: use_plugin_nodes build option
		:rtype: string
		"""
		variant = variant or self.get_variant()
		return self._info.get("build_options", {}).get(variant, {}).get("use_plugin_nodes", True)

	def get_guides(self, variant=None):
		"""
		:variant str: Rig variant to query.
		:return: guides build option
		:rtype: string
		"""
		variant = variant or self.get_variant()
		return self._info.get("build_options", {}).get(variant, {}).get("guides")

	def get_models(self, variant=None):
		"""
		:variant str: Rig variant to query.
		:return: models build option
		:rtype: string
		"""
		variant = variant or self.get_variant()
		return self._info.get("build_options", {}).get(variant, {}).get("models")

	def write_build_options(self, variant, **kwargs):
		"""
		Update arbitrary build options.

		:variant str/None: Rig variant to set.
		:kwargs: build optrions to set.
				"""

		variant = variant or self.get_variant()
		if variant in self._info.get("build_options", {}).keys():
			self._info.get("build_options").get(variant).update(kwargs)
			self.write_info_file()
			self.read_info_file()

			log.debug("Updated {} options: {}".format(variant, kwargs))

		else:
			log.debug("Cannot find build options for variant: {}".format(variant))

	def set_use_plugin(self, value, variant=None):
		"""
		:value bool: Value
		:variant str: Rig variant to set.
		:rtype: None
		"""
		self.write_build_options(variant, use_plugin_nodes=value)

	def set_guides(self, variant=None, asset=None, description="primary", version=None, inherited=False, append=False):
		"""
		Write guide file to load for given variant.

		:param variant:
		:param asset:
		:param description:
		:param version:
		:param inherited:
		:param append:
		:return:
		"""
		value = {"asset": asset,
		         "description": description,
		         "version": version,
		         "inherited": inherited}

		if append:
			guides = list(self.get_guides())
			guides.append(value)
		else:
			guides = [value]

		self.write_build_options(variant, guides=guides)

	def set_models(self,
	               variant=None,
	               asset=None,
	               description="primary",
	               version=None,
	               file_path=None,
	               soft_normal=False,
	               unlock_normals=False,
	               append=False,
	               clear_all=False):
		"""
		Write model file to load for given variant.

		:param variant:
		:param asset:
		:param description:
		:param version:
		:param file_path: Alternate file path
		:param soft_normal:
		:param unlock_normals:
		:param append:
		:return:
		"""
		if clear_all:
			self.write_build_options(variant, models=[])
			return

		value = {"asset": asset,
		         "description": description,
		         "version": version,
		         "file_path": file_path,
		         "soft_normals": soft_normal,
		         "unlock_normals": unlock_normals}

		if append:
			models = list(self.get_models())
			models.append(value)
		else:
			models = [value]

		self.write_build_options(variant, models=models)

	def read_info_file(self):
		"""
		Read info.json file on disk for asset. This method is run when Asset.set_asset is set.

				"""
		self._info = {}

		if not self.get_info_file():
			log.debug("Info file does not exist for: {}".format(self.get_asset()))
			return

		self._info = utils.read_json(self.get_info_file())

		# set variants for Asset singleton
		variant_info = self._info.get("variants") or []
		for v in variant_info:
			if v not in self.get_variants():
				self._variants.append(v)

		# set inheritance (This is a little funky to support legacy info files)
		inherit_info = self._info.get("inheritance") or []
		for inherit_dict in inherit_info:
			if type(inherit_dict) is dict:
				if inherit_dict["asset"] not in self.get_inheritance():
					self._inheritance.append(inherit_dict["asset"])

			else:
				if inherit_dict not in self.get_inheritance():
					self._inheritance.append(inherit_dict)

	def write_info_file(self, **kwargs):
		"""
		Write current asset configuration to assets info.json file on disk.

		:param kwargs: Any optional dict dataexporter to write out.
				"""
		today = datetime.datetime.now()
		current_date = today.strftime("%B %d, %Y")

		if self.get_info_file():
			mod_time = datetime.datetime.fromtimestamp(os.stat(self.get_info_file()).st_mtime)
			mod_date = mod_time.strftime("%B %d, %Y")

		else:
			mod_date = current_date

		data = {
			"variants": self.get_variants(),
			"inheritance": self.get_inheritance(),
			"created_on": self._info.get("created_on", current_date),
			"created_by": self._info.get("created_by", getpass.getuser()),
			"modified_by": getpass.getuser(),
			"modified_on": mod_date,
			"build_options": self._info.get("build_options", {v: self._default_options for v in self.get_variants()})
		}

		# "smrig_git_hash": utils.get_hash()

		data.update(kwargs)

		# forcing new json file type
		rigbuild_path = self.get_rigbuild_path()
		if not os.access(rigbuild_path, os.W_OK):
			log.error("Cannot write to directory. Try using sandbox mode: {}".format(rigbuild_path))
			return

		file_path = utils.join(rigbuild_path, INFO_FILE_NAME)
		utils.write_json(file_path, data)
		utils.change_permission(file_path)
		log.debug("Wrote asset dataexporter to: {}".format(file_path))

	def create_gitignore(self):
		"""
		Create a gitignore to omit dataexporter dir
		"""
		gitignore = ["*.pyc\n", "*.pyo\n", "/dataexporter"]
		gitignore_file = utils.join(self.get_rigbuild_path(), ".gitignore")
		with open(gitignore_file, "w") as f:
			f.writelines(gitignore)
		utils.change_permission(gitignore_file)

	def create_rig_files(self):
		"""
		Create rig build file on disk.

		:return:
		"""

		rigbuild_path = self.get_rigbuild_path()
		if not self.get_asset() or not rigbuild_path:
			log.error("Asset not set!")

		# Create asset info file
		if DEFAULT_VARIANT not in self.get_variants():
			self._variants.append(DEFAULT_VARIANT)
			self._variant = DEFAULT_VARIANT

		# Create system dirs through shotgun
		utils.make_dirs(utils.join(rigbuild_path, "dataexporter", DEFAULT_VARIANT))

		# migrate custom file
		bin_path = utils.join(os.path.dirname(job.__file__), "bin")

		for file_name in ["custom.py"]:
			source = utils.join(bin_path, file_name)
			destination = utils.join(rigbuild_path, "{}_{}".format(self.get_asset(), file_name))

			if not os.path.isfile(destination):
				shutil.copyfile(source, destination)
				utils.change_permission(destination)
				sub_variable_for_asset_name(self.get_asset(), destination)

		# write build json
		build_file = utils.join(self.get_rigbuild_path(), BUILD_FILE_NAME)
		if not os.path.isfile(build_file):
			data = utils.read_json(utils.join(bin_path, "build.json"))
			utils.write_json(build_file, data)
			sub_variable_for_asset_name(self.get_asset(), build_file)

		self.write_info_file()
		self.read_info_file()


class AssetSysPath(object):
	"""
	Modifies the sys.path when the Asset.set_asset is called. Not to be used on its own.
	"""
	_old_paths = []

	def __init__(self):
		pass

	def clear_paths(self):
		"""
		Clears old paths that have been previously inserted for previous assets.

				"""
		for p in self._old_paths:
			while p in sys.path:
				sys.path.remove(p)
				log.debug("Removed path: {}".format(p))

		self._old_paths = []

	def insert_paths(self, paths):
		"""
		Insert paths into sys.path. Note: The result will be inverted in sys.path.

		:paths list: List of paths.
				"""
		self.clear_paths()

		for p in paths:
			sys.path.insert(0, p)
			self._old_paths.append(p)
			log.debug("Inserted path: {}".format(p))


def get_rigbuild_path(asset, user=getpass.getuser(), sandbox=False):
	"""
	Returns the rigbuild path for specified assets. Optionally return the sandbox build path for specied user.

	:param str asset: Asset to generate rigbuild path.
	:param str user: Sandbox user
	:param bool sandbox: Return sandbox path.
	:param bool sandbox: Return sandbox path.
	:return str: Rigbuild path for specified asset.
	"""

	if not _job.get_job() or not asset:
		return ""

	path = prefs.get_sandbox_path_template() if sandbox else prefs.get_path_template()
	path = path.replace("{job}", _job.get_job())
	path = path.replace("{asset_type}", asset.split("_")[0])
	path = path.replace("{asset}", asset)
	path = path.replace("{user}", user)
	return path


def sub_variable_for_asset_name(asset, file_path):
	"""

	:param asset:
	:param file_path:
	:return:
	"""
	with open(file_path) as f:
		content = f.readlines()

	with open(file_path, "w") as f:
		f.writelines([l.replace("${ASSET}", asset) for l in content])


def copy_class_to_file(source, destination, source_class, destination_class):
	"""
	Copies a specified class from one "source" file and appends it to another "destination" file.

	:param str source: Source file
	:param str destination: Destination file.
	:param str source_class: Name of class to opy
	:param str destination_class: New name of class to paste
		"""
	# Read destination lines
	with open(destination) as f:
		d_lines = f.readlines()

	# check if class already exists
	for i, l in enumerate(d_lines):
		if l.startswith("class") and destination_class in l:
			log.debug("{} is already a class in: {}".format(destination_class, destination))
			return

	# read all lines
	with open(source) as f:
		s_lines = f.readlines()

	# strip out source class
	for i, l in enumerate(s_lines):
		if l.startswith("class") and source_class in l:
			s_lines = s_lines[i:]
			break

	for i, l in enumerate(s_lines[1:]):
		if l.startswith("class"):
			s_lines = s_lines[:i]
			break

	if not s_lines:
		log.warning("Could not find source class: {} in: {}".format(source_class, source))
		return

	# rename source lcass to destinatio nclass
	new_lines = [s_lines[0].replace(source_class, destination_class, 1)]
	new_lines.extend([l.replace(source_class, destination_class) for l in s_lines[1:]])

	# join lists and write to file
	new_lines.insert(0, "\n")
	if not new_lines[-1].strip() == "\n":
		new_lines.insert(0, "\n")

	lines = "".join(d_lines + new_lines)

	# write to file
	with open(destination, "w") as f:
		f.write(lines)
		log.debug("Wrote new class: {} into: {}".format(destination_class, destination))


def create_asset(name):
	"""
	Make a new asset.

	:param name:
	:return:
	"""
	assets = Assets()
	asset = Asset()

	if asset in assets.get_assets():
		log.warning("Asset already exists: " + asset)

	name = assets.create_asset_directory(name)
	asset.set_asset(name)
	asset.create_rig_files()


def create_workspace_file(workspace_file):
	"""

	:param workspace_file:
	:return:
	"""
	arg = """//Maya 2017 Project Definition

workspace -fr "clips" "rig";
workspace -fr "scene" "rigbuild";
workspace -fr "images" "scenes";
workspace -fr "renderData" "model";
workspace -fr "sourceImages" "guides";"""

	if not os.path.isdir(os.path.dirname(workspace_file)):
		return

	if not os.path.isfile(workspace_file):
		try:
			with open(workspace_file, 'w') as f:
				f.write(arg)
				log.debug("Created workspace file: " + workspace_file)
		except:
			pass
