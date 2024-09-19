import logging

import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim
import maya.cmds as cmds

deformer_type = "setDrivenKeyframe"
file_type = "json"

log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))


def get_data(node, **kwargs):
	"""

	:param node:
	:param kwargs:
	:return:
	"""
	curves = cmds.listConnections(node, s=1, d=0, type="animCurve", scn=1) or []
	blend_weighted = cmds.listConnections(node, s=1, d=0, type="blendWeighted", scn=1) or []
	for blend in blend_weighted:
		curves.extend(cmds.listConnections(blend, s=1, d=0, type="animCurve", scn=1) or [])

	# initialize dataexporter dict
	data = {"name": node,
	        "nodes": [node],
	        "curves": [],
	        "deformer_type": deformer_type}

	# for each curve get dataexporter
	for i, crv in enumerate(curves):

		driven_attr = get_driven_attr(crv)
		if not driven_attr:
			continue

		# get curve obj
		m_list = OpenMaya.MSelectionList()
		m_list.add(crv)

		m_obj = m_list.getDependNode(0)
		crv_obj = OpenMayaAnim.MFnAnimCurve(m_obj)

		# get sdk driver and driven
		sdk_driver = cmds.listConnections(crv + ".input", s=1, d=0, p=1, scn=1)
		sdk_driver = sdk_driver[0] if sdk_driver else None

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
		crv_data = {"name": crv,
		            "driven_attr": driven_attr,
		            "sdk_driver": sdk_driver,
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
		            "out_weight_list": out_weight_list}

		data["curves"].append(crv_data)

	return data


def get_driven_attr(curve):
	"""

	:param curve:
	:return:
	"""
	attr = cmds.listConnections(curve + ".output", s=0, d=1, p=1, scn=1)
	if not attr:
		return
	if cmds.nodeType(attr[0]) in "blendWeighted":
		attr = cmds.listConnections(attr[0].split(".")[0] + ".output", s=0, d=1, p=1, scn=1)

	return attr[0] if attr else None


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


def set_data(data, **kwargs):
	"""

	:param data:
	:param kwargs:
	:return:
	"""
	for crv_data in data.get("curves"):
		driven_attr = crv_data.get("driven_attr")
		if not driven_attr:
			log.warning("Attribute does not exist: {}. Skipping...".format(driven_attr))
			continue

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
		print(sdk_driver)

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
