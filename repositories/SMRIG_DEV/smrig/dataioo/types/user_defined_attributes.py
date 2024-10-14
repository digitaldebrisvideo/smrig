import maya.cmds as cmds

deformer_type = "userDefinedAttributes"
file_type = "json"


def get_data(node, **kwargs):
	"""

	:param node:
	:param kwargs:
	:return:
	"""
	data = {}
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

			# check the data type and attr type
			data_type = cmds.addAttr(node + "." + attr, dt=1, q=1)
			attr_type = cmds.addAttr(node + "." + attr, at=1, q=1)

			if type(data_type) is list:
				data_type = data_type[0]

			# If string handle it differntly. otherwise
			if data_type == "string":
				data = {
					"type": "string",
					"value": value
				}

			# if its an enum
			elif attr_type == "enum":
				enum = cmds.addAttr(node + "." + attr, en=1, q=1)
				default_value = cmds.addAttr(node + "." + attr, q=1, dv=1)

				data = {
					"type": attr_type,
					"enum": enum,
					"default_value": default_value,
					"value": value
				}

			elif attr_type == "compound":
				number_children = cmds.addAttr(node + "." + attr, q=1, number_children=1)
				children = cmds.attributeQuery(attr, node=node, lc=True)
				data = {
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

				data = {
					"type": attr_type,
					"min": min_value,
					"max": max_value,
					"default_value": default_value,
					"value": value
				}

			if data:
				data["parent"] = cmds.attributeQuery(attr, node=node, lp=True)
				data["keyable"] = cmds.getAttr(node + "." + attr, k=1)
				data["non_keyable"] = cmds.getAttr(node + "." + attr, cb=1)
				node_data[attr] = data
				ordered_attr_list.append(attr)

	if node_data and ordered_attr_list:
		data[node] = {"name": node,
		              "nodes": [node],
		              "deformer_type": deformer_type,
		              "data": node_data,
		              "attr_order": ordered_attr_list}

	return data


def set_data(data, **kwargs):
	"""

	:param data:
	:param kwargs:
	:return:
	"""

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
				pass

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
