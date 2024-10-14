import logging
import re

from maya import cmds

log = logging.getLogger("deformerIO.types.mayaconstraint")

deformer_type = "mayaConstraint"
file_type = "json"

constraint_types = {"pointConstraint": cmds.pointConstraint,
                    "orientConstraint": cmds.orientConstraint,
                    "parentConstraint": cmds.parentConstraint,
                    "scaleConstraint": cmds.scaleConstraint,
                    "aimConstraint": cmds.aimConstraint,
                    "normalConstraint": cmds.normalConstraint,
                    "poleVectorConstraint": cmds.poleVectorConstraint,
                    "tangentConstraint": cmds.tangentConstraint,
                    "geometryConstraint": cmds.geometryConstraint,
                    "pointOnPolyConstraint": cmds.pointOnPolyConstraint}


def get_data(constraint):
	"""
	Get constraint data

	:param constraint:
	:return:
	"""

	# get driven target nodes
	node_type = cmds.nodeType(constraint)
	constraint_func = constraint_types.get(node_type)

	driven = cmds.listConnections(constraint + ".constraintParentInverseMatrix") or []
	drivers = constraint_func(constraint, q=1, tl=1)

	data = {"name": constraint,
	        "constraint_type": node_type,
	        "drivers": drivers,
	        "driven": list(set(driven)),
	        "skip_translate": [],
	        "skip_rotate": [],
	        "skip_scale": [],
	        "weight_list": [cmds.getAttr(constraint + "." + w) for w in constraint_func(constraint, q=1, wal=1)]}

	if node_type in ["pointConstraint", "parentConstraint"]:
		data["skip_translate"] = get_skip_attrs(constraint, "translate")

	if node_type in ["orientConstraint", "aimConstraint", "parentConstraint"]:
		data["skip_rotate"] = get_skip_attrs(constraint, "rotate")

	if node_type in ["scaleConstraint"]:
		data["skip_scale"] = get_skip_attrs(constraint, "scale")

	if node_type in ["aimConstraint", "tangentConstraint", "normalConstraint"]:
		wuo = constraint_func(constraint, q=1, wuo=1)
		data["aim"] = constraint_func(constraint, q=1, aim=1)
		data["u"] = constraint_func(constraint, q=1, u=1)
		data["wu"] = constraint_func(constraint, q=1, wu=1)
		data["wut"] = constraint_func(constraint, q=1, wut=1)
		data["wuo"] = wuo if type(wuo) == list else [wuo]

	if cmds.objExists(constraint + ".interpType"):
		data["interp_type"] = cmds.getAttr(constraint + ".interpType")

	return data


def set_data(data):
	"""
	Set constraint data

	:param data:
	:return:
	"""
	name = data.get("name")
	node_type = data.get("constraint_type")
	drivers = data.get("drivers")
	driven = data.get("driven")
	weight_list = data.get("weight_list")
	interp_type = data.get("interp_type")
	skip_translate = data.get("skip_translate")
	skip_rotate = data.get("skip_rotate")

	constraint_func = constraint_types.get(node_type)
	constraint = None

	try:
		if node_type in ["aimConstraint", "tangentConstraint", "normalConstraint"]:
			for i, driver in enumerate(drivers):
				if data["wuo"]:
					constraint = constraint_func(driver,
					                             driven,
					                             name=name,
					                             aim=data["aim"],
					                             u=data["u"],
					                             wu=data["wu"],
					                             wut=data["wut"],
					                             wuo=data["wuo"][0],
					                             mo=1,
					                             w=weight_list[i])[0]
				else:
					constraint = constraint_func(driver,
					                             driven,
					                             name=name,
					                             aim=data["aim"],
					                             u=data["u"],
					                             wu=data["wu"],
					                             wut=data["wut"],
					                             mo=1,
					                             w=weight_list[i])[0]

		else:
			for i, driver in enumerate(drivers):
				if node_type == "parentConstraint":
					constraint = constraint_func(driver,
					                             driven,
					                             name=name,
					                             mo=1,
					                             st=skip_translate,
					                             sr=skip_rotate,
					                             w=weight_list[i])[0]

				else:
					try:
						constraint = constraint_func(driver, driven, name=name, mo=1, w=weight_list[i])[0]
					except:
						constraint = constraint_func(driver, driven, name=name, w=weight_list[i])[0]

		if cmds.objExists(constraint + ".interpType"):
			cmds.setAttr(constraint + ".interpType", interp_type)

	except:
		log.warning("Cannot create constraint on {}. Attributes may be locked or connected.".format(driven))


def get_skip_attrs(constraint, attr):
	"""

	:param constraint:
	:param attr: translate, rotate or scale
	:return:
	"""
	skip_attrs = []
	if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".{}X".format(attr), c)]:
		skip_attrs.append("x")
	if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".{}Y".format(attr), c)]:
		skip_attrs.append("y")
	if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".{}Z".format(attr), c)]:
		skip_attrs.append("z")

	return skip_attrs
