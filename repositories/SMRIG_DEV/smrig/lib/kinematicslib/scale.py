import maya.cmds as cmds

from smrig.lib import utilslib

SCALE_ATTRIBUTES = ["sy", "sz"]
CONTROL_ATTRIBUTE = "segmentScale"


def create_ramp_scale(controls, joints, interpolation=4, control_attribute=None, scale_attributes=None):
	"""
	Create a distributed scale driven by SDKs and generated ramp nodees.

	:param controls:
	:param joints:
	:param interpolation:
	:param control_attribute:
	:param scale_attributes:
	:return:
	"""
	scale_attributes = scale_attributes if scale_attributes else SCALE_ATTRIBUTES
	control_attribute = control_attribute if control_attribute else CONTROL_ATTRIBUTE

	# create ramps
	number_ctrls = len(controls)
	number_joints = len(joints)

	ctrl_div = 1.0 / (number_ctrls - 1)
	jnt_div = 1.0 / (number_joints - 1)

	sdk_crvs = []
	ramps = []

	for i in range(number_ctrls):
		pre = (i - 1) * ctrl_div
		post = (i + 1) * ctrl_div
		current = i * ctrl_div

		ramp = cmds.createNode("ramp", n=controls[i] + "_ramp")
		cmds.setAttr(ramp + ".colorEntryList[0].color", 0, 0, 0, type="double3")
		cmds.setAttr(ramp + ".colorEntryList[1].color", 1, 1, 1, type="double3")
		cmds.setAttr(ramp + ".colorEntryList[2].color", 0, 0, 0, type="double3")
		cmds.setAttr(ramp + ".colorEntryList[0].position", max(min(1, pre), 0))
		cmds.setAttr(ramp + ".colorEntryList[1].position", current)
		cmds.setAttr(ramp + ".colorEntryList[2].position", max(min(1, post), 0))
		cmds.setAttr(ramp + ".interpolation", interpolation)
		ramps.append(ramp)

	cmds.removeMultiInstance(ramps[-1] + ".colorEntryList[2]", b=True)
	cmds.removeMultiInstance(ramps[0] + ".colorEntryList[0]", b=True)

	# SDK scales based on ramps
	for i in range(number_ctrls):
		driver_ctrl = "{}.{}".format(controls[i], control_attribute)
		cmds.addAttr(controls[i], ln=control_attribute, k=1, dv=1)

		for dattr in scale_attributes:
			for ji in range(number_joints):
				driven_attr = "{}.{}".format(joints[ji], dattr)
				cmds.setAttr(joints[ji] + ".segmentScaleCompensate", 1)
				cmds.setAttr(ramps[i] + ".vCoord", jnt_div * ji)

				value = cmds.getAttr(ramps[i] + ".outColorR")
				cmds.setDrivenKeyframe(driven_attr, cd=driver_ctrl, dv=0, v=0, ott="spline", itt="spline")
				cmds.setDrivenKeyframe(driven_attr, cd=driver_ctrl, dv=1, v=value, ott="spline", itt="spline")

			sdk_crvs.extend(cmds.listConnections(driver_ctrl, type="animCurve", scn=1))

	if sdk_crvs:
		cmds.selectKey(sdk_crvs)
		cmds.setInfinity(poi="linear", pri="linear")

	# set infinity
	cmds.delete(ramps)


def create_volume_preservation(drivers, joints, control, scale_attributes=None):
	"""
	Set up scale base volume preservation for a given set of joints in a chain.

	:param drivers:
	:param joints:
	:param control:
	:param scale_attributes:
	:return:
	"""
	scale_attributes = scale_attributes if scale_attributes else SCALE_ATTRIBUTES

	if not cmds.objExists(control + ".preserveVolume"):
		cmds.addAttr(control, ln="preserveVolume", k=1, min=0, max=1, dv=0.5)

	if not cmds.objExists(control + ".preserveVolumeMin"):
		cmds.addAttr(control, ln="preserveVolumeMin", k=1, min=0.01, max=1, dv=0.2)

	if not cmds.objExists(control + ".preserveVolumeMax"):
		cmds.addAttr(control, ln="preserveVolumeMax", k=1, min=1, max=10, dv=4)

	for i, node in enumerate(joints[:-1]):
		dst = utilslib.distance.create_reader(drivers[i], drivers[i + 1], stretch=True)
		bta = cmds.createNode("blendTwoAttr", name=("blendTwoAttr_preserveVolume_" + node))

		cmds.connectAttr(control + ".preserveVolume", bta + ".attributesBlender")
		cmds.connectAttr(dst + ".inverseStretchFactor", bta + ".input[1]")
		cmds.setAttr(bta + ".input[0]", 1)

		clamp = cmds.createNode("clamp", name=("clamp_preserveVolume_" + node))
		cmds.connectAttr(bta + ".output", clamp + ".inputR")
		cmds.connectAttr(control + ".preserveVolumeMin", clamp + ".minR")
		cmds.connectAttr(control + ".preserveVolumeMax", clamp + ".maxR")

		for attr in scale_attributes:
			cnn = cmds.listConnections(node + "." + attr, s=1, d=0, p=1)
			if cnn:
				mdl = cmds.createNode("multDoubleLinear", name=(node + "_preserveVolume_multDoubleLinear"))
				cmds.connectAttr(cnn[0], mdl + ".i1")
				cmds.connectAttr(clamp + ".outputR", mdl + ".i2")
				cmds.connectAttr(mdl + ".o", node + "." + attr, f=1)

			else:
				cmds.connectAttr(clamp + ".outputR", node + "." + attr)

	try:
		cmds.connectAttr(joints[-2] + ".s", joints[-1] + ".s")
	except:
		pass
