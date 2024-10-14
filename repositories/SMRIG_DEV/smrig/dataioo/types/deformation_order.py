import maya.cmds as cmds

deformer_type = "deformationOrder"
file_type = "json"


def get_data(node, **kwarg):
	"""
	Get deformation order from nodes

	:param node:
	:return:
	"""
	data = {"name": node,
	        "nodes": [node],
	        "order": cmds.listHistory(node, il=1, pdo=1) or [],
	        "deformer_type": deformer_type}

	return data


def set_data(data):
	"""
	Set deformation order

	:param data:
	:return:
	"""
	shape = data.get("nodes")
	order = data.get("order")

	for i in range(len(order) - 1):
		try:
			cmds.reorderDeformers(order[i], order[i + 1], shape)
		except:
			pass
