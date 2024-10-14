import logging
import os

import maya.cmds as cmds
import maya.mel as mel
from smrig import dataio, env
from smrig.lib import attributeslib, nodepathlib, pathlib, selectionlib, utilslib
from smrig.lib.constantlib import ENGINE_SET, RIG_GROUP, RIG_SET

log = logging.getLogger("smrig.build.modellib")

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"


def get_elements_on_disk(asset=None, custom_path=None, type=None, extension="mb"):
	"""

	:param asset:
	:return:
	"""

	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	files = []
	if custom_path is not None:
		if not os.path.isdir(custom_path):
			log.warning("cannot find custom path")
			return []
		all_files = os.listdir(custom_path)
		file_list = [x for x in all_files if all_files]
		for file in file_list:
			name = file.replace(".mb", "")
			files.append(name)
	else:

		base_dir = pathlib.normpath(os.path.join(env.asset.get_rigbuild_path().replace("rigbuild", "scenes")))
		directory = pathlib.normpath(os.path.join(base_dir, type))
		if os.path.isdir(directory):
			all_files = os.listdir(directory)
			file_list = [x for x in all_files if all_files]
			for file in file_list:
				name = file.replace(".mb", "")
				files.append(name)

	return files


def get_element_path(asset=None):
	"""

	:param asset:
	:param type:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	base_dir = pathlib.normpath(os.path.join(env.asset.get_rigbuild_path().replace("rigbuild", "scenes")))
	return base_dir


def save_element(asset=None, description="xxx", version=None, all=True, element="clothing"):
	"""
	Save library item maya file.

	:param asset:
	:param description:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	nodes = []
	if not all:
		nodes = cmds.ls(sl=1)
		if not nodes:
			log.error("Nothing selected. Export All instead")
			return
	else:
		assemblies = cmds.ls(assemblies=True)
		if assemblies:
			for assembly in assemblies:
				node_type = cmds.nodeType(assembly)
				if node_type == "camera":
					continue
				nodes.append(assembly)

	# else:
	#     meshes=cmds.ls(type="mesh")
	#     cmds.select (meshes)
	#     if not meshes:
	#         log.error("No meshes found in scene")
	#         return
	#     for mesh in meshes:
	#         node=selectionlib.get_transform(mesh)
	#         nodes.append(node)
	#         if not nodes:
	#             log.error("no meshes found or something went wrong in scene")
	# for node in nodes:
	#     if selectionlib.get_parent(node):
	#         cmds.parent(node, world=True)
	# lib_grp=description+"_lib_GRP"
	# if not cmds.objExists(lib_grp):
	#     lib_grp=cmds.createNode("transform", name=lib_grp)
	# cmds.parent (nodes, lib_grp)

	# attributeslib.tag.add_tag_attribute(lib_grp, attribute_name="libItem", value=element)
	# for node in nodes:
	#     attributeslib.tag.add_tag_attribute(node, attribute_name="libItem", value=element)

	file_name = "{}.{}".format(description, maya_file_extention)

	base_dir = pathlib.normpath(os.path.join(os.path.dirname(env.asset.get_rigbuild_path()), "scenes"))
	directory = pathlib.normpath(os.path.join(base_dir, "Library", element))
	pathlib.make_dirs(directory)

	file_path = pathlib.normpath(os.path.join(directory, file_name))

	# if os.path.isfile(file_path):
	# result = cmds.confirmDialog(title="Save Element", message="{0} already exists.\nDo you want to replace it and all other existing files? ".format(element),
	# button=["Overwrite", "Backup && Export", "Skip"], icon="warning",
	# defaultButton= "Backup && Export", cancelButton="Skip", dismissString="Skip")
	# if result=="Skip":
	#     return ()
	# if result=="Backup && Export":
	#     backup_path=pathlib.normpath(os.path.join(directory, ".backup"))
	#     if not os.path.isdir(backup_path):
	#         pathlib.make_dirs(backup_path)
	#     backup_file=pathlib.normpath(os.path.join(backup_path, file_name))
	#     cmds.sysFile(file_path, rename=backup_file)

	cmds.select(nodes)
	cmds.file(file_path, options="v=0;", type=maya_file_type, ea=True, force=True)
	# log.info("Saved all to library element: {}".format(pathlib.normpath(file_path)))

	log.info("Exported library item to: {}".format(pathlib.normpath(file_path)))


def load_scene(asset=None,
               variant=None,
               description="primary",
               version=None,
               unlock_normals=False,
               soft_normals=False,
               action="reference",
               namespace=":",
               new_file=False,
               file_path="",
               tag_name=None,
               apply_data=False):
	"""
	Load model file.

	:param asset:
	:param description:
	:param version:
	:param unlock_normals:
	:param soft_normals:
	:param action:
	:param namespace:
	:param new_file:
	:param file_path:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	if not file_path:
		file_name = "Library_{}".format(description)
		directory = pathlib.normpath(os.path.join(os.path.dirname(env.assets.get_rigbuild_path(asset)), "scenes"))
		version_object = pathlib.Version(directory, file_name, maya_file_extention)
		file_path = version_object.get_load_version_path(version)

	if action == "reference":
		new_nodes = cmds.file(file_path, reference=True, namespace=":", rnn=True)
		ref_node = cmds.referenceQuery(new_nodes[0], rfn=True)
		nodes = cmds.referenceQuery(ref_node, nodes=True)
		nn = []

		data_nodes = []

		# result = cmds.ls([selectionlib.get_transform(m) for m in selectionlib.sort_by_hierarchy(nodes)])
		if apply_data:
			grps = [x for x in new_nodes if "lib_GRP" in x]

			for grp in grps:
				children = selectionlib.get_children(grp)
				if children:
					for child in children:
						data_nodes.append(child)

		load_rig_data(data_nodes, variant)


	# if action == "import":
	#     new_nodes = cmds.file(file_path, i=True, namespace=":", rnn=True)
	#
	#     data_nodes = []
	#
	#     if apply_data:
	#         grps = [x for x in new_nodes if "lib_GRP" in x]
	#         print grps
	#
	#         for grp in grps:
	#             children = selectionlib.get_children(grp)
	#             if children:
	#                 for child in children:
	#                     data_nodes.append(child)
	#
	#     load_rig_data(data_nodes, variant)

	else:
		result = utilslib.scene.load(file_path, action=action, rnn=True, namespace=namespace, new_file=new_file)
		print(result)

		if result:
			result = cmds.ls([selectionlib.get_transform(m) for m in selectionlib.sort_by_hierarchy(result)])

			if unlock_normals or soft_normals or apply_data:
				meshes = [n for n in result if cmds.nodeType(n) == "mesh"]

				if unlock_normals:
					cmds.select(meshes)
					mel.eval("UnlockNormals;")

				if soft_normals:
					cmds.select(meshes)
					mel.eval("SoftPolyEdgeElements 1;")


def load_rig_data(nodes=None, variant="primary"):
	"""

	:return:
	"""
	print("applying data")
	print(nodes)
	asset = env.asset.get_asset()
	if not asset:
		return ['asset not set']

	data_base = pathlib.normpath(os.path.join(get_element_path(asset=asset), "Library", "data"))
	data_path = pathlib.normpath(os.path.join(data_base, variant))

	if os.path.isdir(data_path):
		if nodes:
			for node in nodes:
				data_file = pathlib.normpath(os.path.join(data_path, node + "_SKN.skn"))
				if os.path.isfile(data_file):
					print(node)
					dataio.load(data_file)


def load_from_build_options(action="reference", namespace=":"):
	"""
	Load model from build options.

	:param action:
	:param set_shapes:
	:param set_colors:
	:param stash:
	:param namespace:
	:return:
	"""
	library_data = env.asset.get_libraries()
	if not library_data:
		log.warning("No library dataio found.")
		return

	for data in library_data:
		result = load_scene(namespace=namespace,
		                    action=action,
		                    asset=data.get("asset"),
		                    description=data.get("description"),
		                    version=data.get("version"),
		                    file_path=data.get("file_path"))

		if result and cmds.objExists(RIG_GROUP) and cmds.objExists(MODEL_LIB_GRP) and cmds.objExists(RIG_SET):
			if cmds.objExists("|{}|{}".format(RIG_GROUP, MODEL_LIB_GRP)):
				cmds.parent(result, "|{}|{}".format(RIG_GROUP, MODEL_LIB_GRP))

			if not cmds.objExists(LIBRARY_CACHE_SET):
				cmds.sets(cmds.sets(n=LIBRARY_CACHE_SET, em=True), add=RIG_SET)

			if not cmds.objExists(ENGINE_SET):
				cmds.sets(cmds.sets(n=ENGINE_SET, em=True), add=RIG_SET)

			cmds.sets(result, add=LIBRARY_CACHE_SET)
			cmds.sets(result, add=ENGINE_SET)

		return result


def get_current_references(type='Rig'):
	'''

	return:         short_name=return[0][n]
					full_path=return[1][n]
					ref_node=rig_refs[2][n]
					types=rig_refs[3][n]
	'''
	short_names = []
	full_paths = []
	ref_nodes = []
	types = []

	top_nodes = []

	reference_nodes = cmds.ls(type="reference")
	if 'sharedReferenceNode' in reference_nodes:
		reference_nodes.remove('sharedReferenceNode')

	if not reference_nodes:
		logging.info("No references exist in scene")
		return
	else:
		for rn in reference_nodes:
			short_name = cmds.referenceQuery(rn, filename=True, shortName=True)
			long_path = cmds.referenceQuery(rn, filename=True)
			node = cmds.referenceQuery(rn, referenceNode=True, topReference=True)
			if type in short_name or type in long_path:
				top_nodes.append(node)
		# short_names.append(short_name)
		# full_paths.append(long_path)
		# ref_nodes.append(rn)
		# types.append(type)

	return top_nodes


def clean(freeze_transforms=True,
          zero_pivots=True,
          unlock_normals=True,
          soften_normals=True,
          rename_shape_nodes=True,
          delete_intermediate_objects=True,
          delete_layers=True,
          delete_namespaces=True,
          delete_history=True,
          check_clashing_node_names=True,
          remove_unknown_plugins=True,
          unlock_transforms=True):
	"""

	:param freeze_transforms:
	:param zero_pivots:
	:param unlock_normals:
	:param soften_normals:
	:param rename_shape_nodes:
	:param delete_intermediate_objects:
	:param delete_layers:
	:param delete_namespaces:
	:param delete_history:
	:param check_clashing_node_names:
	:param remove_unknown_plugins:
	:param unlock_transforms:
	:return:
	"""
	if delete_intermediate_objects:
		intermediates = [g for g in cmds.ls(type=["mesh", "nurbsSurface", "nurbsCurve"])
		                 if cmds.getAttr(g + ".intermediateObject")]

		if intermediates:
			cmds.delete(intermediates)

	meshes = cmds.ls(type="mesh")
	shapes = cmds.ls(type=["mesh", "nurbsSurface", "nurbsCurve"])
	transforms = [n for n in cmds.ls(type="transform") if n not in ["front", "persp", "side", "top"]]

	if unlock_transforms:
		attributeslib.set_attributes(transforms, ["t", "r", "s", "v"], lock=False, keyable=True)

	if freeze_transforms:
		cmds.makeIdentity(transforms, apply=1, t=1, r=1, s=1, n=0, pn=1)

	if zero_pivots:
		cmds.xform(transforms, piv=[0, 0, 0])

	if unlock_normals:
		cmds.select(meshes)
		mel.eval("UnlockNormals;")

	if soften_normals:
		cmds.select(meshes)
		mel.eval("SoftPolyEdgeElements 1;")

	if delete_layers:
		layers = [l for l in cmds.ls(type="displayLayer") if l not in ["defaultLayer"]]
		if layers:
			cmds.delete(layers)

	if delete_namespaces:
		namespaces = [n for n in cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) if n not in ["UI", "shared"]]
		for namespace in namespaces:
			cmds.namespace(mergeNamespaceWithRoot=True, removeNamespace=namespace)

	if rename_shape_nodes:
		for shape in shapes:
			name = "{}Shape".format(selectionlib.get_transform(shape)).split("|")[-1]
			if shape != name:
				cmds.rename(shape, name)

	if check_clashing_node_names:
		nodepathlib.print_clashing_nodes_names()

	if remove_unknown_plugins:
		utilslib.scene.remove_unknown_nodes_and_plugins()

	if delete_history:
		cmds.DeleteAllHistory()


def connect_mocap_skel_to_rig(rig_top_node=None, mocap_top_node=None):
	"""

	"""


#
# def zero_rig(ns=":", *args):
#     start = -100
#     zero_frame = -100
#     cmds.currentTime(-100, e=1)
#     ctrls = (ns + 'all_ctrls')
#     if not cmds.objExists(ctrls, *args):
#         ctrls = cmds.ls(ns + '*_anim', ns + "*_CTL", ns + "*_Control", ns + "*_Controller")
#     if not ctrls:
#         return ('cannot find controls to apply mocap to, please check rig')
#     cmds.select(ctrls)
#     cmds.currentTime(zero_frame, e=1)
#     resetDefaultValues(nodes=ctrls)
#     cmds.select(cl=1)
#     cmds.currentTime(start, e=1)
#
#
# def resetDefaultValues(nodes=None, *args):
#     nodes = cmds.ls(sl=1, type='transform')
#     for each in nodes:
#         attrs = cmds.listAttr(each, k=1, v=1, u=1)
#         zeros = ["
# translateX', "
# translateY', "
# translateZ', "
# rotateX', "
# rotateY', "
# rotateZ']
#         for attr in attrs:
#             if attr in zeros:
#                 cmds.setAttr(each + '.' + attr, 0)
#             if attrs == 'scaleX' or attrs == 'scaleY' or attrs == 'scaleZ' or attrs == 'globalScale':
#                 cmds.setAttr(each + '.' + attr, 1)
#             else:
#                 try:
#                     dv = cmds.attributeQuery(attr, n=each, ld=1)
#                     cmds.setAttr(each + '.' + attr, dv[0])
#                 except:
#                     pass

def connect_mocap_to_anim_rig(rig_namespace=None, mocap_namespace=None, new_rig=False):
	"""

	"""
	# if new_rig:
	#     dict = {
	#         "C_hip_JNT":               "Maya_Hips",
	#         "L_thigh1_JNT":            "Maya_LeftUpLeg",
	#         "L_knee1_JNT":             "Maya_LeftLeg",
	#         "L_ankle_JNT":             "Maya_LeftFoot",
	#         "L_ball_JNT":              "Maya_LeftToeBase",
	#         "R_thigh1_JNT":            "Maya_RightUpLeg",
	#         "R_knee1_JNT":             "Maya_RightLeg",
	#         "R_ankle_JNT":             "Maya_RightFoot",
	#         "R_ball_JNT":              "Maya_RightToeBase",
	#         "C_spine1_JNT":            "Maya_Spine",
	#         "C_chest_JNT":             "Maya_Spine1",
	#         "L_shoulder_JNT":          "Maya_LeftShoulder",
	#         "L_arm1_JNT":              "Maya_LeftArm",
	#         "L_forearm1_JNT":          "Maya_LeftForeArm",
	#         "L_wrist_JNT":             "Maya_LeftHand",
	#         "C_neck_fk1_JNT":          "Maya_Neck",
	#         "C_neck_fk2_JNT":          "Maya_Neck1",
	#         "C_neck_fk3_JNT":          "Maya_Head",
	#         "R_shoulder_JNT":          "Maya_RightShoulder",
	#         "R_arm1_JNT":              "Maya_RightArm",
	#         "R_forearm1_JNT":          "Maya_RightForeArm",
	#         "R_wrist_JNT":             "Maya_RightHand",
	#         "C_upTeeth_fk1_JNT":       "Maya_joint_upper_teeth",
	#         "C_jaw_fk1_JNT":           "Maya_joint_jaw",
	#         "L_eye1_JNT":              "Maya_LeftEye",
	#         "R_eye1_JNT":              "Maya_RightEye",
	#         "L_thumb_finger_fk1_JNT":  "Maya_L_thumb_finger_fk1_JNT",
	#         "L_thumb_finger_fk2_JNT":  "Maya_L_thumb_finger_fk2_JNT",
	#         "L_thumb_finger_fk3_JNT":  "Maya_L_thumb_finger_fk3_JNT",
	#         "L_thumb_finger_fk4_JNT":  "Maya_L_thumb_finger_fk4_JNT",
	#         "L_index_finger_fk1_JNT":  "Maya_L_index_finger_fk1_JNT",
	#         "L_index_finger_fk2_JNT":  "Maya_L_index_finger_fk2_JNT",
	#         "L_index_finger_fk3_JNT":  "Maya_L_index_finger_fk3_JNT",
	#         "L_index_finger_fk4_JNT":  "Maya_L_index_finger_fk4_JNT",
	#         "L_middle_finger_fk1_JNT": "Maya_L_middle_finger_fk1_JNT",
	#         "L_middle_finger_fk2_JNT": "Maya_L_middle_finger_fk2_JNT",
	#         "L_middle_finger_fk3_JNT": "Maya_L_middle_finger_fk3_JNT",
	#         "L_middle_finger_fk4_JNT": "Maya_L_middle_finger_fk4_JNT",
	#
	#         "L_ring_finger_fk1_JNT":   "Maya_L_ring_finger_fk1_JNT",
	#         "L_ring_finger_fk2_JNT":   "Maya_L_ring_finger_fk2_JNT",
	#         "L_ring_finger_fk3_JNT":   "Maya_L_ring_finger_fk3_JNT",
	#         "L_ring_finger_fk4_JNT":   "Maya_L_ring_finger_fk4_JNT",
	#
	#         "L_pinky_finger_fk1_JNT":  "Maya_L_pinky_finger_fk1_JNT",
	#         "L_pinky_finger_fk2_JNT":  "Maya_L_pinky_finger_fk2_JNT",
	#         "L_pinky_finger_fk3_JNT":  "Maya_L_pinky_finger_fk3_JNT",
	#         "L_pinky_finger_fk4_JNT":  "Maya_L_pinky_finger_fk4_JNT",
	#
	#         "R_thumb_finger_fk1_JNT":  "Maya_R_thumb_finger_fk1_JNT",
	#         "R_thumb_finger_fk2_JNT":  "Maya_R_thumb_finger_fk2_JNT",
	#         "R_thumb_finger_fk3_JNT":  "Maya_R_thumb_finger_fk3_JNT",
	#
	#         "R_index_finger_fk1_JNT":  "Maya_R_index_finger_fk1_JNT",
	#         "R_index_finger_fk2_JNT":  "Maya_R_index_finger_fk2_JNT",
	#         "R_index_finger_fk3_JNT":  "Maya_R_index_finger_fk3_JNT",
	#         "R_index_finger_fk4_JNT":  "Maya_R_index_finger_fk4_JNT",
	#
	#         "R_middle_finger_fk1_JNT": "Maya_R_middle_finger_fk1_JNT",
	#         "R_middle_finger_fk2_JNT": "Maya_R_middle_finger_fk2_JNT",
	#         "R_middle_finger_fk3_JNT": "Maya_R_middle_finger_fk3_JNT",
	#         "R_middle_finger_fk4_JNT": "Maya_R_middle_finger_fk4_JNT",
	#
	#         "R_ring_finger_fk1_JNT":   "Maya_R_ring_finger_fk1_JNT",
	#         "R_ring_finger_fk2_JNT":   "Maya_R_ring_finger_fk2_JNT",
	#         "R_ring_finger_fk3_JNT":   "Maya_R_ring_finger_fk3_JNT",
	#         "R_ring_finger_fk4_JNT":   "Maya_R_ring_finger_fk4_JNT",
	#
	#         "R_pinky_finger_fk1_JNT":  "Maya_R_pinky_finger_fk1_JNT",
	#         "R_pinky_finger_fk2_JNT":  "Maya_R_pinky_finger_fk2_JNT",
	#         "R_pinky_finger_fk3_JNT":  "Maya_R_pinky_finger_fk3_JNT",
	#         "R_pinky_finger_fk4_JNT":  "Maya_R_pinky_finger_fk4_JNT"}
	#
	# else:
	dict = {
		"hips_Mid_jnt": "Maya_Hips",
		"thigh_Lt_jnt": "Maya_LeftUpLeg",
		"knee_Lt_jnt": "Maya_LeftLeg",
		"foot_Lt_bind": "Maya_LeftFoot",
		"toe_Lt_bind": "Maya_LeftToeBase",
		"thigh_Rt_jnt": "Maya_RightUpLeg",
		"knee_Rt_jnt": "Maya_RightLeg",
		"foot_Rt_bind": "Maya_RightFoot",
		"toe_Rt_bind": "Maya_RightToeBase",
		"chest_Mid_bind": "Maya_Spine1",
		"spine01_Mid_jnt": "Maya_Spine",
		"clavicle_Lt_bind": "Maya_LeftShoulder",
		"shoulder_Lt_jnt": "Maya_LeftArm",
		"elbow_Lt_jnt": "Maya_LeftForeArm",
		"wrist_Lt_bind": "Maya_LeftHand",
		"joint_neck_01": "Maya_Neck",
		"joint_neck_02": "Maya_Neck01",
		"joint_head": "Maya_Head",
		"clavicle_Rt_bind": "Maya_RightShoulder",
		"shoulder_Rt_jnt": "Maya_RightArm",
		"elbow_Rt_jnt": "Maya_RightForeArm",
		"wrist_Rt_bind": "Maya_RightHand",
		"ADJUST_joint_upper_teeth": "Maya_upTeeth_fk1",
		"ADJUST_joint_jaw": "Maya_jaw_fk1",
		"ADJUST_joint_left_eye": "Maya_Lefteye1",
		"ADJUST_joint_right_eye": "Maya_Righteye1",
		"thumbCarpal_Lt_bind": "Maya_Leftthumb_finger_fk1",
		"thumb01_Lt_bind": "Maya_Leftthumb_finger_fk2",
		"thumb02_Lt_bind": "Maya_Leftthumb_finger_fk3",
		"thumbEnd_Lt_bind": "Maya_Leftthumb_finger_fk4",
		"indexCarpal_Lt_bind": "Maya_Leftindex_finger_fk1",
		"index01_Lt_bind": "Maya_Leftindex_finger_fk2",
		"index02_Lt_bind": "Maya_Leftindex_finger_fk3",
		"index03_Lt_bind": "Maya_Leftindex_finger_fk4",
		"indexEnd_Lt_bind": "Maya_Leftindex_finger_fk5",
		"middleCarpal_Lt_bind": "Maya_Leftmiddle_finger_fk1",
		"middle01_Lt_bind": "Maya_Leftmiddle_finger_fk2",
		"middle02_Lt_bind": "Maya_Leftmiddle_finger_fk3",
		"middle03_Lt_bind": "Maya_Leftmiddle_finger_fk4",
		"middleEnd_Lt_bind": "Maya_Leftmiddle_finger_fk5",
		"ringCarpal_Lt_bind": "Maya_Leftring_finger_fk1",
		"ring01_Lt_bind": "Maya_Leftring_finger_fk2",
		"ring02_Lt_bind": "Maya_Leftring_finger_fk3",
		"ring03_Lt_bind": "Maya_Leftring_finger_fk4",
		"ringEnd_Lt_bind": "Maya_Leftring_finger_fk5",
		"pinkyCarpal_Lt_bind": "Maya_Leftpinky_finger_fk1",
		"pinky01_Lt_bind": "Maya_Leftpinky_finger_fk2",
		"pinky02_Lt_bind": "Maya_Leftpinky_finger_fk3",
		"pinky03_Lt_bind": "Maya_Leftpinky_finger_fk4",
		"thumbCarpal_Rt_bind": "Maya_Rightthumb_finger_fk1",
		"thumb01_Rt_bind": "Maya_Rightthumb_finger_fk2",
		"thumb02_Rt_bind": "Maya_Rightthumb_finger_fk3",
		"thumbEnd_Rt_bind": "Maya_Rightthumb_finger_fk4",
		"indexCarpal_Rt_bind": "Maya_Rightindex_finger_fk1",
		"index01_Rt_bind": "Maya_Rightindex_finger_fk2",
		"index02_Rt_bind": "Maya_Rightindex_finger_fk3",
		"index03_Rt_bind": "Maya_Rightindex_finger_fk4",
		"indexEnd_Rt_bind": "Maya_Rightindex_finger_fk5",
		"middleCarpal_Rt_bind": "Maya_Rightmiddle_finger_fk1",
		"middle01_Rt_bind": "Maya_Rightmiddle_finger_fk2",
		"middle02_Rt_bind": "Maya_Rightmiddle_finger_fk3",
		"middle03_Rt_bind": "Maya_Rightmiddle_finger_fk4",
		"middleEnd_Rt_bind": "Maya_Rightmiddle_finger_fk5",
		"ringCarpal_Rt_bind": "Maya_Rightring_finger_fk1",
		"ring01_Rt_bind": "Maya_Rightring_finger_fk2",
		"ring02_Rt_bind": "Maya_Rightring_finger_fk3",
		"ring03_Rt_bind": "Maya_Rightring_finger_fk4",
		"ringEnd_Rt_bind": "Maya_Rightring_finger_fk5",
		"pinkyCarpal_Rt_bind": "Maya_Rightpinky_finger_fk1",
		"pinky01_Rt_bind": "Maya_Rightpinky_finger_fk2",
		"pinky02_Rt_bind": "Maya_Rightpinky_finger_fk3",
		"pinky03_Rt_bind": "Maya_Rightpinky_finger_fk4"}

	if not rig_namespace:
		rig_node = cmds.ls("*:rig_GRP")
		if rig_node:
			rig_namespace = rig_node[0].split(":")[0] + ":"
		else:
			rig_namespace = ""

	if not mocap_namespace:
		mocap_node = cmds.ls("*:mocap_rig_GRP")
		if mocap_node:
			mocap_namespace = mocap_nodee[0].split(":")[0] + ":"
		else:
			mocap_namespace = ""

	keys = list(dict.keys())
	for key in keys:
		driven = mocap_namespace + dict.get(key)
		driver = rig_namespace + key
		if not cmds.objExists(driver):
			print(driver + "does not exist.  skipping")
			continue
		if not cmds.objExists(driven):
			print(driven + " does not exist. skipping")
			continue
		constraint = cmds.parentConstraint(driver, driven, mo=1)
		cmds.setAttr(constraint[0] + ".interpType", 2)
		print("done connecting " + driven + " to " + driver)
