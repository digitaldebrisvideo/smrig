import logging
import os

import maya.cmds as cmds
from smrig import env
from smrig.dataio import types
from smrig.dataio import utils
from smrig.gui.mel import prompts
from smrig.lib import decoratorslib
from smrig.lib import pathlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.dataexporter.common")


@decoratorslib.preserve_selection
def save(deformer, node=None, directory=None, sub_directory=False, force=True, *args, **kwargs):
	"""
	Save specified deformers

	:param str/list deformer: export these deformer types
	:param str/list node: Export deformers for these nodes
	:param str directory:
	:param bool sub_directory: Put into sub-directories based on deforemr type.
	:param bool force: Force overwrite
	:param args:
	:param kwargs:
	:return:
	"""
	node_type = cmds.nodeType(deformer) if cmds.objExists(deformer) else None

	if node_type in types.constraints.constraint_types.keys():
		module = types.modules.get("constraints")

	elif cmds.objExists("{}.smrigMatrixConstraint".format(deformer)):
		module = types.modules.get("matrix_constraints")

	elif deformer in types.modules.keys():
		module = types.modules.get(deformer)

	else:
		module = types.modules.get(node_type)

	if not module:
		log.warning("{} not a valid export type ({}). Skipping...".format(deformer, node_type))
		return

	export_node = node if node and cmds.objExists(node) else deformer
	file_name = deformer if type(export_node) is list else export_node

	directory = directory if directory else utils.browser("export multiple", extension=module.file_extension)[0]

	if sub_directory:
		file_path = pathlib.join(directory, module.deformer_type, "{}.{}".format(file_name, module.file_extension))

	else:
		file_path = pathlib.join(directory, "{}.{}".format(file_name, module.file_extension))

	file_path = file_path.replace("|", "_")

	if os.path.exists(file_path) and not force:
		if prompts.confirm_dialog(title="Export Data", icon="question", message="File exists. Overwrite?"):
			os.remove(file_path)
		else:
			return

	pathlib.make_dirs(os.path.dirname(file_path))
	module.save(export_node, file_path, *args, **kwargs)

	return file_path


@decoratorslib.preserve_selection
def load(file_path=None, *args, **kwargs):
	"""
	Load specified deformers

	:param str file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	file_path = file_path if file_path else utils.browser("import multiple", extension="*")
	file_path = utilslib.conversion.as_list(file_path)

	for file in file_path:
		extension = os.path.splitext(file)[-1][1:]
		module = [m for t, m in types.modules.items() if m.file_extension == extension]
		module = module[0] if module else None

		if not module:
			log.warning("File is not a dataexporter file: {}".format(file))
			continue

		module.load(file, *args, **kwargs)


@decoratorslib.preserve_selection
def get_required_nodes(file_path):
	"""
	Load specified deformers

	:param str file_path:
	:param args:
	:param kwargs:
	:return:
	"""

	extension = os.path.splitext(file_path)[-1][1:]
	module = [m for t, m in types.modules.items() if m.file_extension == extension]
	module = module[0] if module else None

	if not module:
		log.warning("File is not a dataexporter file: {}".format(file_path))
		return []

	try:
		return module.get_required_nodes(file_path)

	except:
		log.warning("{} does not yet support remapping.".format(module.deformer_type))
		return []


# ---------------------------------------------------------------------


def save_to_asset(deformer, node=None, *args, **kwargs):
	"""
	Save deformers to asset data folder

	:param str/list deformer: export these deformer types
	:param str/list node: Export deformers for these nodes
	:param args:
	:param kwargs:
	:return:
	"""
	data_path = env.asset.get_data_path()
	save(deformer, node=node, directory=data_path, sub_directory=True, *args, **kwargs)


def load_type(deformer_types, *args, **kwargs):
	"""
	Load deformer from asset build data folder

	:param str/List deformer_types:
	:param args:
	:param kwargs:
	:return:
	"""
	deformer_types = utilslib.conversion.as_list(deformer_types)

	for node_type in deformer_types:
		module = types.modules.get(node_type)

		if not module:
			log.warning("{} is not a valid data type".format(node_type))
			continue

		extension = types.modules.get(node_type).file_extension
		data_path = pathlib.join(env.asset.get_data_path(), node_type)

		files = pathlib.get_files(data_path, search="*.{}".format(extension))
		if files:
			load(files, *args, **kwargs)
