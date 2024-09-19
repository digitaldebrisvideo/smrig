import logging

import maya.cmds as cmds
import maya.mel as mel

from smrig.lib import nodeslib
from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.geometrylib.curve")

MIRROR_PLANE = {"x": [-1, 1, 1], "y": [1, -1, 1], "z": [1, 1, -1]}


def create_surface_link(targets,
                        name=None,
                        parent=None,
                        degree=3,
                        axis="X",
                        direction="U",
                        normalize=True,
                        width=None,
                        display_type="template"):
	"""
	Create a nurbs surface ribbon from controls.
	Uses decompose matrix nodes to drive the curve and surface points.surface.

	:param targets:
	:param name:
	:param parent:
	:param degree:
	:param axis:
	:param direction:
	:param normalize:
	:param width:
	:param display_type:
	:return:
	"""
	name = name if name else targets[0] + "_SURF"
	width = width if width else utilslib.distance.get(targets[0], targets[1]) * 0.4

	locs0 = [cmds.createNode("locator", n="{}0_pnt{}_LOC".format(name, i), p=targets[i]) for i in range(len(targets))]
	locs1 = [cmds.createNode("locator", n="{}1_pnt{}_LOC".format(name, i), p=targets[i]) for i in range(len(targets))]

	for loc0, loc1 in zip(locs0, locs1):
		cmds.setAttr("{}.localPosition{}".format(loc0, axis.upper()), width * 0.5)
		cmds.setAttr("{}.localPosition{}".format(loc1, axis.upper()), width * -0.5)

	surf = cmds.nurbsPlane(ch=0, ax=[0, 1, 0])
	spans = len(targets) - 3 if degree == 3 else len(targets) - 2 if degree == 2 else len(targets)
	kr = 0 if normalize else 2

	if direction.upper() == "U":
		surf = cmds.rename(cmds.rebuildSurface(surf, ch=False, rpo=1, rt=0, end=1, kr=kr, kcp=0, kc=0,
		                                       su=spans, du=degree, sv=0, dv=1, tol=0.01, fr=0, dir=2)[0], name)

		cv_idx = 0
		for i in range(len(locs0)):
			loc0 = locs0[i]
			loc1 = locs1[i]

			cv0 = "{}.controlPoints[{}]".format(surf, cv_idx)
			cmds.connectAttr("{}.worldPosition".format(loc0), cv0)
			cv_idx += 1

			cv1 = "{}.controlPoints[{}]".format(surf, cv_idx)
			cmds.connectAttr("{}.worldPosition".format(loc1), cv1)
			cv_idx += 1

	else:
		surf = cmds.rename(cmds.rebuildSurface(surf, ch=False, rpo=1, rt=0, end=1, kr=kr, kcp=0, kc=0,
		                                       sv=spans, dv=degree, su=0, du=1, tol=0.01, fr=0, dir=2)[0], name)

		for idx, loc in enumerate(locs1 + locs0):
			cvs = "{}.controlPoints[{}]".format(surf, idx)
			cmds.connectAttr("{}.worldPosition".format(loc), cvs)

	if parent:
		cmds.parent(surf, parent)

	cmds.hide(locs0, locs1)
	nodeslib.display.set_display_type(surf, display_type=display_type)

	return surf


def create_surface_from_points(targets, name=None, parent=None, degree=3, axis="X", width=None):
	"""
	Create a lofted ribbon and surface from controls.
	Uses decompose matrix nodes to drive the curve and surface points.surface.

	:param targets:
	:param name:
	:param degree:
	:param axis:
	:param width:
	:param parent:
	:param stretch:
	:return:
	"""
	name = name if name else targets[0] + "_SURF"
	width = width if width else utilslib.distance.get(targets[0], targets[1]) * 0.4

	locs0 = [cmds.createNode("locator", n="{}0_pnt{}_LOC".format(name, i), p=targets[i]) for i in range(len(targets))]
	locs1 = [cmds.createNode("locator", n="{}1_pnt{}_LOC".format(name, i), p=targets[i]) for i in range(len(targets))]
	cmds.hide(locs0, locs1)

	for loc0, loc1 in zip(locs0, locs1):
		cmds.setAttr("{}.localPosition{}".format(loc0, axis.upper()), width * 0.5)
		cmds.setAttr("{}.localPosition{}".format(loc1, axis.upper()), width * -0.5)

	surf = cmds.nurbsPlane(ch=0, ax=[0, 1, 0])
	spans = len(targets) - 3 if degree == 3 else len(targets) - 3

	surf = cmds.rename(cmds.rebuildSurface(surf, ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kc=0,
	                                       su=spans, du=degree, sv=0, dv=1, tol=0.01, fr=0, dir=2)[0], name)

	# now connect locator world pos to surf cvs
	cv_idx = 0
	for i in range(len(locs0)):
		loc0 = locs0[i]
		loc1 = locs1[i]

		value = cmds.getAttr("{}.worldPosition".format(loc0))[0]
		cmds.setAttr("{}.controlPoints[{}]".format(surf, cv_idx), *value)
		cv_idx += 1

		value = cmds.getAttr("{}.worldPosition".format(loc1))[0]
		cmds.setAttr("{}.controlPoints[{}]".format(surf, cv_idx), *value)
		cv_idx += 1

	if parent:
		cmds.parent(surf, parent)

	cmds.delete(locs0, locs1)
	return surf


def rebuild_surface(surface):
	"""
	Rebuild 0-1 surface

	:param surface:
	:return:
	"""
	surface = mel.eval("rebuildSurface -ch 0 -rpo 1 -rt 0 -end 1 -kr 0 -kcp 1 "
	                   "-kc 1 -su 4 -du 0 -sv 4 -dv 0 -tol 0.01 -fr 0  -dir 2 ".format(surface))
	cmds.delete(surface, ch=1)
	return surface[0]


def assign_ribbon_shader(surfaces):
	"""

	:param surfaces:
	:return:
	"""
	shader = "rbRibbon_SHD"
	shading_group = "rbRibbon_SG"

	if not cmds.objExists(shader):
		shader = cmds.createNode("blinn", n=shader)
		cmds.setAttr(shader + ".transparency", 0.8, 0.8, 0.8)
		cmds.setAttr(shader + ".color", 0.25, 0.25, 0.65)
		cmds.setAttr(shader + ".specularRollOff", 0.2)

	if not cmds.objExists(shading_group):
		shading_group = cmds.sets(renderable=1, noSurfaceShader=1, empty=1, name=shading_group)
		cmds.connectAttr(shader + ".outColor", shading_group + ".surfaceShader")

	cmds.sets(surfaces, forceElement=shading_group)
	cmds.toggle(editPoint=1, origin=1)
