import maya.cmds as cmds

from smrig.dataioo import utils

deformer_type = "shadingEngine"
file_type = "mayaBinary"


def get_data(shaders, **kwargs):
	"""
	Get data for export.

	:param str/list nodes:
	:return:
	"""
	excluded_nodes = ["initialParticleSE", "initialShadingGroup"]
	shaders = utils.as_list(shaders) if shaders else cmds.ls(type="shadingEngine")
	shaders = [s for s in shaders if s not in excluded_nodes]

	shading_engines = []
	materials = []
	assignments = []

	for shader in shaders:
		material_connection = cmds.listConnections(shader + ".surfaceShader")
		if material_connection:
			material = material_connection[0]
			cmds.hyperShade(objects=material)
			assignment = cmds.ls(sl=1)

			materials.append(material)
			shading_engines.append(shader)
			assignments.append(assignment)

	data = {"name": "all",
	        "deformer_type": deformer_type,
	        "shaders": shading_engines,
	        "materials": materials,
	        "assignments": assignments}

	export_node = cmds.createNode("mute", n="shaingEngine_data")
	utils.tag_export_data_nodes(export_node, data=data)

	return [export_node] + shading_engines + materials


def set_data(data, **kwargs):
	"""

	:param data:
	:param kwargs:
	:return:
	"""
	junk = [n for n in cmds.ls(data.get("imported_nodes") or [], l=True) if "|" in n]
	if junk:
		cmds.sets(junk, forceElement="initialShadingGroup", e=True)
		cmds.delete(junk)

	shading_engines = data.get("shaders")
	materials = data.get("materials")
	assignments = data.get("assignments")

	for shader, material, assignment in zip(shading_engines, materials, assignments):
		assignment = [a for a in cmds.ls(assignment) if "." not in a]
		if assignment and cmds.objExists(material):
			assign_shader(assignment, material, shader)

	for shader, material, assignment in zip(shading_engines, materials, assignments):
		assignment = [a for a in cmds.ls(assignment) if "." in a]
		if assignment and cmds.objExists(material):
			assign_shader(assignment, material, shader)


def assign_shader(assignment, material, shader):
	"""

	:param assignment:
	:param material:
	:param shader:
	:return:
	"""
	if not cmds.objExists(shader):
		shader = cmds.sets(renderable=1, noSurfaceShader=1, empty=1, name=shader)
		cmds.connectAttr(material + ".outColor", shader + ".surfaceShader")

	cmds.sets(assignment, forceElement=shader, e=True)
