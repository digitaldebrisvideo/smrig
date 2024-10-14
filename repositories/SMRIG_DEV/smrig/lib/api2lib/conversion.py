import maya.api.OpenMaya as OpenMaya


def get_dep(node):
	"""
	:param str node:
	:return: Maya dependency node
	:rtype: OpenMaya.MObject
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)


def get_dag(node):
	"""
	:param str node:
	:return: Maya dag path
	:rtype: OpenMaya.MDagPath
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)
	return sel.getDagPath(0)


def get_plug(node):
	"""
	:param str node:
	:return: Maya plug node
	:rtype: OpenMaya.MPlug
	"""
	sel = OpenMaya.MSelectionList()
	sel.add(node)
	return sel.getPlug(0)
