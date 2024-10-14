import maya.cmds as cmds
import maya.mel as mel


def create(driver,
           nodes,
           base=None,
           threshold=0,
           max_dist=1,
           infl_type=2,
           exclusive=1,
           auto_weight_threshold=1,
           render_infl=0,
           falloff_mode=0):
	"""
	Create wrap

	:param driver:
	:param nodes:
	:param base:
	:param threshold:
	:param max_dist:
	:param infl_type:
	:param exclusive:
	:param auto_weight_threshold:
	:param render_infl:
	:param falloff_mode:
	:return:
	"""
	if nodes is None:
		nodes = cmds.ls(sl=1)
		driver = nodes[len(nodes) - 1]
		nodes.remove(driver)

	nodes = cmds.ls(nodes)

	allwraps = []
	for n in nodes:
		name = n + '_wrp'
		cmds.select(n, driver)
		wraps = mel.eval('doWrapArgList "7" { "1", "' + str(threshold) + '","' + str(max_dist) + '", "' + str(
			infl_type) + '", "' + str(exclusive) + '", "' + str(auto_weight_threshold) + '", "' + str(
			render_infl) + '", "' + str(falloff_mode) + '" }')

		cmds.setAttr(wraps[0] + ".maxDistance", 100000)
		allwraps.append(cmds.rename(wraps[0], name))

	if base is None:
		bases = cmds.ls(driver + 'Base')
		if bases:
			base = bases[0]
		else:
			base = cmds.listConnections(allwraps[0] + '.basePoints')[0]

	for i in range(0, len(allwraps)):
		bjunk = cmds.listConnections(allwraps[i] + '.basePoints', p=0)[0]
		if not bjunk == base:
			cmds.connectAttr(base + '.worldMesh', allwraps[i] + '.basePoints[0]', f=1)
			cmds.delete(bjunk)

	if len(allwraps) == 1:
		return (allwraps[0], base)

	else:
		return (allwraps, base)
