import re

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import maya.mel as mel

from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib import utilslib


def create_surface_rivet(surface, nodes, maintain_offset=True, translate=True, rotate=True, driver=None):
	"""

	:param surface:
	:param nodes:
	:param maintain_offset:
	:param translate:
	:param rotate:
	:param driver:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	results = []

	for node in nodes:
		cpos = cmds.createNode("closestPointOnSurface")
		ps_info = cmds.createNode("pointOnSurfaceInfo")
		results.append(ps_info)

		cmds.connectAttr(surface + ".worldSpace", ps_info + ".inputSurface")
		cmds.connectAttr(surface + ".worldSpace", cpos + ".inputSurface")

		# support for control driver
		if driver:
			ddmx = cmds.createNode("decomposeMatrix")
			cmds.connectAttr(driver + ".worldMatrix", ddmx + ".inputMatrix")
			cmds.connectAttr(ddmx + ".outputTranslate", cpos + ".inPosition")
			cmds.connectAttr(cpos + ".parameterU", ps_info + ".parameterU")
			cmds.connectAttr(cpos + ".parameterV", ps_info + ".parameterV")

		else:
			# get u and v param
			cmds.setAttr(cpos + ".inPositionX", cmds.xform(node, q=1, ws=1, t=1)[0])
			cmds.setAttr(cpos + ".inPositionY", cmds.xform(node, q=1, ws=1, t=1)[1])
			cmds.setAttr(cpos + ".inPositionZ", cmds.xform(node, q=1, ws=1, t=1)[2])
			cmds.setAttr(ps_info + ".parameterU", cmds.getAttr(cpos + ".parameterU"))
			cmds.setAttr(ps_info + ".parameterV", cmds.getAttr(cpos + ".parameterV"))

		# recreate the new world matrix for node
		mtx = cmds.createNode("fourByFourMatrix")
		cmds.connectAttr(ps_info + ".normalX", mtx + ".i00")
		cmds.connectAttr(ps_info + ".normalY", mtx + ".i01")
		cmds.connectAttr(ps_info + ".normalZ", mtx + ".i02")
		cmds.connectAttr(ps_info + ".tangentUx", mtx + ".i10")
		cmds.connectAttr(ps_info + ".tangentUy", mtx + ".i11")
		cmds.connectAttr(ps_info + ".tangentUz", mtx + ".i12")
		cmds.connectAttr(ps_info + ".tangentVx", mtx + ".i20")
		cmds.connectAttr(ps_info + ".tangentVy", mtx + ".i21")
		cmds.connectAttr(ps_info + ".tangentVz", mtx + ".i22")
		cmds.connectAttr(ps_info + ".positionX", mtx + ".i30")
		cmds.connectAttr(ps_info + ".positionY", mtx + ".i31")
		cmds.connectAttr(ps_info + ".positionZ", mtx + ".i32")

		# get offset
		constraintslib.matrix_constraint(mtx,
		                                 node,
		                                 maintain_offset=maintain_offset,
		                                 translate=translate,
		                                 rotate=rotate,
		                                 scale=False,
		                                 matrix_plug="output")

		if not driver:
			cmds.delete(cpos)

	return results


def create_curve_rivet(curve, nodes, maintain_offset=True, translate=True, driver=None):
	"""

	:param curve:
	:param nodes:
	:param maintain_offset:
	:param translate:
	:param driver:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	results = []

	for node in nodes:
		pc_info = cmds.createNode("pointOnCurveInfo")
		npoc = cmds.createNode("nearestPointOnCurve")
		results.append(pc_info)

		cmds.connectAttr(curve + ".worldSpace", pc_info + ".inputCurve")
		cmds.connectAttr(curve + ".worldSpace", npoc + ".inputCurve")

		if driver:
			ddmx = cmds.createNode("decomposeMatrix")
			cmds.connectAttr(driver + ".worldMatrix", ddmx + ".inputMatrix")
			cmds.connectAttr(ddmx + ".outputTranslate", npoc + ".inPosition")
			cmds.connectAttr(npoc + ".parameter", pc_info + ".parameter")

		else:
			cmds.setAttr(npoc + ".inPositionX", cmds.xform(node, q=1, ws=1, t=1)[0])
			cmds.setAttr(npoc + ".inPositionY", cmds.xform(node, q=1, ws=1, t=1)[1])
			cmds.setAttr(npoc + ".inPositionZ", cmds.xform(node, q=1, ws=1, t=1)[2])
			cmds.setAttr(pc_info + ".parameter", cmds.getAttr(npoc + ".parameter"))

		# recreate the new world matrix for node
		mtx = cmds.createNode("fourByFourMatrix")
		cmds.connectAttr(pc_info + ".positionX", mtx + ".i30")
		cmds.connectAttr(pc_info + ".positionY", mtx + ".i31")
		cmds.connectAttr(pc_info + ".positionZ", mtx + ".i32")

		# get offset
		if translate:
			constraintslib.matrix_constraint(mtx,
			                                 node,
			                                 maintain_offset=maintain_offset,
			                                 translate=translate,
			                                 rotate=False,
			                                 scale=False,
			                                 matrix_plug="output")
		if not driver:
			cmds.delete(npoc)

	return results


def create_motion_path(curve, nodes, translate=True, rotate=True):
	"""

	:param curve:
	:param nodes:
	:param translate:
	:param rotate:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)
	results = []

	for node in nodes:
		mp = cmds.createNode("motionPath")
		npoc = cmds.createNode("nearestPointOnCurve")
		results.append(mp)

		cmds.connectAttr(curve + ".worldSpace", mp + ".geometryPath")
		cmds.connectAttr(curve + ".worldSpace", npoc + ".inputCurve")

		cmds.setAttr(npoc + ".inPositionX", cmds.xform(node, q=1, ws=1, t=1)[0])
		cmds.setAttr(npoc + ".inPositionY", cmds.xform(node, q=1, ws=1, t=1)[1])
		cmds.setAttr(npoc + ".inPositionZ", cmds.xform(node, q=1, ws=1, t=1)[2])

		param = cmds.getAttr(npoc + ".parameter")
		cmds.setAttr(mp + ".uValue", 0.0 if param == 1.0 else param)
		cmds.delete(npoc)

		if translate:
			cmds.connectAttr(mp + ".allCoordinates", node + ".t", f=True)
		if rotate:
			cmds.connectAttr(mp + ".rotate", node + ".r", f=True)

	return results


def create_mesh_rivet(mesh, node, noxform_grp='noxform_GRP', edges=[], use_trianlge_edges=False, constrain=True,
                      create_offset=True):
	"""

	:param mesh:
	:param node:
	:param noxform_grp:
	:param edges:
	:param use_trianlge_edges:
	:param constrain:
	:param create_offset:
	:return:
		"""
	node = cmds.ls(node)[0]

	shape = selectionlib.get_shapes(mesh)[0]
	edges = cmds.ls(edges)

	if cmds.nodeType(shape) != 'mesh':
		raise ValueError(shape + ' is not a mesh!')

	if not len(edges) == 2:

		# get triangle verts
		loc = transformslib.xform.match_locator(node)

		pos = cmds.xform(loc, q=1, ws=1, t=1)
		cmds.delete(loc)

		m_intersect = OpenMaya.MMeshIntersector()
		m_list = OpenMaya.MSelectionList()
		m_list.add(shape)

		shape_dag = m_list.getDependNode(0)
		node_point = OpenMaya.MPoint(pos[0], pos[1], pos[2])
		m_intersect.create(shape_dag)

		point_info = m_intersect.getClosestPoint(node_point)
		face_id = point_info.face
		triangle_id = point_info.triangle

		fnMesh = OpenMaya.MFnMesh(shape_dag)
		verts = fnMesh.getPolygonTriangleVertices(face_id, triangle_id)
		verts = ['{0}.vtx[{1}]'.format(mesh, v) for v in verts]

		# get two edges (this is our backup if the mesh is triangulated)
		face = '{0}.f[{1}]'.format(mesh, face_id)
		face_edges = cmds.polyInfo(face, faceToEdge=1)[0].split(':')[1].replace('\n', '')
		face_edges = ['{0}.e[{1}]'.format(mesh, i) for i in re.sub(' +', ' ', face_edges).strip().split(' ')]

		triangle_edges = []
		for edge in face_edges:
			edge_verts = cmds.polyInfo(edge, ev=1)[0].split(':')[1].replace('\n', '')
			edge_verts = ['{0}.vtx[{1}]'.format(mesh, i) for i in re.sub(' +', ' ', edge_verts).strip().split(' ')]

			pass_check = True
			for v in edge_verts:
				if cmds.objExists(v) and not v in verts:
					pass_check = False

			if pass_check:
				triangle_edges.append(edge)

		# get the edge ring
		cmds.select(triangle_edges[0])
		mel.eval('SelectEdgeRingSp')
		edge_ring = cmds.ls(sl=1, fl=1)

		edges = []

		for e in edge_ring:
			if e in face_edges:
				edges.append(e)

		if not len(edges) == 2 and len(triangle_edges) == 2:
			edges = triangle_edges

		# override and use triangle edges
		if use_trianlge_edges and len(triangle_edges) == 2:
			edges = triangle_edges

	if not len(edges) == 2:
		raise ValueError('2 edges were not found or not specified! ')

	# Create curve from edges then loft
	cme1 = cmds.createNode('curveFromMeshEdge')
	cme2 = cmds.createNode('curveFromMeshEdge')
	loft = cmds.createNode('loft')

	edge_id1 = int(edges[0].split('[')[1].split(']')[0])
	edge_id2 = int(edges[1].split('[')[1].split(']')[0])
	cmds.setAttr(cme1 + '.ei[0]', edge_id1)
	cmds.setAttr(cme2 + '.ei[0]', edge_id2)
	cmds.setAttr(loft + '.uniform', 1)

	cmds.connectAttr(shape + '.worldMesh', cme1 + '.inputMesh')
	cmds.connectAttr(shape + '.worldMesh', cme2 + '.inputMesh')

	cmds.connectAttr(cme1 + '.outputCurve', loft + '.inputCurve[0]')
	cmds.connectAttr(cme2 + '.outputCurve', loft + '.inputCurve[1]')

	# get u and v parameters
	cpos = cmds.createNode('closestPointOnSurface')
	cmds.connectAttr(loft + '.outputSurface', cpos + '.inputSurface')
	cmds.setAttr(cpos + '.inPositionX', cmds.xform(node, q=1, ws=1, t=1)[0])
	cmds.setAttr(cpos + '.inPositionY', cmds.xform(node, q=1, ws=1, t=1)[1])
	cmds.setAttr(cpos + '.inPositionZ', cmds.xform(node, q=1, ws=1, t=1)[2])

	param_u = max(cmds.getAttr(cpos + '.parameterU'), 0.001)
	param_v = max(cmds.getAttr(cpos + '.parameterV'), 0.001)

	# Create point on surface info
	psinfo = cmds.createNode('pointOnSurfaceInfo')
	cmds.connectAttr(loft + '.outputSurface', psinfo + '.inputSurface')
	cmds.setAttr(psinfo + '.parameterU', param_u)
	cmds.setAttr(psinfo + '.parameterV', param_v)
	cmds.delete(cpos)

	# recreate the new world matrix for node
	mtx = cmds.createNode('fourByFourMatrix')
	cmds.connectAttr(psinfo + '.normalX', mtx + '.i00')
	cmds.connectAttr(psinfo + '.normalY', mtx + '.i01')
	cmds.connectAttr(psinfo + '.normalZ', mtx + '.i02')
	cmds.connectAttr(psinfo + '.tangentUx', mtx + '.i10')
	cmds.connectAttr(psinfo + '.tangentUy', mtx + '.i11')
	cmds.connectAttr(psinfo + '.tangentUz', mtx + '.i12')
	cmds.connectAttr(psinfo + '.tangentVx', mtx + '.i20')
	cmds.connectAttr(psinfo + '.tangentVy', mtx + '.i21')
	cmds.connectAttr(psinfo + '.tangentVz', mtx + '.i22')
	cmds.connectAttr(psinfo + '.positionX', mtx + '.i30')
	cmds.connectAttr(psinfo + '.positionY', mtx + '.i31')
	cmds.connectAttr(psinfo + '.positionZ', mtx + '.i32')

	# get offset
	mult_mtx = cmds.createNode('multMatrix')
	dmx = cmds.createNode('decomposeMatrix')
	world_drv = cmds.createNode('transform', n=node + '_rivet_GRP', p=noxform_grp)

	cmds.connectAttr(mtx + '.o', mult_mtx + '.matrixIn[0]')
	cmds.connectAttr(world_drv + '.parentInverseMatrix', mult_mtx + '.matrixIn[1]')
	cmds.connectAttr(mult_mtx + '.matrixSum', dmx + '.inputMatrix')
	cmds.connectAttr(dmx + '.outputTranslate', world_drv + '.t')
	cmds.connectAttr(dmx + '.outputRotate', world_drv + '.r')

	# parent constrain node
	if constrain:
		con_node = world_drv
		if create_offset:
			con_node = cmds.duplicate(node, n=node + '_rivet_OFF', po=1)[0]
			attributeslib.set_attributes(con_node, ["t", "r", "s"], keyable=True, lock=False)
			cmds.parent(con_node, world_drv)

		prc = cmds.parentConstraint(con_node, node, mo=1)[0]
		return prc

	return world_drv
