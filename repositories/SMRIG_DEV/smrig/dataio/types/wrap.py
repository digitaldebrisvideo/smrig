import logging

import maya.cmds as cmds
from smrig.dataio import utils
from smrig.lib import deformlib
from smrig.lib import iolib
from smrig.lib import utilslib

deformer_type = "wrap"
file_extension = "wrap"
log = logging.getLogger("smrig.dataexporter.types.{}".format(deformer_type))

attrs = ["envelope",
         "weightThreshold",
         "maxDistance",
         "autoWeightThreshold",
         "exclusiveBind",
         "falloffMode"]


def get_data(wraps):
	"""

	:param constraints:
	:return:
	"""
	wraps = utilslib.conversion.as_list(wraps)
	data = {}

	for wrap in wraps:
		out_meshes = cmds.listConnections(wrap + ".outputGeometry")
		in_meshes = cmds.listConnections(wrap + ".driverPoints")

		data[wrap] = {
			"outMeshes": out_meshes,
			"inMeshes": in_meshes,
		}

		for attr in attrs:
			data[wrap][attr] = cmds.getAttr("{}.{}".format(wrap, attr))

	return data


def set_data(data):
	"""

	:param data:
	:return:
	"""
	for name, cdata in data.items():
		out_meshes = cdata.get("outMeshes")
		in_meshes = cdata.get("inMeshes")

		if not out_meshes or not in_meshes:
			continue

		if utils.check_missing_nodes(name, out_meshes + in_meshes):
			continue

		wrap = list(deformlib.wrap.create(in_meshes[0], out_meshes))
		wrap[0] = cmds.rename(wrap[0], name)

		for attr in attrs:
			cmds.setAttr("{}.{}".format(wrap[0], attr), cdata.get(attr))

		log.info("Loaded {}".format(name))


def get_required_nodes(file_path):
	"""

	:param file_path:
	:return:
	"""
	data = iolib.json.read(file_path)
	nodes = []

	for name, cdata in data.items():
		nodes.extend(cdata.get("outMeshes") + cdata.get("inMeshes"))

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
		out_meshes = cdata.get("outMeshes")
		in_meshes = cdata.get("inMeshes")

		for search, replace in remap:
			# remap shape
			for i in range(out_meshes):
				if search in out_meshes[i]:
					out_meshes[i] = out_meshes[i].replace(search, replace)

			for i in range(in_meshes):
				if search in in_meshes[i]:
					in_meshes[i] = in_meshes[i].replace(search, replace)

		cdata["outMeshes"] = out_meshes
		cdata["inMeshes"] = in_meshes
		data[name] = cdata

	return data


def save(wraps, file_path):
	"""

	:param constraints:
	:param file_path:
	:return:
	"""
	iolib.json.write(file_path, get_data(wraps))
	log.info("Saved {} to: {}".format(wraps, file_path))


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
