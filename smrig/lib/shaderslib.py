import logging

import maya.cmds as cmds

from smrig.lib import nodepathlib
from smrig.lib import selectionlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.shaderslib")

color_ATTRIBUTE = {"surfaceShader": "outColor"}
TRANSPARENCY_ATTRIBUTE = {"surfaceShader": "outTransparency"}
PLACEMENT_TO_FILE_ATTRIBUTES = {
	"coverage": "coverage",
	"translateFrame": "translateFrame",
	"rotateFrame": "rotateFrame",
	"mirrorU": "mirrorU",
	"mirrorV": "mirrorV",
	"stagger": "stagger",
	"wrapU": "wrapU",
	"wrapV": "wrapV",
	"repeatUV": "repeatUV",
	"offset": "offset",
	"rotateUV": "rotateUV",
	"noiseUV": "noiseUV",
	"vertexUvOne": "vertexUvOne",
	"vertexUvTwo": "vertexUvTwo",
	"vertexUvThree": "vertexUvThree",
	"vertexCameraOne": "vertexCameraOne",
	"outUV": "uv",
	"outUvFilterSize": "uvFilterSize"
}


def create_shader(name, shader_type="lambert", default_color=None):
	"""
	Creates a shader of the provided shader type. A shading engine will also
	be created and connected. The suffix of the shader is automatically
	generated and doesn't have to be provided in the name.

	:param str name:
	:param str shader_type:
	:param list default_color:
	:return: Shading node
	:rtype: str
	:raise ValueError: If a node with the shader name already exist.
	"""
	# get shader name
	# TODO: implement proper shader suffix
	shader_name = "{}_{}".format(name, shader_type.upper())
	engine_name = "{}_SG".format(name)

	# validate shader name
	if cmds.objExists(shader_name):
		error_message = "A node with name '{}' already exists.".format(shader_name)
		log.error(error_message)
		raise ValueError(error_message)

	# create shader + shader engine
	cmds.shadingNode(shader_type, asShader=True, name=shader_name)
	cmds.sets(name=engine_name, renderable=True, noSurfaceShader=True, empty=True)
	cmds.connectAttr("{}.outColor".format(shader_name), "{}.surfaceShader".format(engine_name))

	# set default color
	if default_color:
		color_path = get_color_attribute(shader_name, node_path=True)
		cmds.setAttr(color_path, *default_color)

	return shader_name


def assign_shader(shader, geometry):
	"""
	Assign the shader to the geometry. The geometry argument can either be a
	string or a list. The geometry list will be checked to see of any of the
	objects doesn't exist. If it doesn't exist a warning message will be
	displayed.

	:param str shader:
	:param str/list geometry:
	"""
	# get shading engine attached to shader
	shading_engine = get_shading_engine(shader)

	# force geo as list
	geometry = utilslib.conversion.as_list(geometry)

	# loop geometry
	for geo in geometry:
		# validate geometry
		if not cmds.objExists(geo):
			log.warning(
				"Can't assign geometry '{}' to shader '{}', it doesn't exist.".format(
					nodepathlib.get_name(geo),
					shader
				)
			)
			continue

		# assign geometry
		cmds.sets(geo, forceElement=shading_engine)


def assign_texture(shader, texture_path, shader_attribute="color"):
	"""
	Create a file node which links to the provided texture path and assign it
	to the provided attribute on the shader. Safety checks are in place to get
	the right attribute for color and transparency as they can differ on
	certain shaders.

	It is possible to assign the texture to a certain uv set for this the
	geometry and uv_set arguments will have to be used. If the texture is to
	be assigned to the default map these arguments can be ignored.

	:param str shader:
	:param str texture_path:
	:param str shader_attribute:
	:param str/list geometry:
	:param str uv_set:
	:return: File node
	:rtype: str
	"""
	# safety check for color and transparency attributes
	if shader_attribute in ["color"]:
		shader_attribute = get_color_attribute(shader)
	elif shader_attribute in ["transparency"]:
		shader_attribute = get_transparency_attribute(shader)

	# TODO: implement proper name handling
	name = shader.rsplit("_")[0]

	# create file node
	file_node_name = "{}_{}_FILE".format(name, shader_attribute)
	file_node = cmds.shadingNode("file", name=file_node_name, asTexture=True)

	# create placement node
	placement_node_name = "{}_{}_PLACE2D".format(name, shader_attribute)
	placement_node = cmds.shadingNode("place2dTexture", name=placement_node_name, asUtility=True)

	# connect placement to file
	for placement_attribute, file_attribute in PLACEMENT_TO_FILE_ATTRIBUTES.items():
		cmds.connectAttr(
			"{}.{}".format(placement_node, placement_attribute),
			"{}.{}".format(file_node, file_attribute)
		)

	# set texture path
	cmds.setAttr("{}.fileTextureName".format(file_node), texture_path, type="string")

	# connect to shader
	cmds.connectAttr("{}.outColor".format(file_node), "{}.{}".format(shader, shader_attribute))

	return file_node


def link_texture(file_node, uv_set, geometry):
	"""
	Create an UV link between the file node and geometry using the provided
	uv set.

	:param str file_node:
	:param str uv_set:
	:param str/list geometry:
	"""
	# force geometry to be list
	geometry = utilslib.conversion.as_list(geometry)

	# validate geometry
	for geo in geometry[:]:
		# validate geometry
		if not cmds.objExists(geo):
			log.warning(
				"Unable to link texture map '{}' to geometry '{}', geometry doesn't exist.".format(
					file_node,
					nodepathlib.get_name(geo)
				)
			)

			geometry.remove(geo)

	# get geometry shapes
	geometry = selectionlib.extend_with_shapes(geometry)
	geometry = selectionlib.filter_by_type(geometry, ["mesh", "nurbsSurface"])

	# loop geometry
	for geo in geometry:
		# validate uv set
		uv_sets = cmds.polyUVSet(geo, query=True, allUVSets=True)
		uv_sets_indices = cmds.polyUVSet(geo, query=True, allUVSetsIndices=True)

		if uv_set not in uv_sets:
			log.warning(
				"Unable to link texture map '{}' to geometry '{}', uv set '{}' doesn't exist.".format(
					file_node,
					nodepathlib.get_name(geo),
					uv_set
				)
			)

			continue

		# link uv
		uv_set_index = uv_sets_indices[uv_sets.index(uv_set)]
		cmds.uvLink(uvSet="{}.uvSet[{}].uvSetName".format(geo, uv_set_index), texture=file_node)


def link_color(node, shader, default_color=None):
	"""
	Create a color link between the shader and node provided node. This node
	is usually a control of some sort that animators will have easy access to.

	If not default color is provided the shaders current color will be used
	as the default.

	:param str node:
	:param str shader:
	"""
	# TODO: implement proper name handling
	name = shader.rsplit("_")[0]
	node_attribute = "{}_color".format(name)
	shader_attribute = get_color_attribute(shader, node_path=True)

	# get default color
	if not default_color:
		default_color = cmds.getAttr(shader_attribute)[0]

	# create attribute
	cmds.addAttr(node, longName=node_attribute, attributeType="double3", keyable=True)

	# create attribute channels
	for i, channel in enumerate(["R", "G", "B"]):
		cmds.addAttr(
			node,
			longName=node_attribute + channel,
			attributeType="double",
			minValue=0.0,
			maxValue=1.0,
			defaultValue=default_color[i],
			keyable=True,
			parent=node_attribute
		)

	# connect
	cmds.connectAttr("{}.{}".format(node, node_attribute), shader_attribute)


def link_transparency(node, shader, default_value=1.0):
	"""
	Create a transparency link between the shader and node provided node. This
	node is usually a control of some sort that animators will have easy
	access to.

	To improve rig playback speed a transparency value of 0 will also turn off
	the geometry completely. Switch will be created for each piece of geometry
	that is assigned to the shader.

	:param str node:
	:param str shader:
	"""
	# TODO: implement proper name handling
	name = shader.rsplit("_")[0]
	node_attribute = "{}_transparency".format(name)
	shader_attribute = get_transparency_attribute(shader)

	# create attribute
	cmds.addAttr(
		node,
		longName=node_attribute,
		attributeType="double",
		minValue=0.0,
		maxValue=1.0,
		defaultValue=default_value,
		keyable=True
	)

	# get reversed transparency value without using a reverse node.
	# the reverse node stops the transparency from working, using only double
	# linear nodes will prevent that issue from happening.
	mdl = cmds.createNode("multDoubleLinear", name="{}Transparency_MDL".format(name))
	cmds.connectAttr("{}.{}".format(node, node_attribute), "{}.input1".format(mdl))
	cmds.setAttr("{}.input2".format(mdl), -1)

	adl = cmds.createNode("addDoubleLinear", name="{}Transparency_ADL".format(name))
	cmds.setAttr("{}.input1".format(adl), 1)
	cmds.connectAttr("{}.output".format(mdl), "{}.input2".format(adl))

	# get children of transparency attribute
	children = cmds.attributeQuery(shader_attribute, node=shader, listChildren=True)

	# connect children individually
	for child in children:
		cmds.connectAttr("{}.output".format(adl), "{}.{}".format(shader, child))

	# TODO: best way of doing this? allow for input?
	shading_engine = get_shading_engine(shader)
	geometry = cmds.sets(shading_engine, query=True) or []
	geometry = list(set([geo.split(".")[0] for geo in geometry]))
	geometry = selectionlib.extend_with_shapes(geometry)
	geometry = selectionlib.filter_by_type(geometry, types=["mesh", "nurbsSurface"])

	# validate geometry
	if not geometry:
		return

	# create visibility condition node to only switch geometry of when the
	# transparency attribute is set to 0
	cd = cmds.createNode("condition", name="{}Transparency_CD".format(name))
	cmds.connectAttr("{}.{}".format(node, node_attribute), "{}.firstTerm".format(cd))

	# connect visibility
	for geo in geometry:
		cmds.connectAttr("{}.outColorR".format(cd), "{}.visibility".format(geo))


def get_shading_engine(shader):
	"""
	:param str shader:
	:return: Shading engine
	:raise RuntimeError: When no shading engine is attached to the shader.
	"""
	# get shading engine attached to shader
	shading_engine = cmds.listConnections(shader, type="shadingEngine")

	# validate shading engine
	if not shading_engine:
		error_message = "Shader '{}' has no shading engine attached.".format(shader)
		log.error(error_message)
		raise ValueError(error_message)

	return shading_engine[0]


def get_color_attribute(shader, node_path=False):
	"""
	Get the color attribute from a shader. Different shader types have
	different channels for the color attribute. This helper function will
	get that attribute. The name of the color channel defaults to 'color',
	any deviation from this can be implemented in the color_ATTRIBUTE
	variable.

	:param str shader:
	:param bool node_path:
	:return: color attribute
	:rtype: str
	:raise ValueError:
		When the color attribute doesn't exist on the shader node.
	"""
	shader_type = cmds.nodeType(shader)
	color_attribute = color_ATTRIBUTE.get(shader_type, "color")
	color_path = "{}.{}".format(shader, color_attribute)

	if not cmds.objExists(color_path):
		error_message = "Shader '{}' of type '{}' doesn't have the color attribute '{}'.".format(
			shader,
			shader_type,
			color_attribute
		)
		log.error(error_message)
		raise ValueError(error_message)

	return color_path if node_path else color_attribute


def get_transparency_attribute(shader, node_path=False):
	"""
	Get the transparency attribute from a shader. Different shader types have
	different channels for the transparency attribute. This helper function
	will get that attribute. The name of the transparency channel defaults to
	'transparency', any deviation from this can be implemented in the
	TRANSPARENCY_ATTRIBUTE variable.

	:param str shader:
	:param bool node_path:
	:return: Transparency attribute
	:rtype: str
	:raise ValueError:
		When the transparency attribute doesn't exist on the shader node.
	"""
	shader_type = cmds.nodeType(shader)
	transparency_attribute = TRANSPARENCY_ATTRIBUTE.get(shader_type, "transparency")
	transparency_path = "{}.{}".format(shader, transparency_attribute)

	if not cmds.objExists(transparency_path):
		error_message = "Shader '{}' of type '{}' doesn't have the transparency attribute '{}'.".format(
			shader,
			shader_type,
			transparency_attribute
		)
		log.error(error_message)
		raise ValueError(error_message)

	return transparency_path if node_path else transparency_attribute
