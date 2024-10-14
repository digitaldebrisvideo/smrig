import logging

import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim
import maya.cmds as cmds
from smrig.lib import iolib
from smrig.lib import nodepathlib
from smrig.lib import utilslib

deformer_type = "setDrivenKeyframe"
file_extension = "sdk"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(nodes, sdk_only=False):
	"""

	:param nodes:
	:param sdk_only:
	:return:
	"""
	keyed_attrs = []
	anim_curves = []
	nodes = utilslib.conversion.as_list(nodes)

	for node in nodes:

		# sdks only
		connections = cmds.listConnections(node, s=1, d=0, type="animCurve", scn=1) or []
		for crv in connections:
			plug = cmds.listConnections(crv + ".output", s=0, d=1, p=1, scn=1)

			if plug:
				plug = nodepathlib.remove_namespace(plug[0])

				is_sdk = cmds.listConnections(crv + ".input", s=1, d=0, p=1, scn=1)
				if sdk_only and not is_sdk:
					continue

				anim_curves.append(str(crv))
				keyed_attrs.append(str(plug))

		# bloend weighted sdks
		connections = cmds.listConnections(node, s=1, d=0, type="blendWeighted", scn=1) or []
		for bw in connections:
			plug = cmds.listConnections(bw + ".output", s=0, d=1, p=1, scn=1)
			crvs = cmds.listConnections(bw, s=1, d=0, type="animCurve", scn=1) or []

			if plug:
				plug = nodepathlib.remove_namespace(plug[0])

			for crv in crvs:
				if plug:
					is_sdk = cmds.listConnections(crv + ".input", s=1, d=0, p=1, scn=1)
					if sdk_only and not is_sdk:
						continue

					anim_curves.append(str(crv))
					keyed_attrs.append(str(plug))

	# initialize dataexporter dict
	data = {}

	# for each curve get dataexporter
	for i, crv in enumerate(anim_curves):

		# get curve obj
		m_list = OpenMaya.MSelectionList()
		m_list.add(crv)

		m_obj = m_list.getDependNode(0)
		crv_obj = OpenMayaAnim.MFnAnimCurve(m_obj)

		# get sdk driver
		sdk_driver = cmds.listConnections(crv + ".input", s=1, d=0, p=1, scn=1)
		if sdk_driver:
			sdk_driver = nodepathlib.remove_namespace(sdk_driver[0])

		# get basic crv info
		crv_type = crv_obj.animCurveType
		pre_infinity = crv_obj.preInfinityType
		post_infinity = crv_obj.postInfinityType
		is_weighted = crv_obj.isWeighted
		number_keys = int(crv_obj.numKeys)

		# declare list variables
		value_list = []
		time_list = []

		# tangent lists
		in_type_list = []
		in_angle_list = []
		in_weight_list = []

		out_type_list = []
		out_angle_list = []
		out_weight_list = []

		# get time, value and tangent info per key
		for ii in range(number_keys):
			key_input = crv_obj.input(ii)
			time = OpenMaya.MTime(key_input)
			time = time.value

			time_list.append(time)
			value_list.append(crv_obj.value(ii))

			# api style tangent types
			in_type_list.append(crv_obj.inTangentType(ii))
			out_type_list.append(crv_obj.outTangentType(ii))

			# IN TANGENTS
			in_angle_weight = crv_obj.getTangentAngleWeight(ii, True)
			in_angle = OpenMaya.MAngle(in_angle_weight[0]).value
			in_weight = in_angle_weight[1]

			in_angle_list.append(in_angle)
			in_weight_list.append(in_weight)

			# OUT TANGENTS
			out_angle_weight = crv_obj.getTangentAngleWeight(ii, False)
			out_angle = OpenMaya.MAngle(out_angle_weight[0]).value
			out_weight = out_angle_weight[1]

			out_angle_list.append(out_angle)
			out_weight_list.append(out_weight)

		# create dict
		crv_data = {
			"name": crv,
			"crv_type": crv_type,
			"pre_infinity": pre_infinity,
			"post_infinity": post_infinity,
			"is_weighted": is_weighted,
			"time_list": time_list,
			"value_list": value_list,
			"in_type_list": in_type_list,
			"in_angle_list": in_angle_list,
			"in_weight_list": in_weight_list,
			"out_type_list": out_type_list,
			"out_angle_list": out_angle_list,
			"out_weight_list": out_weight_list,
			"sdk_driver": sdk_driver
		}

		if keyed_attrs[i] in data.keys():
			data[keyed_attrs[i]].append(crv_data)
		else:
			data[keyed_attrs[i]] = [crv_data]

	return data


def create_anim_crv(driven_attr, crv_type):
	"""

	:param driven_attr:
	:param crv_type:
	:return:
	"""
	bw_connections = cmds.listConnections(driven_attr, s=1, d=0, type="blendWeighted", scn=1) or []
	anim_connections = cmds.listConnections(driven_attr, s=1, d=0, type="animCurve", scn=1) or []

	m_list = OpenMaya.MSelectionList()
	m_list.add(driven_attr)
	plug = m_list.getPlug(0)

	if anim_connections:
		cmds.disconnectAttr(anim_connections[0] + ".output", driven_attr)
		bw = cmds.createNode("blendWeighted")
		cmds.connectAttr(bw + ".output", driven_attr)
		cmds.connectAttr(anim_connections[0] + ".output", bw + ".input[0]")

		m_list = OpenMaya.MSelectionList()
		m_list.add(bw + ".input[1]")
		plug = m_list.getPlug(0)

	elif bw_connections:
		bw = bw_connections[0]
		count = len(cmds.listConnections(bw + ".input", s=1, d=0, type="animCurve", scn=1) or [])

		m_list = OpenMaya.MSelectionList()
		m_list.add("{0}.input[{1}]".format(bw, count))
		plug = m_list.getPlug(0)

	crv = OpenMayaAnim.MFnAnimCurve()
	crv.create(plug, crv_type)

	return crv


def set_data(data):
	"""

	:param data:
	:return:
	"""
	for driven_attr, all_crv_data in data.items():
		if type(all_crv_data) is dict:
			all_crv_data = [all_crv_data]

		for crv_data in all_crv_data:
			test_attr = cmds.ls(driven_attr)
			if not test_attr:
				log.warning("Attribute does not exist: {}. Skipping...".format(driven_attr))
				continue

			driven_attr = test_attr[0]

			# get all dataexporter"=
			name = crv_data.get("name") or driven_attr.replace(".", "_")
			crv_type = crv_data.get("crv_type")
			pre_infinity = crv_data.get("pre_infinity")
			post_infinity = crv_data.get("post_infinity")
			is_weighted = crv_data.get("is_weighted")
			time_list = crv_data.get("time_list")
			value_list = crv_data.get("value_list")

			in_type_list = crv_data.get("in_type_list")
			in_angle_list = crv_data.get("in_angle_list")
			in_weight_list = crv_data.get("in_weight_list")

			out_type_list = crv_data.get("out_type_list")
			out_angle_list = crv_data.get("out_angle_list")
			out_weight_list = crv_data.get("out_weight_list")

			sdk_driver = crv_data.get("sdk_driver")

			# check if ther are keys to create
			if not len(value_list):
				continue

			# create new crv obj
			crv = create_anim_crv(driven_attr, crv_type)
			crv_name = cmds.rename(crv.name(), name)

			# set infinity and is weighted
			crv.setPreInfinityType(pre_infinity)
			crv.setPostInfinityType(post_infinity)
			crv.setIsWeighted(is_weighted)

			# create keys
			for i in range(len(time_list)):

				# try creating for UU type anim curves
				try:
					crv.addKey(time_list[i], value_list[i], in_type_list[i], out_type_list[i])

				# try creating for TL TA and TU type anim curves
				except:
					# try creating for ta tl and tu type anim curves
					time = OpenMaya.MTime(time_list[i])
					crv.addKey(time, value_list[i], in_type_list[i], out_type_list[i])

				# Set tangent angle and weight
				in_angle = OpenMaya.MAngle(in_angle_list[i])
				out_angle = OpenMaya.MAngle(out_angle_list[i])

				crv.setTangent(i, in_angle, in_weight_list[i], True)
				crv.setTangent(i, out_angle, out_weight_list[i], False)

			# Connect SDK
			if sdk_driver:
				sdk_driver = cmds.ls(sdk_driver)
				if sdk_driver:
					cmds.connectAttr(sdk_driver[0], crv_name + ".input")

			log.info("Created setDrivenKeyframe for: " + driven_attr)


def remap_nodes(data, remap):
	"""

	:param data:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	data = dict(data)
	for node, values in data.items():
		for search, replace in remap:
			for i, value in enumerate(values):
				driver = value.get("sdk_driver")
				name = value.get("name")

				if search in name:
					r_name = name.replace(search, replace)
					value["name"] = r_name

				if search in driver:
					r_driver = driver.replace(search, replace)
					value["sdk_driver"] = r_driver

				values[i] = value

			if search in node:
				r_node = node.replace(search, replace)
				data[r_node] = values
				del data[node]
	return data


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	nodes = []
	for node, values in data.items():
		nodes.append(node)
		for i, value in enumerate(values):
			driver = value.get("sdk_driver")
			nodes.append(driver)


def save(nodes, file_path, *args, **kwargs):
	"""

	:param nodes:
	:param file_path:
	:param args:
	:param kwargs:
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
	set_data(remap_nodes(data, remap) if remap else data)
