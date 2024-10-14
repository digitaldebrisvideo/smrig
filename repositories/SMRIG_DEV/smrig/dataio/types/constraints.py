import logging
import re

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import iolib
from smrig.lib import utilslib

deformer_type = "constraint"
file_extension = "con"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))

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


def get_data(constraints):
	"""

	:param constraints:
	:return:
	"""
	constraints = utilslib.conversion.as_list(constraints)
	constraints = [n for n in constraints if cmds.nodeType(n) in constraint_types]

	data = {}
	for constraint in constraints:

		# get driven target nodes
		ntype = cmds.nodeType(constraint)
		constraint_func = constraint_types.get(ntype)
		driven = cmds.listConnections(constraint + ".constraintParentInverseMatrix") or []
		drivers = constraint_func(constraint, q=1, tl=1)

		if ntype not in constraint_types or not driven or not drivers:
			continue

		con_data = {
			"con_type": ntype,
			"drivers": drivers,
			"driven": list(set(driven)),
			"weight_list": [cmds.getAttr(constraint + "." + w) for w in constraint_func(constraint, q=1, wal=1)]
		}

		if ntype == "parentConstraint":
			skip_tranlate = []
			if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".translateX", c)]:
				skip_tranlate.append("x")
			if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".translateY", c)]:
				skip_tranlate.append("y")
			if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".translateZ", c)]:
				skip_tranlate.append("z")

			skip_rotate = []
			if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".rotateX", c)]:
				skip_rotate.append("x")
			if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".rotateY", c)]:
				skip_rotate.append("y")
			if not [c for c in cmds.listConnections(constraint, p=True) or [] if re.search(".rotateZ", c)]:
				skip_rotate.append("z")

			con_data["skip_translate"] = skip_tranlate
			con_data["skip_rotate"] = skip_rotate

		if ntype in ["aimConstraint", "tangentConstraint", "normalConstraint"]:
			wuo = constraint_func(constraint, q=1, wuo=1)

			con_data["aim"] = constraint_func(constraint, q=1, aim=1)
			con_data["u"] = constraint_func(constraint, q=1, u=1)
			con_data["wu"] = constraint_func(constraint, q=1, wu=1)
			con_data["wut"] = constraint_func(constraint, q=1, wut=1)
			con_data["wuo"] = wuo[0] if type(wuo) == list else wuo

		if cmds.objExists(constraint + ".interpType"):
			con_data["interp_type"] = cmds.getAttr(constraint + ".interpType")

		data[constraint] = con_data

	return data


def set_data(data):
	"""

	:param data:
	:return:
	"""

	for name, con_data in data.items():

		# get dataexporter
		ntype = con_data.get("con_type")
		drivers = con_data.get("drivers")
		driven = con_data.get("driven")
		weight_list = con_data.get("weight_list")
		interp_type = con_data.get("interp_type")
		skip_translate = con_data.get("skip_translate")
		skip_rotate = con_data.get("skip_rotate")

		constraint_func = constraint_types.get(ntype)
		constraint = None

		if utils.check_missing_nodes(name, drivers + driven):
			continue

		# Recreate constraints with aim and ups
		try:
			if ntype in ["aimConstraint", "tangentConstraint", "normalConstraint"]:
				for i, driver in enumerate(drivers):
					if con_data["wuo"]:
						constraint = constraint_func(driver,
						                             driven,
						                             name=name,
						                             aim=con_data["aim"],
						                             u=con_data["u"],
						                             wu=con_data["wu"],
						                             wut=con_data["wut"],
						                             wuo=con_data["wuo"],
						                             mo=1,
						                             w=weight_list[i])[0]
					else:
						constraint = constraint_func(driver,
						                             driven,
						                             name=name,
						                             aim=con_data["aim"],
						                             u=con_data["u"],
						                             wu=con_data["wu"],
						                             wut=con_data["wut"],
						                             mo=1,
						                             w=weight_list[i])[0]

			else:
				for i, driver in enumerate(drivers):
					if ntype == "parentConstraint":
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
			log.warning("Could not create constraint: {}".format(name))
			continue

		log.info("Loaded {}".format(name))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	nodes = []
	data = iolib.json.read(file_path)
	for name, con_data in data.items():
		# get dataexporter
		drivers = con_data.get("drivers")
		driven = con_data.get("driven")

		nodes.extend(drivers + driven)

	return nodes


def remap_nodes(data, remap):
	"""

	:param shapes:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	data = dict(data)
	for search, replace in remap:
		for key, con_data in data.items():

			drivers = list(con_data.get("drivers"))
			for i, driver in enumerate(drivers):
				if search in driver:
					drivers[i] = driver.replace(search, replace)
			data[key]["drivers"] = drivers

			drivens = list(con_data.get("driven"))
			for i, driven in enumerate(drivens):
				if search in driven:
					drivens[i] = driven.replace(search, replace)
			data[key]["driven"] = drivens

	return data


def save(constraints, file_path):
	"""

	:param constraints:
	:param file_path:
	:return:
	"""
	iolib.json.write(file_path, get_data(constraints))
	log.info("Saved {} to: {}".format(constraints, file_path))


def load(file_path, *args, **kwargs):
	"""

	:param file_path:
	:param method:
	:param args:
	:param kwargs:
	:return:
	"""
	remap = kwargs.get("remap")
	data = iolib.json.read(file_path)
	set_data(remap_nodes(data, remap) if remap else data)
