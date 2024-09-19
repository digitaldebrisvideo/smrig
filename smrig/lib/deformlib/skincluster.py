import logging

import maya.cmds as cmds

from smrig.lib import selectionlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.dataexporter.deformlib.skincluster")


def copy_bind(source_shape, targets, surface_association="closestPoint"):
	"""

	:param source_shape:
	:param targets:
	:param surface_association:
	:return:
	"""
	targets = utilslib.conversion.as_list(targets)
	valid_types = ["mesh", "nurbsCurve", "nurbsSurface"]

	# get deformer dataexporter
	source_deformer = selectionlib.get_history(source_shape, types="skinCluster")[0]

	influences = cmds.skinCluster(source_deformer, q=1, inf=1)
	skinning_method = cmds.getAttr(source_deformer + ".skinningMethod")
	normalize_weights = cmds.getAttr(source_deformer + ".normalizeWeights")
	deform_normals = cmds.getAttr(source_deformer + ".deformUserNormals")

	# loop throug hall targets and copy bind
	for target in targets:

		# check shapes
		shapes = selectionlib.get_shapes(target)
		target_shape = [s for s in shapes if cmds.nodeType(s) in valid_types]

		if shapes and not target_shape:
			log.warning("Shape: {0} is not valid! Skipping..".format(shapes[0]))
			continue

		# unbind IF its already bound
		if selectionlib.get_history(target, types="skinCluster"):
			cmds.skinCluster(target, e=1, ub=1)

		# bind target geo
		target_deformer = cmds.skinCluster(target_shape[0], influences, tsb=1)[0]
		cmds.setAttr(target_deformer + ".deformUserNormals", deform_normals)
		cmds.setAttr(target_deformer + ".skinningMethod", skinning_method)
		cmds.setAttr(target_deformer + ".normalizeWeights", normalize_weights)

		# copy weights
		cmds.copySkinWeights(ss=source_deformer, ds=target_deformer, nm=1, sa=surface_association, ia="oneToOne")
		# cmds.copySkinWeights(ss=source_deformer, ds=target_deformer, nm=1, nbw=1, sa=surface_association, ia="oneToOne")

		log.info("Copied skinCluster from: {} to: {} ({})".format(source_shape, target, surface_association))


def add_influences_from_source(source_shape, targets):
	"""

	:param source_shape:
	:param targets:
	:return:
	"""
	targets = utilslib.conversion.as_list(targets)
	valid_types = ["mesh", "nurbsCurve", "nurbsSurface"]

	# get deformer dataexporter
	source_deformer = selectionlib.get_history(source_shape, types="skinCluster")[0]
	influences = cmds.skinCluster(source_deformer, q=1, inf=1)

	# loop throug hall targets and copy bind
	for target in targets:

		# check shapes
		shapes = selectionlib.get_shapes(target)
		target_shape = [s for s in shapes if cmds.nodeType(s) in valid_types]

		if shapes and not target_shape:
			log.warning("Shape: {0} is not valid! Skipping..".format(shapes[0]))
			continue

		# unbind IF its already bound
		target_scls = selectionlib.get_history(target, types="skinCluster")
		if not target_scls:
			log.warning("{} has no skinCluster".format(target))

		for inf in influences:
			try:
				cmds.skinCluster(target_scls, e=True, lw=True, wt=0, ai=inf)
			except:
				log.warning("Cannot add influence: {}, It is possibly already added.".format(inf))

		log.info("Added influences from: {} to: {}".format(source_shape, target))


def get_influences(source_shapes):
	"""

	:param source_shapes:
	:return:
	"""
	source_shapes = utilslib.conversion.as_list(source_shapes)
	influences = []

	for shape in source_shapes:
		source_deformer = selectionlib.get_history(shape, types="skinCluster")[0]
		influences.extend(cmds.skinCluster(source_deformer, q=1, inf=1))

	return influences


def print_influences(source_shapes):
	"""

	:param source_shapes:
	:return:
	"""
	influences = get_influences(source_shapes)
	messgae = "Total influences: {}\n".format(len(influences))
	for inf in influences:
		messgae += "\t{}\n".format(inf)

	log.info(messgae)
