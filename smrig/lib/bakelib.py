import maya.cmds as cmds

from smrig.lib import utilslib, animationlib, decoratorslib


@decoratorslib.null_viewport
def bake_animation(nodes,
                   sample_by=1,
                   unroll_gimbal=True,
                   unroll_exluded=[],
                   minimize_rotation=False,
                   tanget_type="linear",
                   start_frame=None,
                   end_frame=None,
                   remove_static_channels=True,
                   remove_static_flat_keys=True,
                   remove_static_linear_keys=False,
                   precision=3):
	"""
	Bake transforms down to keyframes, unroll gimbal and minimize rotation.

	:param nodes:
	:param sample_by:
	:param unroll_gimbal:
	:param unroll_exluded:
	:param minimize_rotation:
	:param tanget_type:
	:param start_frame:
	:param end_frame:
	:param remove_static_channels:
	:param remove_static_flat_keys:
	:param remove_static_linear_keys:
	:param precision:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)

	# set_nodes = mc.sets(engine_joints, query=True)
	start_frame = start_frame if start_frame else cmds.playbackOptions(query=True, minTime=True)
	end_frame = end_frame if end_frame else cmds.playbackOptions(query=True, maxTime=True)

	# Bake it all
	cmds.bakeResults(nodes,
	                 simulation=True,
	                 t=(int(start_frame), int(end_frame)),
	                 sampleBy=sample_by,
	                 disableImplicitControl=True,
	                 preserveOutsideKeys=False,
	                 sparseAnimCurveBake=False,
	                 removeBakedAttributeFromLayer=False,
	                 removeBakedAnimFromLayer=False,
	                 bakeOnOverrideLayer=False,
	                 minimizeRotation=minimize_rotation,
	                 controlPoints=False)

	crvs = animationlib.get_anim_curves(nodes)
	animationlib.set_tangent_type(crvs, tanget_type)

	if unroll_gimbal:
		unroll_nodes = [n for n in nodes if n not in unroll_exluded]
		unroll_gimbal_rotations(unroll_nodes)

	if remove_static_channels:
		delete_static_channels(nodes)

	if remove_static_linear_keys or remove_static_flat_keys:
		curves = animationlib.get_anim_curves(nodes)
		delete_redundant_keys(curves, remove_static_flat_keys, remove_static_linear_keys, precision)


def delete_redundant_keys(curves, flat_keys=True, linear_keys=True, precision=3):
	"""
	Remove flat or linear redundant keys

	:param curves:
	:param flat_keys:
	:param linear_keys:
	:param precision:
	:return:
	"""
	curves = utilslib.conversion.as_list(curves)

	for crv in curves:
		values = cmds.keyframe(crv, valueChange=1, query=1)
		frames = cmds.keyframe(crv, timeChange=1, query=1)
		redundant = []

		for i in range(1, len(values[1:])):
			v = values[i]
			t = frames[i]
			pv = values[i - 1]
			nv = values[i + 1]

			if flat_keys and nv == v and v == pv:
				redundant.append(t)

			if linear_keys:
				cmds.cutKey(crv, t=(t, t))
				cmds.setKeyframe(crv, t=t, itt="linear", ott="linear")

				lv = cmds.keyframe(crv, t=(t, t), valueChange=1, query=1)[0]

				cmds.cutKey(crv, t=(t, t))
				cmds.setKeyframe(crv, t=t, v=v, itt="linear", ott="linear")

				if round(v, precision) == round(lv, precision):
					redundant.append(t)

		for t in redundant:
			cmds.cutKey(crv, t=(t, t))


def delete_static_channels(nodes):
	"""
	Remove static anim curves from channels

	:param nodes:
	:return:
	"""
	cmds.delete(nodes, staticChannels=True, unitlessAnimationCurves=False, controlPoints=0, shape=0)


def unroll_gimbal_rotations(nodes):
	"""
	Takes transforms and fixes gimbal issues one frame at a time using some conditional math.

	:param nodes:
	:return:
	"""
	nodes = utilslib.conversion.as_list(nodes)

	for transform in nodes:
		t0 = float(cmds.playbackOptions(q=1, ast=1))
		t1 = float(cmds.playbackOptions(q=1, aet=1))
		k = 0

		# get keys - should be same for all channels since we baked them in that range
		nKeys = int(cmds.keyframe(transform + ".rotateX", query=1, keyframeCount=1))
		rotX = cmds.keyframe(transform + ".rotateX", valueChange=1, query=1)
		rotY = cmds.keyframe(transform + ".rotateY", valueChange=1, query=1)
		rotZ = cmds.keyframe(transform + ".rotateZ", valueChange=1, query=1)

		for k in range(1, nKeys):
			x_diff = 0.0
			y_diff = 0.0
			z_diff = 0.0
			x_diff = rotX[k] - rotX[k - 1]

			if x_diff < -90:
				rotX[k] += float(float((((int((x_diff + 90)) / -360) + 1) * 360)))
			x_diff = rotX[k] - rotX[k - 1]

			if x_diff > 270:
				rotX[k] -= float(float((((int((x_diff - 270)) / 360) + 1) * 360)))
			z_diff = rotZ[k] - rotZ[k - 1]

			if z_diff < -90:
				rotZ[k] += float(float((((int((z_diff + 90)) / -360) + 1) * 360)))
			z_diff = rotZ[k] - rotZ[k - 1]

			if z_diff > 270:
				rotZ[k] -= float(float((((int((z_diff - 270)) / 360) + 1) * 360)))
			x_diff = rotX[k] - rotX[k - 1]

			if (x_diff > 90) and (x_diff < 270):
				rotX[k] = rotX[k] - 180
				rotY[k] = float(180 - rotY[k])
				rotZ[k] = rotZ[k] - 180
			y_diff = rotY[k] - rotY[k - 1]

			if y_diff > 180:
				rotY[k] -= float(float((((int((y_diff - 180)) / 360) + 1) * 360)))
			y_diff = rotY[k] - rotY[k - 1]

			if y_diff < -180:
				rotY[k] += float(float((((int((y_diff + 180)) / -360) + 1) * 360)))

		# set keyframes
		for k in range(0, nKeys):
			cmds.keyframe((transform + ".rotateX"), edit=1, index=(k, k), valueChange=rotX[k])
			cmds.keyframe((transform + ".rotateY"), edit=1, index=(k, k), valueChange=rotY[k])
			cmds.keyframe((transform + ".rotateZ"), edit=1, index=(k, k), valueChange=rotZ[k])


def remove_flip(joints):
	"""
	Takes transforms and fixes gimbal issues one frame at a time using some conditional math.
	Depricated..

	:param joints:
	:return:
	"""
	start_frame = cmds.playbackOptions(q=1, min=1)
	end_frame = cmds.playbackOptions(q=1, max=1) + 1

	for i in range(int(start_frame), int(end_frame)):
		cmds.currentTime(i)

		for joint in joints:
			# repo worldSpace
			rot = cmds.xform(joint, q=1, ws=1, ro=1)
			cmds.xform(joint, ws=1, ro=rot)

			# repo precsisioio
			abs_rot = cmds.xform(joint, q=1, a=1, ro=1)
			abs_rot = [round(v, 3) for v in abs_rot]
			cmds.xform(joint, a=1, ro=abs_rot)

			# unroll -180
			cmds.setKeyframe(joint + '.rx')
			cmds.setKeyframe(joint + '.ry')
			cmds.setKeyframe(joint + '.rz')
