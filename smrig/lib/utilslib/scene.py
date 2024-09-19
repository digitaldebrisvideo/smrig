import logging
import os
import uuid

import maya.cmds as cmds
import maya.mel as mel
from six import string_types

log = logging.getLogger("smrig.lib.utilslib.scene")
STASH_NAMESPACE = "stashed"


def load(file_path, action="open", namespace=None, rnn=False, new_file=False, force=False):
	"""
	Load maya scene

	:param str file_path:
	:param str action: Options are import open, reference
	:param str namespace:
	:param bool rnn: Return new nodes as list
	:param bool new_file: Start new file
	:param bool force: Forse without showing unsaved changes promopt
	:return:
	"""
	if not os.path.isfile(file_path or ""):
		log.warning("File not found: {}".format(file_path))
		return

	if action == "import":
		message = "Imported"

		if new_file:
			if save_unsaved_changes(force=force):
				cmds.file(new=1, f=1)
			else:
				return

		if namespace:
			namespace = namespace if namespace else ""
			nodes = cmds.file(file_path,
			                  i=True,
			                  rnn=rnn,
			                  options="v=0;",
			                  ignoreVersion=True,
			                  ra=True,
			                  mergeNamespacesOnClash=False,
			                  namespace=namespace)
		else:
			nodes = cmds.file(file_path,
			                  i=True,
			                  ignoreVersion=True,
			                  mergeNamespacesOnClash=False,
			                  rpr="",
			                  rnn=rnn,
			                  options="v=0;",
			                  pr=True)

	elif action == "open":
		message = "Opened"

		if save_unsaved_changes(force=force):
			nodes = cmds.file(file_path, f=1, o=1, rnn=rnn)
		else:
			return

	elif action == "reference":
		message = "Referenced"
		namespace = namespace if namespace else ""
		nodes = cmds.file(file_path,
		                  r=True,
		                  rnn=rnn,
		                  options="v=0;",
		                  ignoreVersion=True,
		                  mergeNamespacesOnClash=False,
		                  namespace=namespace)
	else:
		log.warning("Invalid action: {}".format(action))
		return

	remove_unknown_nodes_and_plugins()
	log.info("{} maya scene: {}".format(message, os.path.normpath(file_path)))
	return nodes


def export(file_path, action="export_selection", file_type="mayaBinary"):
	"""

	:param file_path:
	:param file_type:
	:return:
	"""
	file_path = os.path.splitext(file_path)[0]
	file_path = "{}.mb".format(file_path) if file_type == "mayaBinary" else "{}.ma".format(file_path)

	remove_unknown_nodes_and_plugins()

	if action == "export_selection":
		cmds.file(file_path, options="v=0;", type=file_type, es=True)
		log.info("Exported selection: {}".format(os.path.normpath(file_path)))
		return file_path

	elif action == "export_all":
		cmds.file(file_path, options="v=0;", type=file_type, ea=True)
		log.info("Exported all: {}".format(os.path.normpath(file_path)))
		return file_path

	else:
		log.warning("Invalid action: {}".format(action))


def save_unsaved_changes(force=False):
	"""
	Unsaved changes dialog.

	:param force:
	:return:
	"""
	if force:
		return True
	return bool(mel.eval('int $reult = `saveChanges("file -f -new")`;'))


def remove_unknown_nodes():
	"""
	Remove any unknown nodes from the current scene.
	"""
	nodes = cmds.ls(type=["unknown", "unknownDag", "unknownTransform"])
	if not nodes:
		log.debug("No unknown nodes found in the current scene.")
		return

	cmds.delete(nodes)
	log.info("Successfully removed {} unknown nodes.".format(len(nodes)))


def remove_unknown_plugins():
	"""
	Removes any unknown plugins form the scene. Unknown plugins that are being
	used will not be removed.
	"""
	# get unknown plugins
	unknown_plugins = cmds.unknownPlugin(query=True, list=True) or []

	# validate
	if not unknown_plugins:
		log.debug("No unknown plugins found.")
		return

	# remove plugins
	for unknown_plugin in unknown_plugins:
		data_types = cmds.unknownPlugin(unknown_plugin, query=True, dataTypes=True)
		node_types = cmds.unknownPlugin(unknown_plugin, query=True, nodeTypes=True)
		if not data_types + node_types:
			cmds.unknownPlugin(unknown_plugin, remove=True)
			log.info("Plugin successfully removed, '{}'.".format(unknown_plugin))
		else:
			log.warning("Plugin in use and cannot be removed, '{}'.".format(unknown_plugin))


def remove_unknown_nodes_and_plugins():
	"""
	Remove any unknown nodes and plugins in the scene.
	"""
	remove_unknown_nodes()
	remove_unknown_plugins()


# ----------------------------------------------------------------------------


def shakeout(nodes, remove_temp_file=True):
	"""
	Export the provided nodes to a temporary file. Once this is done an empty
	scene will be opened and the temporary path imported. This gets rid of
	any unused nodes in the scene, also with respect to the provided nodes.

	Use with caution. If any changes are not saved, those changes will be
	lost. It is possible to keep the temp file, but by default it gets deleted
	after the file has been imported.

	:param str/list nodes:
	:param bool remove_temp_file:
	:return: Temp file path
	:rtype: str/None
	"""
	# get temp file path
	temp_directory = cmds.internalVar(userTmpDir=True)
	temp_file_path = os.path.join(temp_directory, "shakeout-{0}.mb".format(uuid.uuid4()))

	# export selection
	remove_unknown_nodes_and_plugins()
	cmds.select(nodes, hierarchy=True)
	cmds.file(
		temp_file_path,
		force=True,
		options="v=0;",
		type="mayaBinary",
		preserveReferences=True,
		exportSelected=True
	)

	# import selection
	cmds.file(new=True, force=True)
	cmds.file(temp_file_path, i=True)

	# return temp file
	if not remove_temp_file:
		return temp_file_path

	# remove temp file
	os.remove(temp_file_path)


def set_stash_namespace():
	"""

	:return:
	"""
	if not cmds.namespace(exists=":" + STASH_NAMESPACE):
		cmds.namespace(add=":" + STASH_NAMESPACE)

	cmds.namespace(set=":" + STASH_NAMESPACE)


def stash_nodes(nodes=None, hierarchy=False, all_in_scene=False):
	"""
	Stash all nodes in the scene into a temp namespace.

	:param nodes:
	:param hierarchy:
	:param all_in_scene:
	:return:
	"""
	nodes_to_stash = [n for n in cmds.ls() if ':' not in n] if all_in_scene else cmds.ls(nodes)
	nodes_to_stash = cmds.ls(nodes_to_stash)

	if not nodes_to_stash:
		return

	if hierarchy:
		nodes_to_stash = cmds.listRelatives(nodes, ad=1) or []
		nodes_to_stash += nodes_to_stash

	if not cmds.namespace(exists=STASH_NAMESPACE):
		cmds.namespace(add=STASH_NAMESPACE)

	for node in nodes_to_stash:
		if cmds.objExists(node) and not node.startswith(STASH_NAMESPACE):
			ns_node_name = "{}:{}".format(STASH_NAMESPACE, node.split('|')[-1])
			try:
				cmds.rename(node, ns_node_name)
			except:
				pass


def unstash_all_nodes():
	"""
	Unstash all nodes in the scene and kill the stash namespace.

		:rtype: None
	"""
	if cmds.namespace(exists=STASH_NAMESPACE):
		cmds.namespace(removeNamespace=STASH_NAMESPACE, mergeNamespaceWithRoot=True)


def delete_stashed_nodes():
	"""
	Delete all stashed nodes in the scene and kill the stash namespace.

		:rtype: None
	"""
	if cmds.namespace(exists=STASH_NAMESPACE):
		cmds.namespace(removeNamespace=STASH_NAMESPACE, deleteNamespaceContent=True)


def find_stashed_nodes(nodes, stash_priority=True):
	"""
	Find a node stashed or not.

	:param str/list nodes:
	:param bool stash_priority: Prefer stashed node over unstashed if both found.
	:return: stashed or unstashed node
	:rtype: str/list
	"""
	nodes = eval(nodes) if "[" in nodes else nodes
	l_nodes = [nodes] if isinstance(nodes, string_types) else nodes

	if stash_priority:
		found = cmds.ls(["{}:{}".format(STASH_NAMESPACE, n) for n in l_nodes])
		found = found if found else cmds.ls(nodes)

	else:
		found = cmds.ls(nodes)
		found = found if found else cmds.ls(["{}:{}".format(STASH_NAMESPACE, n) for n in l_nodes])

	if isinstance(nodes, string_types):
		return found[0]
	else:
		return found
