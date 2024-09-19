import logging
import os

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import decoratorslib

deformer_type = "animShaders"
file_extension = "mb"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(nodes=None):
	"""
	Get data for export.

	:param str/list nodes:
	:return:
	"""
	nodes = [n for n in cmds.ls(nodes) if cmds.nodeType(n) == "shadingEngine"]

	excluded_nodes = ["initialParticleSE", "initialShadingGroup"]
	all_shading_engines = [s for s in cmds.ls(type="shadingEngine") if s not in excluded_nodes]
	all_shading_engines = nodes if nodes else all_shading_engines

	shading_engines = []
	materials = []
	assignments = []

	for shader in all_shading_engines:
		material_connection = cmds.listConnections(shader + ".surfaceShader")
		if material_connection:
			material = material_connection[0]

			cmds.hyperShade(objects=material)
			assignment = cmds.ls(sl=1)

			materials.append(material)
			shading_engines.append(shader)
			assignments.append(assignment)

	return shading_engines, materials, assignments


@decoratorslib.preserve_selection
def save(nodes=None, file_path=None, *args, **kwargs):
	"""
	Write data file.

	:param str/ list nodes:
	:param str file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	if not file_path:
		raise AttributeError("file path not specified.")

	shading_engines, materials, assignments = get_data()

	export_node = cmds.createNode("mute", n="anim_shaders_data")
	cmds.addAttr(export_node, ln="exportData", at="message")
	cmds.addAttr(export_node, ln="shadingEngines", dt="string")
	cmds.addAttr(export_node, ln="materials", dt="string")
	cmds.addAttr(export_node, ln="assignments", dt="string")

	cmds.setAttr(export_node + ".shadingEngines", str(shading_engines), type="string")
	cmds.setAttr(export_node + ".materials", str(materials), type="string")
	cmds.setAttr(export_node + ".assignments", str(assignments), type="string")

	file_path = "{}.mb".format(os.path.splitext(file_path)[0])

	cmds.select(export_node, shading_engines, r=True, ne=True)
	cmds.file(file_path, op="v=0;", type="mayaBinary", es=True)

	log.info("Saved {} to: {}".format(deformer_type, file_path))


@decoratorslib.preserve_selection
def load(file_path, ignore_missing=True, *args, **kwargs):
	"""
	Load data file

	:param str file_path:
	:param bool ignore_missing:
	:param args:
	:param kwargs:
	:return:
	"""
	remap = kwargs.get("remap")

	if not os.path.isfile(file_path):
		raise AttributeError("file path not found.")

	nodes = cmds.file(file_path, i=True, rnn=True)
	junk = [n for n in cmds.ls(nodes, l=True) if "|" in n]
	if junk:
		cmds.delete(junk)

	data_node = cmds.ls("*shaders*.exportData")
	if not data_node:
		log.warning("Cannot find data node.")

	data_node = data_node[0].split(".")[0]
	shading_engines = eval(cmds.getAttr(data_node + ".shadingEngines"))
	materials = eval(cmds.getAttr(data_node + ".materials"))
	assignments = eval(cmds.getAttr(data_node + ".assignments"))

	assignments = [remap_nodes(a, remap) for a in assignments] if remap else assignments

	for shader, assignment in zip(shading_engines, assignments):
		if utils.check_missing_nodes(shader, assignment):
			if not ignore_missing:
				return

	for shader, material, assignment in zip(shading_engines, materials, assignments):
		shape_assignment = [a for a in cmds.ls(assignment) if "." not in a]
		if shape_assignment and cmds.objExists(shader):
			cmds.sets(shape_assignment, forceElement=shader, e=True)

	for shader, material, assignment in zip(shading_engines, materials, assignments):
		face_assignment = [a for a in cmds.ls(assignment) if "." in a]
		if face_assignment and cmds.objExists(shader):
			cmds.sets(face_assignment, forceElement=shader, e=True)

	log.debug("Loaded: {}".format(deformer_type))


def remap_nodes(assignments, remap):
	"""
	Remap nodes

	:param assignments:
	:param remap:
	:return:
	"""
	if not remap:
		return assignments

	assignments = list(assignments)
	for search, replace in remap:
		for i, assignment in enumerate(assignments):
			if search in assignment:
				assignments[i] = assignment.replace(search, replace)

	return assignments
