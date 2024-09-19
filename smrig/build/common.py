import getpass
import logging
import os

import maya.cmds as cmds
import maya.mel as mel
from smrig import env
from smrig.lib import decoratorslib
from smrig.lib import iolib
from smrig.lib import pathlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.build")

CACHE_NAME_FORMAT = "{}_{}_{}_{}_smrig_build_step_cache.mb"

exec("""
try:
    from importlib import reload
except:
    pass
""")


@decoratorslib.singleton
class Manager():
	"""
	         @decoratorslib.singleton
	class Manager():

		"""

	def __init__(self):
		self.asset = ""
		self.variant = ""
		self.path = ""
		self.status_node = ""
		self.current_step_index = 0
		self.build_list = []
		self.data = {}

		self.reload_manager()

	@property
	def build_file(self):
		"""
		Path to rig build json file
		:return:
		"""
		return self.path

	@property
	def status(self):
		"""
		List of step statuses

		:return:
		"""
		return [s.get("status") for s in self.build_list]

	def reload_manager(self):
		"""
		Reload build list manager.

		:return:
		"""
		self.asset = env.asset.get_asset()
		self.variant = env.asset.get_variant()
		self.path = env.asset.get_build_file()

		self.status_node = "{}_{}_smrig_manager".format(self.asset, self.variant)
		self.current_step_index = 0
		self.build_list = []
		self.data = {}

		if not self.asset:
			log.debug("Asset not set.")
			return

		if not self.variant:
			log.debug("Variant not set.")
			return

		if not self.path:
			log.warning("Could not find build list file!")
			return

		# read dataexporter from build list
		self.data = iolib.json.read(self.path)
		if self.variant not in self.data.keys():
			log.debug("Cant find build list for variant: {}".format(self.variant))
			return

		self.build_list = self.data.get(self.variant)

		# update build list status and current index
		if self.status_node and cmds.objExists(self.status_node):
			status_list = eval(cmds.getAttr("{}.buildStatus".format(self.status_node)))

			if len(status_list) != len(self.build_list):
				cmds.delete(self.status_node)
				return

			self.current_step_index = cmds.getAttr("{}.currentIndex".format(self.status_node))
			for i in range(len(self.build_list)):
				self.build_list[i]["status"] = status_list[i]

		self.check_imports()

	@decoratorslib.preserve_selection
	def create_status_node(self):
		"""
		Create an introspective mute node to store build status.

		:return:
		"""
		if not cmds.objExists(self.status_node):
			self.status_node = cmds.createNode("mute", n=self.status_node)
			cmds.addAttr(self.status_node, ln="smrigStatusManager", at="message")
			cmds.addAttr(self.status_node, ln="currentIndex", at="long")
			cmds.addAttr(self.status_node, ln="buildStatus", dt="string")

		extras = [n for n in cmds.ls("*_smrig_manager.smrigStatusManager") if n != self.status_node]
		if extras:
			cmds.delete(extras)

	def update_status_node(self):
		"""
		Update build status node

		:return:
		"""
		status_list = [s.get("status") for s in self.build_list]

		self.create_status_node()
		cmds.setAttr("{}.currentIndex".format(self.status_node), self.current_step_index)
		cmds.setAttr("{}.buildStatus".format(self.status_node), status_list, type="string")

	def cache_build_step(self, index):
		"""
		Save cache file to prefs cache directory.

		:param int index: step index
		:return:
		"""
		cache_path = env.prefs.get_cache_directory()
		pathlib.make_dirs(cache_path)

		utilslib.scene.remove_unknown_nodes()
		utilslib.scene.remove_unknown_plugins()

		file_path = os.path.join(cache_path, CACHE_NAME_FORMAT.format(self.asset,
		                                                              self.variant,
		                                                              getpass.getuser(),
		                                                              index))
		try:
			cmds.file(file_path, pr=1, ea=1, f=1, type='mayaBinary')
			log.debug("Cached build step: {}".format(file_path))

		except Exception as e:
			log.warning("Could not save build step cache file.")

	def check_imports(self):
		"""
		Check module imports and update status

		:return:
		"""
		for step_data in self.build_list:
			import_code = step_data.get("import_code")
			item_type = step_data.get("item_type")
			index = self.build_list.index(step_data) if step_data in self.build_list else -1

			try:
				if item_type.lower() == "python":
					exec("{}".format(import_code))
					exec("reload({})".format(import_code.split(" ")[-1]))

					file_path = eval("{}.__file__".format(import_code.split(" ")[-1]))
					file_path = file_path.replace(".pyc", ".py") if file_path else ""
					self.build_list[index]["file_path"] = file_path

				elif item_type.lower() == "mel":
					mel.eval("{}".format(import_code))
					self.build_list[index]["file_path"] = ""

			except Exception as e:
				err = utilslib.py.get_exception_info(Exception(e))
				err = err[0] if err else "Error"
				self.build_list[index]["status"] = err

	def build_step_from_data(self, step_data):
		"""
		Run the step code based on step dict.

		:param dict step_data:
		:return: True if succeeded, Exception if fail.
		:rtype: bool / Exception
		"""

		label = step_data.get("label")
		item_type = step_data.get("item_type")
		import_code = step_data.get("import_code")
		command_code = step_data.get("command_code")
		enabled = step_data.get("enabled")
		cache = step_data.get("cache")
		index = self.build_list.index(step_data) if step_data in self.build_list else -1

		# python code
		if item_type == "label" or not enabled:
			return True

		elif command_code:
			try:
				msg = "Buidling step {}: {}\n\n\tlabel: {}\n\tcode type: {}\n\texecuting code:\n\t\t{}\n\t\t{}\n"
				msg = msg.format(index, "-" * 60, label, item_type, import_code, command_code)
				log.debug(msg)

				if item_type.lower() == "python":
					exec("{}\n{}\n{}".format(import_code, import_code.split(" ")[-1], command_code))

				elif item_type.lower() == "mel":
					mel.eval("{};{}".format(import_code, command_code))

				msg = "Completed step {}: {} {}".format(index, label, "-" * 60)
				log.info(msg)

			except Exception as e:
				msg = "Failed step {}: {} {}".format(index, label, "-" * 60)
				log.info(msg)
				log.error(utilslib.py.get_exception())
				return Exception(e)

		if cache:
			self.cache_build_step(index)

		return True

	def build_next_step(self):
		"""
		Run through te build and execute each step.

		:return: Result, True if succeeded, Exception if failed
		:rtype: bool / Exception
		"""
		if self.current_step_index >= len(self.build_list):
			log.info("Build is complete.")
			return

		index = int(self.current_step_index)
		result = self.build_step_from_data(self.build_list[index])

		if result is True:
			self.build_list[self.current_step_index]["status"] = "success"
			self.current_step_index = index + 1
			self.update_status_node()

		elif type(result) is Exception:
			err = utilslib.py.get_exception_info(result)
			err = err[0] if err else "Error"
			self.build_list[self.current_step_index]["status"] = err
			self.update_status_node()
			raise result

	def build_steps(self, restart=False, start_index=None, last_index=None):
		"""
		Run through the remaining build or rebuild from start to finish.

		:param bool restart: Start from beginning
		:param int start_index: start range
		:param int last_index: end range
		:return: Result, True if succeeded, Exception if failed
		:rtype: None
		"""
		self.current_step_index = 0 if restart else self.current_step_index
		self.current_step_index = start_index if start_index else self.current_step_index

		if self.current_step_index >= len(self.build_list) - 1:
			log.info("Build is complete.")
			return

		index = int(self.current_step_index)
		for index in range(index, len(self.build_list)):
			result = self.build_step_from_data(self.build_list[index])

			if result is True:
				self.build_list[index]["status"] = "success"
				self.current_step_index = index
				self.update_status_node()

			elif type(result) is Exception:
				err = utilslib.py.get_exception_info(result)
				err = err[0] if err else "Error"
				self.build_list[self.current_step_index]["status"] = err
				self.current_step_index = index - 1
				self.update_status_node()
				raise result

			if last_index and index == last_index:
				log.info("Completed selected steps.")
				return

		log.info("Build is complete.")

	def write_build_list(self):
		"""
		write build list to disk

		:return:
		"""
		data = dict(self.data)
		build_list = []

		for item in self.build_list:
			build_list.append({
				"annotation": item.get("annotation"),
				"cache": item.get("cache"),
				"command_code": item.get("command_code"),
				"enabled": item.get("enabled"),
				"expanded": item.get("expanded"),
				"import_code": item.get("import_code"),
				"item_type": item.get("item_type"),
				"label": item.get("label"),
			})

		data[self.variant] = build_list
		iolib.json.write(self.path, data)
		log.debug("Wrote build list to disk")
