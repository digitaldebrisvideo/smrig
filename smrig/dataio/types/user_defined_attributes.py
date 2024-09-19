import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import iolib
from smrig.lib import utilslib

deformer_type = "userDefinedAttributes"
file_extension = "uatt"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(nodes):
	"""

	:param nodes:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	data = {}

	for node in nodes:
		attrs = cmds.listAttr(node, ud=1) or []
		ordered_attr_list = []
		node_data = {}

		for attr in attrs:

			value = None
			attr_type = cmds.addAttr(node + "." + attr, at=1, q=1)

			# check if value is gettable
			try:
				value = cmds.getAttr(node + "." + attr, sl=1)
				test_string_type = cmds.addAttr(node + "." + attr, dt=1, q=1)

				# Do this to record empty string attributes.
				if value is None and test_string_type[0] == "string":
					value = ""
					cmds.setAttr(node + "." + attr, value, type="string")

			except:
				pass

			# This is so maya doesnt crash if you try ot read a compuynd attribute
			if attr_type in ["compound", "message"]:
				value = attr_type

			# now gather data
			if value is not None:
				attr_data = {}

				# check the data type and attr type
				data_type = cmds.addAttr(node + "." + attr, dt=1, q=1)
				attr_type = cmds.addAttr(node + "." + attr, at=1, q=1)

				if type(data_type) is list:
					data_type = data_type[0]

				# If string handle it differntly. otherwise
				if data_type == "string":
					attr_data = {
						"type": "string",
						"value": value
					}

				# if its an enum
				elif attr_type == "enum":
					enum = cmds.addAttr(node + "." + attr, en=1, q=1)
					default_value = cmds.addAttr(node + "." + attr, q=1, dv=1)

					attr_data = {
						"type": attr_type,
						"enum": enum,
						"default_value": default_value,
						"value": value
					}

				elif attr_type == "compound":
					number_children = cmds.addAttr(node + "." + attr, q=1, number_children=1)
					children = cmds.attributeQuery(attr, node=node, lc=True)
					attr_data = {
						"type": attr_type,
						"number_children": number_children,
						"children": children
					}

				# if its numeric
				else:
					min_value = None
					max_value = None

					if cmds.attributeQuery(attr, node=node, minExists=True):
						min_value = cmds.addAttr(node + "." + attr, q=1, min=1)

					if cmds.attributeQuery(attr, node=node, minExists=True):
						max_value = cmds.addAttr(node + "." + attr, q=1, max=1)

					default_value = None

					try:
						default_value = cmds.attributeQuery(attr, node=node, ld=True)
						if default_value and type(default_value) is list:
							default_value = default_value[0]

					except:
						pass

					attr_data = {
						"type": attr_type,
						"min": min_value,
						"max": max_value,
						"default_value": default_value,
						"value": value
					}

				if attr_data:
					attr_data["parent"] = cmds.attributeQuery(attr, node=node, lp=True)
					attr_data["keyable"] = cmds.getAttr(node + "." + attr, k=1)
					attr_data["non_keyable"] = cmds.getAttr(node + "." + attr, cb=1)
					node_data[attr] = attr_data
					ordered_attr_list.append(attr)

		if node_data and ordered_attr_list:
			data[node] = {"data": node_data, "attr_order": ordered_attr_list}

	return data


def set_data(data):
	"""
	:param data:
	:param create_attrs:
	:return:
	"""

	def set_value(node, attr, attr_data):
		"""

		:param node:
		:param attr:
		:param attr_data:
		:return:
		"""
		value = attr_data.get("value")
		attr_type = attr_data.get("type")

		excluded_types = ["float2", "float3", "double2", "double3",
		                  "compound", "message", "short3", "long2", "long3"]
		try:
			if not cmds.objExists(node + "." + attr):
				log.warning("# Attr {0}.{1} does not exist! Skipping..".format(node, attr))
				return

			elif attr_type in excluded_types:
				return

			elif attr_type == "string":
				if not value:
					value = ""
				cmds.setAttr(node + "." + attr, value, type="string")

			else:
				cmds.setAttr(node + "." + attr, value)

			log.info("Set attribute value: " + node + "." + attr)

		except:
			log.warning("Could not set " + attr_type + " attr value :" + node + "." + attr)

	def add_attr(node, attr, attr_data):
		"""Actually add the attribbutes based on attr_dataDict"""

		parent = attr_data.get("parent")
		keyable = attr_data.get("keyable")
		attr_type = attr_data.get("type")

		# get parent and make sure it is a string
		if parent and type(parent) is list:
			parent = parent[0]

		# skip if the attr already exists
		if cmds.objExists(node + "." + attr):
			return

		# add message attrs
		elif attr_type == "message":
			cmds.addAttr(node, ln=attr, at="message")

		# add compound attrs
		elif attr_type == "compound":
			number_children = attr_data.get("number_children")

			try:
				if parent:
					cmds.addAttr(node, ln=attr, at="compound", p=parent, k=keyable, number_children=number_children)
				else:
					cmds.addAttr(node, ln=attr, at="compound", k=keyable, number_children=number_children)

			except:
				cmds.warning("# Could not add attr: {0}.{1}".format(node, attr))

		# add string attrs
		elif attr_type == "string":
			try:
				if parent:
					cmds.addAttr(node, ln=attr, dt="string", p=parent)
				else:
					cmds.addAttr(node, ln=attr, dt="string")

			except:
				cmds.warning("# Could not add attr: {0}.{1}".format(node, attr))

		# add enum attrs
		elif attr_type == "enum":
			try:
				enum = attr_data.get("enum")
				if parent:
					cmds.addAttr(node, ln=attr, at=attr_type, k=keyable, en=enum, p=parent)
				else:
					cmds.addAttr(node, ln=attr, at=attr_type, k=keyable, en=enum)

			except:
				cmds.warning("# Could not add attr: {0}.{1}".format(node, attr))

		elif attr_type == "bool":
			try:
				default_value = attr_data.get("default_value") or 0
				if parent:
					cmds.addAttr(node, ln=attr, at=attr_type, k=keyable, dv=default_value, p=parent)
				else:
					cmds.addAttr(node, ln=attr, at=attr_type, k=keyable, dv=default_value)

			except:
				cmds.warning("# Could not add attr: {0}.{1}".format(node, attr))

		elif attr_type in ["float2", "float3", "double2", "double3", "short3", "long2", "long3"]:
			try:
				if parent:
					cmds.addAttr(node, ln=attr, at=attr_type, k=keyable, p=parent)
				else:
					cmds.addAttr(node, ln=attr, at=attr_type, k=keyable)

			except:
				log.warning("Could not add attr: {0}.{1}".format(node, attr))

		else:
			try:
				min_value = attr_data.get("min")
				max_value = attr_data.get("max")
				default_value = attr_data.get("default_value") or 0

				if parent:
					if min_value and max_value:
						cmds.addAttr(node,
						             ln=attr,
						             min=min_value,
						             max=max_value,
						             at=attr_type,
						             k=keyable,
						             dv=default_value, p=parent)
					elif min_value:
						cmds.addAttr(node,
						             ln=attr,
						             min=min_value,
						             at=attr_type,
						             k=keyable,
						             dv=default_value,
						             p=parent)
					elif max_value:
						cmds.addAttr(node,
						             ln=attr,
						             max=max_value,
						             at=attr_type,
						             k=keyable,
						             dv=default_value,
						             p=parent)
					else:
						cmds.addAttr(node,
						             ln=attr,
						             at=attr_type,
						             k=keyable,
						             dv=default_value,
						             p=parent)
				else:
					if min_value is not None and max_value is not None:
						cmds.addAttr(node,
						             ln=attr,
						             min=min_value,
						             max=max_value,
						             at=attr_type,
						             k=keyable,
						             dv=default_value)
					elif min_value:
						cmds.addAttr(node,
						             ln=attr,
						             min=min_value,
						             at=attr_type,
						             k=keyable,
						             dv=default_value)
					elif max_value:
						cmds.addAttr(node,
						             ln=attr,
						             max=max_value,
						             at=attr_type,
						             k=keyable,
						             dv=default_value)
					else:
						cmds.addAttr(node,
						             ln=attr,
						             at=attr_type,
						             k=keyable,
						             dv=default_value)

					log.info("Added attribute: " + node + "." + attr)
					return True

			except:
				log.warning("Could not add attr: {0}.{1}".format(node, attr))

	# first create all compound and child attrs
	if not data:
		return

	nodes = data.keys()

	for node in nodes:
		node_data = data.get(node)
		if not node_data:
			continue

		node_data = node_data.get("data")
		ordered_attr_list = data.get(node).get("attr_order")

		# first create attrs
		for attr in ordered_attr_list:
			attr_data = node_data.get(attr)
			add_attr(node, attr, attr_data)


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	return [n for n in data.keys()]


def remap_nodes(data, remap):
	"""

	:param data:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	new_data = {}
	for search, replace in remap:
		for node, value in data.items():
			r_node = node.replace(search, replace) if search in node else node
			new_data[r_node] = value

	return new_data


def save(nodes, file_path, *args, **kwargs):
	"""

	:param nodes:
	:param file_path:
	:return:
	"""
	iolib.json.write(file_path, get_data(nodes))
	log.info("Saved {} to: {}".format(nodes, file_path))


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param args:
	:param kwargs:
	:return:
	"""
	remap = kwargs.get("remap")
	data = iolib.json.read(file_path)
	data = remap_nodes(data, remap) if remap else data

	nodes = list(data.keys())
	if utils.check_missing_nodes(file_path, nodes):
		return

	set_data(data)
