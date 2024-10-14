import maya.OpenMaya as OpenMaya


def get_dep(node):
	"""
	:param str node:
	:return: Maya dependency node
	:rtype: OpenMaya.MObject
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)

	obj = OpenMaya.MObject()
	sel.getDependNode(0, obj)

	return obj


def get_dag(node):
	"""
	:param str node:
	:return: Maya dag path
	:rtype: OpenMaya.MDagPath
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)

	dag = OpenMaya.MDagPath()
	sel.getDagPath(0, dag)

	return dag


def get_plug(node):
	"""
	:param str node:
	:return: Maya plug node
	:rtype: OpenMaya.MPlug
	"""
	plug = OpenMaya.MPlug()
	sel = OpenMaya.MSelectionList()
	sel.add(node)
	sel.getPlug(0, plug)

	return plug
