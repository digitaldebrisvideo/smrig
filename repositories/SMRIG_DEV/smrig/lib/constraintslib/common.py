import logging

import maya.cmds as cmds
import maya.mel as mel

from smrig.lib import api2lib
from smrig.lib import nodepathlib
from smrig.lib import selectionlib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.constraintslib.common")

MATRIX_CONSTRAINT_TAG = "smrigMatrixConstraint"

CONSTRAINT_TYPES = {
	"parentConstraint": "PRC",
	"pointConstraint": "PC",
	"orientConstraint": "OC",
	"scaleConstraint": "SC",
	"aimConstraint": "AC",
	"poleVectorConstraint": "PVC",
	"normalConstraint": "NC",
	"geometryConstraint": "GC"
}


def matrix_constraint(driver,
                      driven,
                      maintain_offset=True,
                      translate=True,
                      rotate=True,
                      scale=True,
                      matrix_plug=None):
	"""

	:param driver:
	:param driven:
	:param maintain_offset:
	:param translate:
	:param rotate:
	:param scale:
	:param matrix_plug:
	:return:
	"""
	matrix_plug = matrix_plug if matrix_plug else "worldMatrix"
	mmtx = cmds.createNode("multMatrix")
	dmtx = cmds.createNode("decomposeMatrix", n=driven + "_MTC")

	# add some attrs
	cmds.addAttr(dmtx, ln=driver.replace("|", "") + "W0", nn=driver + "W0", dv=1, k=1)
	cmds.addAttr(dmtx, ln=MATRIX_CONSTRAINT_TAG, at="message")
	cmds.addAttr(dmtx, ln="maintainOffset", at="bool", dv=maintain_offset)

	if maintain_offset:
		offset = api2lib.matrix.get_offset_matrix(driver, driven, parent_matrix_plug=matrix_plug)
		cmds.setAttr(mmtx + ".matrixIn[0]", offset, type="matrix")

	# build constraint
	cmds.connectAttr("{}.{}".format(driver, matrix_plug), mmtx + ".matrixIn[1]")
	cmds.connectAttr(driven + ".parentInverseMatrix", mmtx + ".matrixIn[2]")
	cmds.connectAttr(mmtx + ".matrixSum", dmtx + ".inputMatrix")
	cmds.setAttr(mmtx + ".ihi", 0)

	if translate:
		cmds.connectAttr(dmtx + ".outputTranslate", driven + ".t", f=1)

	if rotate:
		if cmds.nodeType(driven) == "joint":
			etq = cmds.createNode("eulerToQuat")
			qinv = cmds.createNode("quatInvert")
			qprod = cmds.createNode("quatProd")
			qte = cmds.createNode("quatToEuler")

			cmds.setAttr(etq + ".inputRotate", *cmds.getAttr(driven + ".jo")[0])
			cmds.connectAttr(etq + ".outputQuat", qinv + ".inputQuat")
			cmds.connectAttr(dmtx + ".outputQuat", qprod + ".input1Quat")
			cmds.connectAttr(qinv + ".outputQuat", qprod + ".input2Quat")
			cmds.connectAttr(qprod + ".outputQuat", qte + ".inputQuat")
			cmds.connectAttr(qte + ".outputRotate", driven + ".r", f=1)
			cmds.disconnectAttr(qinv + ".outputQuat", qprod + ".input2Quat")
			cmds.setAttr(qprod + ".ihi", 0)
			cmds.setAttr(qte + ".ihi", 0)
			cmds.delete(etq, qinv)

		else:
			cmds.connectAttr(dmtx + ".outputRotate", driven + ".r", f=1)

	if scale:
		cmds.connectAttr(dmtx + ".outputScale", driven + ".s", f=1)
		cmds.connectAttr(dmtx + ".outputShear", driven + ".shear", f=1)

	return dmtx


def matrix_constraint_multi(drivers,
                            driven,
                            maintain_offset=True,
                            translate=True,
                            rotate=True,
                            scale=False,
                            weighted=False,
                            split=False,
                            matrix_plug="worldMatrix"):
	"""
	Matrix constraint with multiple drivers.

	:param drivers:
	:param driven:
	:param maintain_offset:
	:param translate:
	:param rotate:
	:param scale:
	:param weighted:
	:param split:
	:param matrix_plug:
	:return:
	"""
	dmtx = cmds.createNode("decomposeMatrix", n=driven + "_MTC")
	wtmtx = cmds.createNode("wtAddMatrix") if weighted else cmds.createNode("choice")
	cmds.connectAttr(wtmtx + ".o", dmtx + ".inputMatrix")

	if split:
		ro_dmtx = cmds.createNode("decomposeMatrix", n=driven + "_MTC")
		ro_wtmtx = cmds.createNode("wtAddMatrix") if weighted else cmds.createNode("choice")
		cmds.connectAttr(ro_wtmtx + ".o", ro_dmtx + ".inputMatrix")
	else:
		ro_wtmtx = wtmtx
		ro_dmtx = dmtx

	for i, driver in enumerate(drivers):
		mmtx = cmds.createNode("multMatrix")

		if maintain_offset:
			offset = api2lib.matrix.get_offset_matrix(driver, driven, parent_matrix_plug=matrix_plug)
			cmds.setAttr(mmtx + ".matrixIn[0]", offset, type="matrix")

		# build constraint
		cmds.connectAttr("{}.{}".format(driver, matrix_plug), mmtx + ".matrixIn[1]")
		cmds.connectAttr(driven + ".parentInverseMatrix", mmtx + ".matrixIn[2]")

		if weighted:
			dv = 1 if i == 0 else 0
			cmds.addAttr(wtmtx, ln="{}W{}".format(driver, i), min=0, max=1, dv=dv, k=1)
			cmds.connectAttr("{}.{}W{}".format(wtmtx, driver, i), "{}.wtMatrix[{}].weightIn ".format(wtmtx, i))
			cmds.connectAttr(mmtx + ".matrixSum", "{}.wtMatrix[{}].matrixIn".format(wtmtx, i))

		else:
			cmds.connectAttr(mmtx + ".matrixSum", "{}.input[{}]".format(wtmtx, i))

		if split:
			if weighted:
				dv = 1 if i == 0 else 0
				cmds.addAttr(ro_wtmtx, ln="{}W{}".format(driver, i), sn="w{}".format(i), min=0, max=1, dv=dv, k=1)
				cmds.connectAttr("{}.{}W{}".format(ro_wtmtx, driver, i),
				                 "{}.wtMatrix[{}].weightIn ".format(ro_wtmtx, i))
				cmds.connectAttr(mmtx + ".matrixSum", "{}.wtMatrix[{}].matrixIn".format(ro_wtmtx, i))

			else:
				cmds.connectAttr(mmtx + ".matrixSum", "{}.input[{}]".format(ro_wtmtx, i))

	if translate:
		cmds.connectAttr(dmtx + ".outputTranslate", driven + ".t", f=1)

	if rotate:
		if cmds.nodeType(driven) == "joint":
			etq = cmds.createNode("eulerToQuat")
			qinv = cmds.createNode("quatInvert")
			qprod = cmds.createNode("quatProd")
			qte = cmds.createNode("quatToEuler")

			cmds.connectAttr(ro_dmtx + ".outputQuat", qprod + ".input1Quat")
			cmds.setAttr(etq + ".inputRotate", *cmds.getAttr(driven + ".jo")[0])
			cmds.connectAttr(etq + ".outputQuat", qinv + ".inputQuat")
			cmds.connectAttr(qinv + ".outputQuat", qprod + ".input2Quat")
			cmds.connectAttr(qprod + ".outputQuat", qte + ".inputQuat")
			cmds.connectAttr(qte + ".outputRotate", driven + ".r", f=1)
			cmds.disconnectAttr(qinv + ".outputQuat", qprod + ".input2Quat")
			cmds.setAttr(qprod + ".ihi", 0)
			cmds.setAttr(qte + ".ihi", 0)
			cmds.delete(etq, qinv)

		else:
			cmds.connectAttr(ro_dmtx + ".outputRotate", driven + ".r", f=1)

	if scale:
		cmds.connectAttr(dmtx + ".outputScale", driven + ".s", f=1)
		cmds.connectAttr(dmtx + ".outputShear", driven + ".shear", f=1)

	if split:
		return wtmtx, ro_wtmtx
	else:
		return wtmtx


def transform_constraint(
		targets,
		destination,
		translate=True,
		rotate=True,
		scale=False,
		maintain_offset=False,
		interpolation_type=0,
):
	"""
	:param str/list targets:
	:param str destination:
	:param str/bool/list/tuple translate:
	:param str/bool/list/tuple rotate:
	:param str/bool/list/tuple scale:
	:param bool maintain_offset:
	:param interpolation_type:
	:return: Constraints
	:rtype: list
	:raise ValueError: When no channels are provided to be constraint.
	"""

	def get_skip_axis(input_):
		"""
		:param str/bool/list/tuple input_:
		:return: Skip axis
		:rtype: list
		"""
		axis = ["x", "y", "z"]
		if isinstance(input_, bool):
			input_ = axis if input_ else []

		return utilslib.conversion.get_difference(axis, input_)

	# validate channels
	if not translate and not rotate and not scale:
		error_message = "No channels provided to constraint."
		log.error(error_message)
		raise ValueError(error_message)

	# variable
	constraints = []

	# do parent constraint
	if translate or rotate:
		# get skip axis
		key = "".join([k for k, v in zip(["T", "R"], [translate, rotate]) if v])
		skip_translate = get_skip_axis(translate)
		skip_rotate = get_skip_axis(rotate)

		# get name
		parent_constraint_names = [nodepathlib.get_leaf_name(destination),
		                           key + CONSTRAINT_TYPES.get("parentConstraint")]
		parent_constraint_name = "_".join(parent_constraint_names)

		# do constraint
		try:
			parent_constraint = cmds.parentConstraint(
				targets,
				destination,
				maintainOffset=maintain_offset,
				skipTranslate=skip_translate,
				skipRotate=skip_rotate,
			)[0]

		# Added in some more information on the error
		except RuntimeError as e:
			raise RuntimeError("constraint failed on {} with error :{}".format(destination, e))

		# update constraint
		cmds.setAttr("{}.interpType".format(parent_constraint), interpolation_type)
		parent_constraint = cmds.rename(parent_constraint, parent_constraint_name)
		constraints.append(parent_constraint)

	if scale:
		# get skip axis
		skip_scale = get_skip_axis(scale)

		# get name
		scale_constraint_names = [nodepathlib.get_leaf_name(destination), CONSTRAINT_TYPES.get("scaleConstraint")]
		scale_constraint_name = "_".join(scale_constraint_names)

		# do constraint
		scale_constraint = cmds.scaleConstraint(
			targets,
			destination,
			maintainOffset=maintain_offset,
			skip=skip_scale,
		)[0]

		# update constraint
		scale_constraint = cmds.rename(scale_constraint, scale_constraint_name)
		constraints.append(scale_constraint)

	return constraints


def weighted_constraint(mesh, nodes, values=[]):
	"""

	:param mesh:
	:param nodes:
	:param values:
	:return:
	"""
	nodes = cmds.ls(nodes)
	cpom = cmds.createNode('closestPointOnMesh')
	shape = selectionlib.get_shapes(mesh)[0]

	cmds.connectAttr(shape + '.outMesh', cpom + '.inMesh')

	for node in nodes:

		scls = mel.eval('findRelatedSkinCluster ' + mesh)

		pos = cmds.xform(node, q=1, ws=1, t=1)
		cmds.setAttr(cpom + '.inPosition', pos[0], pos[1], pos[2])
		vert = mesh + '.vtx[{0}]'.format(cmds.getAttr(cpom + '.closestVertexIndex'))

		existing_cons = get_constraints_from_target(node)
		if existing_cons:
			cmds.delete(existing_cons)

		# get influences
		if values:
			sorted_influences = values

		else:
			infs = cmds.skinCluster(scls, q=1, inf=1)

			# get values
			weighted_influences = {}
			values = []
			for inf in infs:
				val = cmds.skinPercent(scls, vert, q=1, t=inf, v=1)
				val = round(val, 3)

				if val > 0.0:
					weighted_influences[inf] = val
					values.append(val)

			values.sort()
			values.reverse()

			sorted_influences = []
			for sv in values:
				for inf, val in weighted_influences.items():
					if val == sv:
						sorted_influences.append([inf, val])

		suffix = "PRC"
		for si in sorted_influences:
			prc = cmds.parentConstraint(si[0], node, n=node + '_' + suffix, mo=1, weight=si[1])[0]

		cmds.setAttr(prc + '.interpType', 2)
		cmds.addAttr(prc, ln='weighted_constraint', at='message')

	cmds.delete(cpom)
	cmds.select(nodes)


def aim_constraint_chain(drivers, joints, aim=None, up=None, wup=None, mo=False, mirror_value=1):
	"""
	Drivers and joints must have the same list length

	:param drivers:
	:param joints:
	:param aim:
	:param up:
	:param wup:
	:param mo:
	:param mirror_value:
	:return:
	"""
	aim = aim if aim else [mirror_value, 0, 0]
	up = up if up else [0, 0, 1]
	wup = wup if wup else [0, 0, 1]

	constraints = []
	for i in range(len(joints[:-1])):
		con_name = "{}_AC".format(joints[i])
		constraints.extend(cmds.aimConstraint(drivers[i + 1], joints[i], mo=mo,
		                                      aim=aim, u=up, wu=wup, wut="objectRotation", wuo=drivers[i], n=con_name))

	return constraints


def get_constraints_from_target(target, constraint_type="constraint", channel=None):
	"""
	Get constraint of a specific type from a target. It is possible to provide
	a channel in case two parent constraints drive the same target but
	isolating translation from rotation.

	:param str target:
	:param str/None constraint_type:
	:param str/None channel: "translate", "rotate", "scale"
	:return: Constraints
	:rtype: list
	"""
	target_paths = target if not channel else ["{}.{}{}".format(target, channel, axis) for axis in ["X", "Y", "Z"]]
	constraints = cmds.listConnections(target_paths, source=True, destination=False) or []
	constraints = selectionlib.filter_by_type(constraints, types=constraint_type)

	return list(set(constraints))


def get_matrix_constraints_from_target(target):
	"""

	:param target:
	:return:
	"""
	constraints = cmds.listConnections(target, source=True, destination=False) or []
	matrix_constraints = [c for c in constraints if cmds.objExists(c + "." + MATRIX_CONSTRAINT_TAG)]
	return list(set(matrix_constraints))


def get_constraint_command(constraint_type):
	"""
	Get the constraint command from a string constraint type value. Ideal when
	working with a list of constraint and it is unsure what type of
	constraints they are.

	Example:
	.. code-block:: python

			constraint_type = cmds.nodeType(constraint)
			constraint_func = get_constraint_command(constraint_type)
			constraint_func(constraint, query=True, weightAliasList=True)

	:param str constraint_type:
	:return: Constraint method associated with constraint type
	:rtype: method
	:raise ValueError:
		When the constraint type has no method associated with it
	"""
	func = cmds.__dict__.get(constraint_type)

	if not func:
		error_message = "Constraint type of '{}' has no function associated with it.".format(constraint_type)
		log.error(error_message)
		raise ValueError(error_message)

	return func


def rename_constraints():
	"""
	Rename all constraint in CONSTRAINTS_TYPES list. It is assumed non of the
	constraint have custom names as it stripes away the constraint type from
	the name and replaces it with the suffix provided from the dictionary.
	"""
	for constraint_type, suffix in CONSTRAINT_TYPES.items():
		constraints = cmds.ls(type=constraint_type) or []

		for constraint in constraints:
			if not constraint.count(constraint_type):
				continue

			base = nodepathlib.get_leaf_name(constraint)
			base = base.rsplit(constraint_type, 1)[0]
			cmds.rename(constraint, base + suffix)
