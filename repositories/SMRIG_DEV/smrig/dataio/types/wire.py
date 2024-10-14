import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import iolib
from smrig.lib import selectionlib
from smrig.lib import utilslib

deformer_type = "wire"
file_extension = "wire"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))

attrs = ["envelope", "scale[0]", "dropoffDistance[0]", "rotation", "localInfluence", "tension", "crossingEffect"]


def get_data(wires):
	"""

	:param constraints:
	:return:
	"""
	wires = utilslib.conversion.as_list(wires)
	data = {}

	for wire in wires:
		geos = [selectionlib.get_transform(g) for g in cmds.wire(wire, q=True, g=True)]
		crvs = [selectionlib.get_transform(g) for g in cmds.wire(wire, q=True, w=True)]

		geos = cmds.ls(geos)
		crvs = cmds.ls(crvs)

		base = cmds.listConnections(wire + ".baseWire[0]")
		base = cmds.ls(selectionlib.get_transform(base)) if base else None
		base = base[0] if base else None
		base_parent = selectionlib.get_parent(base) if base else None

		data[wire] = {
			"geos": geos,
			"curves": crvs,
			"base": base,
			"base_parent": base_parent
		}

		for attr in attrs:
			data[wire][attr] = cmds.getAttr("{}.{}".format(wire, attr))

	return data


def set_data(data):
	"""

	:param data:
	:return:
	"""
	for name, cdata in data.items():
		geos = cdata.get("geos")
		crvs = cdata.get("curves")
		base_parent = cdata.get("base_parent")

		if not geos or not crvs:
			continue

		if utils.check_missing_nodes(name, geos + crvs + [base_parent]):
			continue

		wire = cmds.wire(geos, w=crvs, gw=False, ce=0.0, li=0.0, en=1.0)
		wire[0] = cmds.rename(wire[0], name)

		base = cmds.listConnections(wire[0] + ".baseWire[0]")
		base = cmds.ls(selectionlib.get_transform(base)) if base else None

		c_parent = cmds.ls(selectionlib.get_parent(base)) if base else None
		c_parent = c_parent[0] if c_parent else None

		if base and base_parent and c_parent != base_parent:
			cmds.parent(base, base_parent)

		for attr in attrs:
			cmds.setAttr("{}.{}".format(wire[0], attr), cdata.get(attr))

		log.info("Loaded {}".format(name))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	nodes = []

	for name, cdata in data.items():
		nodes.extend(cdata.get("geos") + cdata.get("curves") + [cdata.get("base_parent")])

	return nodes


def remap_nodes(data, remap):
	"""

	:param data:
	:param remap:
	:return:
	"""
	if not remap:
		return data

	for name, cdata in dict(data).items():

		cdata = dict(cdata)
		geos = cdata.get("geos")
		crvs = cdata.get("curves")
		base_parent = cdata.get("base_parent")

		for search, replace in remap:

			# remap shape
			for i in range(geos):
				if search in geos[i]:
					geos[i] = geos[i].replace(search, replace)

			for i in range(crvs):
				if search in crvs[i]:
					crvs[i] = crvs[i].replace(search, replace)

			if base_parent and search in base_parent:
				cdata["parent"] = base_parent.replace(search, replace)

		cdata["geos"] = geos
		cdata["curves"] = crvs
		data[name] = cdata

	return data


def save(wires, file_path):
	"""

	:param constraints:
	:param file_path:
	:return:
	"""
	iolib.json.write(file_path, get_data(wires))
	log.info("Saved {} to: {}".format(wires, file_path))


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
