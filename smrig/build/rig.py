import logging
import os
import shutil

import maya.cmds as cmds
import maya.mel as mel
from smrig import dataio
from smrig import env
from smrig import partslib
from smrig.lib import attributeslib
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import mocaplib
from smrig.lib import nodepathlib
from smrig.lib import nodeslib
from smrig.lib import pathlib
from smrig.lib import selectionlib
from smrig.lib import utilslib
from smrig.lib.constantlib import RIG_SET, CONTROL_SET, ENGINE_SET, ENGINE_EXCLUDE_SET, \
	JOINTS_GROUP, PARTS_GROUP, VISIBILITY_CONTROL, NO_TRANSFORM_GROUP, MODEL_GROUP, RIG_GROUP, ROOT_JOINT

log = logging.getLogger("smrig.build.rig")

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"

exclude_lock = ["joint"]
historical_interest_excluded = ["wrap", "nonLinear", "skinCluster", "cluster", "blendShape",
                                "deltaMush", "ffd", "sculpt", "poseInterpolator", "parentConstraint",
                                "pointConstraint", "orientConstraint", "normalConstraint", "scaleConstraint",
                                "poleVectorConstraint", "geometryConstraint", "transform", "joint"]


def save_scene(asset=None, description=None, version=None):
	"""
	Save guides maya file.

	:param str asset:
	:param str description:
	:param str version:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()
	description = description if description else env.asset.get_variant()

	if not asset:
		log.error("Asset not set")
		return

	file_name = "{}_rig_{}".format(asset, description)
	directory = pathlib.normpath(os.path.join(os.path.dirname(env.asset.get_rigbuild_path()), "rig"))
	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	cmds.file(rename=file_path)
	cmds.file(save=True, type=maya_file_type)

	env.asset.write_info_file()
	log.info("Saved rig scene: {}".format(pathlib.normpath(file_path)))


def set_lookdev_workspace(asset=None):
	"""

	"""

	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	model_filepath = env.asset.get_models()[0].get("file_path")
	workspace_path = pathlib.normpath(model_filepath.split("scenes")[0])
	if os.path.exists(workspace_path):
		mel.eval('setProject "{0}"'.format(workspace_path))


def get_description():
	result = cmds.promptDialog(
		title='Description',
		message='Character Description:',
		button=['OK', 'Default'],
		defaultButton='OK',
		cancelButton='Default',
		dismissString='Default')

	if result == 'OK':
		description = cmds.promptDialog(query=True, text=True)

	if result == "Default":
		description = env.asset.get_variant()

	return description


def save_rig_scene(asset=None, description=None, version=None, tag_node=None, file_browser=False):
	"""
	Save maya versioned and versionless rig file.

	:param str/None asset:
	:param str description:
	:param int version:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()
	# description = description if description else env.asset.get_variant()
	description = description if description else get_description()

	if not asset:
		log.error("Asset not set")
		return

	directory = ""
	file_name = "{}_Rig_{}".format(description, asset)
	if file_browser:
		directory = dataio.utils.browser(action="export", extension="mb")
	else:
		directory = pathlib.normpath(
			os.path.join(os.path.dirname(env.asset.get_rigbuild_path()), "scenes", "Rig", description))
	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	if not tag_node and cmds.objExists("rig_GRP"):
		tag_node = "rig_GRP"
		attributeslib.tag.add_tag_attribute(node=tag_node, attribute_name="versionPath", value=file_path)

	cmds.file(rename=file_path)
	cmds.file(save=True, type=maya_file_type)

	log.info("Saved versioned scene: {}".format(pathlib.normpath(file_path)))

	latest_file_name = file_name + "." + maya_file_extention
	latest_file_path = pathlib.normpath(os.path.join(directory, latest_file_name))
	cmds.file(rename=latest_file_path)
	cmds.file(save=True, type=maya_file_type)

	log.info("Saved latest versionless scene: {}".format(pathlib.normpath(latest_file_path)))


def save_rig_to_asset(asset=None, variant="", description=None, version=None, tag_node=None, file_browser=False):
	"""
	Save maya versioned and versionless rig file.

	:param str/None asset:
	:param str description:
	:param int version:
	:return:
	"""
	asset = asset if asset else env.asset.get_asset()
	variant = variant if variant else env.asset.get_variant()
	description = description if description else get_description()
	rig_type = "SM_Rig"

	if variant == "metahuman":
		rig_type = "MH_Rig"

	lookdev_data = env.asset.get_models()[0]
	lookdev_filepath = lookdev_data["file_path"]
	lookdev_filename = lookdev_filepath.split("/")[-1]
	lookdev_dir = lookdev_filepath.replace(lookdev_filename, "")
	lookdev_dir = pathlib.normpath(os.path.join(lookdev_dir, "Rig"))

	if not asset:
		log.error("Asset not set")
		return

	directory = ""
	file_name = "{}_{}_Rig_{}".format(description, rig_type, asset)
	if file_browser:
		directory = dataio.utils.browser(action="export", extension="mb")
	else:
		directory = pathlib.normpath(os.path.join(lookdev_dir, rig_type, description))

	pathlib.make_dirs(directory)

	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	file_path = version_object.get_save_version_path(version, new_version=False if version else True)

	if not tag_node and cmds.objExists("rig_GRP"):
		tag_node = "rig_GRP"
		attributeslib.tag.add_tag_attribute(node=tag_node, attribute_name="versionPath", value=file_path)

	cmds.file(rename=file_path)
	cmds.file(save=True, type=maya_file_type)

	log.info("Saved versioned scene: {}".format(pathlib.normpath(file_path)))

	latest_file_name = file_name + "." + maya_file_extention
	latest_file_path = pathlib.normpath(os.path.join(directory, latest_file_name))
	cmds.file(rename=latest_file_path)
	cmds.file(save=True, type=maya_file_type)

	log.info("Saved latest versionless scene: {}".format(pathlib.normpath(latest_file_path)))

	reference_file_name = description + "_Integration_START.mb"
	# lookdev_split = lookdev_filepath.split("/")[0 : -1]
	lookdev_data = env.asset.get_models()[0]
	lookdev_filepath = lookdev_data["file_path"].split("scenes")[0]
	reference_file_path = pathlib.normpath(os.path.join(lookdev_filepath, "scenes", reference_file_name))
	if not os.path.exists(reference_file_path):
		cmds.file(new=True, force=True)
		cmds.file(latest_file_path, reference=True, namespace=":")
		cmds.file(rename=reference_file_path)
		cmds.file(save=True, type=maya_file_type)
		log.info("Referenced Rig into Integration_START scene: {}".format(pathlib.normpath(reference_file_path)))


def connect_parent_drivers():
	"""
	Connect parent drivers via matrix constraint.

	:return:
	"""
	parts = [partslib.part(p) for p in partslib.utils.get_guides_in_scene()]
	for part in parts:
		parent_drivers = {part.format_name([part.part_type, d], node_type="transform"): v.get("value")
		                  for d, v in part.options.items() if v.get("data_type") == "parent_driver"}

		for grp, driver in parent_drivers.items():
			if cmds.objExists(grp) and cmds.objExists(driver):
				constraintslib.matrix_constraint(driver, grp, maintain_offset=True)

			else:
				log.warning("{}: Cannot connect parent driver, missing one or more nodes: ['{}', '{}']".format(part,
				                                                                                               grp,
				                                                                                               driver))


def connect_attribute_drivers():
	"""
	Connect attribute drivers via direct connection.

	:return:
	"""
	parts = [partslib.part(p) for p in partslib.utils.get_guides_in_scene()]
	for part in parts:
		parent_drivers = {part.format_name([part.part_type, d], node_type="transform"): v.get("value")
		                  for d, v in part.options.items() if v.get("data_type") == "attribute_driver"}

		for grp, driver in parent_drivers.items():
			if cmds.objExists(grp) and cmds.objExists(driver):
				attr_data = dataio.types.user_defined_attributes.get_data(grp)
				attr_data[driver] = dict(attr_data[grp])
				del attr_data[grp]

				dataio.types.user_defined_attributes.set_data(attr_data)
				for attr in attr_data[driver].get("attr_order"):
					try:
						cmds.connectAttr("{}.{}".format(driver, attr), "{}.{}".format(grp, attr), f=True)
					except:
						log.warning("{}: Cannot connect {}.{} to {}.{}".format(part, driver, attr, grp, attr))

			else:
				log.warning("{}: Cannot connect parent driver, missing one or more nodes: ['{}', '{}']".format(part,
				                                                                                               grp,
				                                                                                               driver))


def add_controls_to_control_set():
	"""
	Add all *_CTL nodes to controls selection set.

	:return:
	"""
	parts = selectionlib.get_children("parts_GRP")

	for part in parts:
		ctrls = [n for n in selectionlib.get_children(part, all_descendents=True) if
		         cmds.objExists(n + ".smrigControl")]
		ctrls = [c for c in ctrls if selectionlib.get_shapes(c)]

		if not cmds.objExists(CONTROL_SET):
			cmds.sets(cmds.sets(n=CONTROL_SET, em=True), add=RIG_SET)

		ctrl_set = cmds.sets(ctrls, n=part.replace("part_GRP", "control_SEL"))
		cmds.sets(ctrl_set, add=CONTROL_SET)


def add_joints_to_engine_set():
	"""
	Add all *_JNT joints to game engine selection saet.

	:return:
	"""
	joints = selectionlib.get_children(JOINTS_GROUP, all_descendents=True, types="joint")
	joints = selectionlib.sort_by_hierarchy(joints)

	if not cmds.objExists(ENGINE_SET):
		cmds.sets(cmds.sets(n=ENGINE_SET, em=True), add=RIG_SET)

	nodes = cmds.ls(NO_TRANSFORM_GROUP, PARTS_GROUP)
	if nodes:
		if not cmds.objExists(ENGINE_EXCLUDE_SET):
			cmds.sets(cmds.sets(n=ENGINE_EXCLUDE_SET, em=True), add=RIG_SET)

		cmds.sets(NO_TRANSFORM_GROUP, PARTS_GROUP, add=ENGINE_EXCLUDE_SET)
	cmds.sets(joints, add=ENGINE_SET)


def populate_sets():
	"""
	Add controls and joints to their respective selection sets.

	:return:
	"""
	add_controls_to_control_set()
	add_joints_to_engine_set()


def delete_stashed_guides():
	"""
	Delete stashed:guides_GRP.

	:return:
	"""
	# first we need to rename ik solver nodes so they dont get deleted
	namespace = utilslib.scene.STASH_NAMESPACE

	nodes = [n for n in cmds.ls(type=["ikSplineSolver", "ikRPsolver", "ikSCsolver"]) if n.startswith(namespace)]
	for node in nodes:
		cmds.rename(node, nodepathlib.remove_namespace(node))

	cmds.delete(cmds.ls("{}:*".format(namespace)))


def set_historical_interest(state=False):
	"""
	Turn off historical interest on all nodes. this makes ht channel box cleaner and hides inputs nad outputs
	except those in exluded types

	:param bool state:
	:return:
	"""
	nodes = [n for n in cmds.ls()]
	ex_nodes = [n for n in cmds.ls() if cmds.nodeType(n) in historical_interest_excluded]
	set_nodes = nodes - ex_nodes

	nodeslib.display.set_historical_importance(nodes, state)


def set_visibility_defaults():
	"""
	Set default visibility settings on rig

	:return:
	"""
	if not cmds.objExists(VISIBILITY_CONTROL):
		return

	cmds.setAttr("{}.controlsVisibility".format(VISIBILITY_CONTROL), 1)
	cmds.setAttr("{}.offsetControlsVisibility".format(VISIBILITY_CONTROL), 1)
	cmds.setAttr("{}.modelVisibility".format(VISIBILITY_CONTROL), 1)
	cmds.setAttr("{}.jointsVisibility".format(VISIBILITY_CONTROL), 0)
	cmds.setAttr("{}.rigVisibility".format(VISIBILITY_CONTROL), 0)
	cmds.setAttr("{}.modelDisplay".format(VISIBILITY_CONTROL), 2)
	cmds.setAttr("{}.jointDisplay".format(VISIBILITY_CONTROL), 2)
	cmds.setAttr("{}.modelResolution".format(VISIBILITY_CONTROL), 0)


def lock_control_group_hierarchy():
	"""
	Lock all groups nodes in control hierarchy.

	:return:
	"""
	parts = selectionlib.get_children("parts_GRP")
	lock_nodes = []

	for part in parts:
		groups = selectionlib.get_children(part)
		for group in groups:
			groups2 = selectionlib.get_children(group)
			ct_groups = [g for g in groups2 if "control" in g]
			for ct_group in ct_groups:
				ct_nodes = selectionlib.get_children(ct_group, all_descendents=True)

				ctrls = [controlslib.Control(n) for n in ct_nodes if cmds.objExists(n + ".smrigControl")]
				exclude_nodes = []

				for ctrl in ctrls:
					try:
						if ctrl.groups:
							# exclude_nodes.append(ctrl.groups[0])
							pass

						exclude_nodes.extend(ctrl.all_controls)

					except:
						pass

				lock_nodes.extend([c for c in ct_nodes if c not in exclude_nodes])

	lock_nodes = [n for n in lock_nodes if cmds.nodeType(n) not in exclude_lock]

	if lock_nodes:
		attributeslib.set_attributes(lock_nodes,
		                             ["t", "r", "s", "v", "ro"],
		                             lock=True,
		                             keyable=False,
		                             channel_box=False)


def parent_constraint_noxform():
	"""
	Parent all constraints that are under the joint_GRP to noxform_GRP

	:return:
	"""
	nodes = selectionlib.get_children(JOINTS_GROUP, all_descendents=True)
	cons = [n for n in nodes if "Constraint" in cmds.nodeType(n)]

	if cons:
		con_grp = "constraints_GRP"
		if not cmds.objExists(con_grp):
			con_grp = cmds.createNode("transform", n="constraints_GRP", p=NO_TRANSFORM_GROUP)

		cmds.parent(cons, con_grp)


def build_mocap_root():
	"""
	Build mocap rig hierarchy.

	:return:
	"""
	cmds.createNode("transform", n=RIG_GROUP)
	cmds.createNode("transform", n=JOINTS_GROUP, p=RIG_GROUP)
	cmds.createNode("transform", n=MODEL_GROUP, p=RIG_GROUP)
	cmds.parent(ROOT_JOINT, JOINTS_GROUP)

	cmds.sets(RIG_GROUP, n=RIG_SET)

	add_joints_to_engine_set()


def build_mocap_bake_skeleton():
	"""
	This builds ref skeleton to bake mocap to controls.

	:return:
	"""
	joints = mocaplib.skeleton.build_mocap_skeleton(suffix="MOCAP")
	mocaplib.pose.create_tpose_from_labels(descriptor="MOCAP")
	cmds.parent(joints[0], NO_TRANSFORM_GROUP)
	cmds.hide(joints[0])


def reference_connect_cache_render_scenes(asset=None):
	asset = env.asset.get_asset()
	if not asset:
		log.error("Asset not set")
		return

	model_filepath = pathlib.normpath(env.asset.get_models()[0].get("file_path"))
	print(model_filepath)
	cmds.file(model_filepath, reference=True, namespace=":RENDER")

	current_scene = cmds.file(expandName=True, query=True)
	scene_number = current_scene.split("/")[-2]
	if scene_number == "scenes":
		scene_number = "000"

	source_abc_folder = pathlib.normpath(
		os.path.join(env.asset.get_paths()[0].replace("rigbuild", "cache"), "alembic", "000_cache"))
	dest_abc_folder = pathlib.normpath(
		os.path.join(model_filepath.split("/scenes")[0], "cache", "alembic", scene_number + "_cache"))
	dest_filename = pathlib.normpath(os.path.join(dest_abc_folder, scene_number + "_face_export.abc"))

	if not os.path.exists(dest_abc_folder):
		shutil.copytree(source_abc_folder, dest_abc_folder, dirs_exist_ok=True)
		source_filename = pathlib.normpath(os.path.join(dest_abc_folder, "face_export.abc"))
		dest_filepath = pathlib.normpath(os.path.join(dest_abc_folder, "face_export.abc"))
		os.rename(dest_filepath, os.path.join(dest_abc_folder, dest_filename))

	if os.path.isfile(dest_filename):
		print("exists")
		cmds.file(dest_filename, reference=True, namespace=":CACHE")

	nss = ["CACHE", "RENDER"]
	geos = ["Head_hi", "Body_hi", "Eyes_hi", "Caruncles_hi", "Teeth_hi"]
	for geo in geos:
		src = nss[0] + ":" + geo
		if not cmds.objExists(src):
			return ("CACHE reference for " + geo + " not found in scene")
		target = nss[1] + ":" + geo
		if not cmds.objExists(target):
			return ("CACHE reference for " + target + " not found in scene")
		if cmds.objExists(target + "_BSH"):
			cmds.confirmDialog(title='blendshapeExists', message='Blendshape Already Exists', button=['OK', 'Cancel'],
			                   defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
			return ("blendshape already exists")
		bs = cmds.blendShape(src, target, o="world", foc=1, name=target + "_BSH")
		cmds.setAttr(bs[0] + "." + geo, 1)


# version_object = pathlib.Version(cache_folder, scene_number+"_cache", "abc")
# file_path = version_object.get_save_version_path(version, new_version=False if version else True)


'''
from smrig import env
from smrig.lib import pathlib
import shutil


def reference_cache_render_scenes(asset=None):
	asset = asset if asset else env.asset.get_asset()
	if not asset:
		log.error("Asset not set")
		return
	
	model_filepath = pathlib.normpath(env.asset.get_models()[0].get("file_path"))
	print (model_filepath)
	cmds.file(model_filepath, reference=True, namespace=":RENDER")
	
	current_scene=cmds.file (expandName=True, query=True)
	scene_number = current_scene.split("/")[-2]
	if scene_number == "scenes":
		scene_number = "000"
		
		
	source_abc_folder = pathlib.normpath(os.path.join(env.asset.get_paths()[0].replace("rigbuild", "cache"), "alembic", "000"))
	dest_abc_folder = pathlib.normpath(os.path.join(model_filepath.split("/scenes")[0], "cache", "alembic", scene_number))
	dest_filename = pathlib.normpath(os.path.join(dest_abc_folder, scene_number+"_face_export.abc"))
	
	if not os.path.exists(dest_abc_folder):
		shutil.copytree(source_abc_folder, dest_abc_folder, dirs_exist_ok=True)
		source_filename = pathlib.normpath(os.path.join(dest_abc_folder, "face_export.abc"))
		dest_filepath = pathlib.normpath(os.path.join(dest_abc_folder, "face_export.abc"))
		os.rename (dest_filepath, os.path.join(dest_abc_folder, dest_filename))
		
	if os.path.isfile(dest_filename):
		print ("exists")
		cmds.file(dest_filename, reference=True, namespace=":CACHE")			


	nss = ["CACHE", "RENDER"]
	geos = ["Head_hi", "Body_hi", "Eyes_hi", "Caruncles_hi", "Teeth_hi"]		
	for geo in geos:
		src = nss[0]+":"+geo
		if not cmds.objExists(src):
			return ("CACHE reference for "+geo+" not found in scene")
		target = nss[1]+":"+geo
		if not cmds.objExists(target):
			return ("CACHE reference for "+target+" not found in scene")
		if cmds.objExists(target+"_BSH"):
			cmds.confirmDialog( title='blendshapeExists', message='Blendshape Already Exists', button=['OK','Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel' )
			return ("blendshape already exists")
		bs=cmds.blendShape(src, target, o="world", foc=1, name=target+"_BSH")
		cmds.setAttr (bs[0]+"."+geo, 1)
	
			
reference_cache_render_scenes()		
		
	
def get_cache_dir_from_current_scene():

    asset = env.asset.get_asset()
    if not asset:
        log.error("Asset not set")
        return

    model_filepath = pathlib.normpath(env.asset.get_models()[0].get("file_path"))


    current_scene = cmds.file(expandName=True, query=True)
    scene_number = current_scene.split("/")[-1]
    if scene_number == "scenes":
        scene_number = "000"

    cache_folder = pathlib.normpath(
        os.path.join(model_filepath.split("/scenes")[0], "cache", "alembic", scene_number + "_cache"))

    return (cache_folder, scene_number)

def export_alembic ():
    """
    Save maya versioned and versionless rig file.

    :param str/None asset:
    :param str description:
    :param int version:
    :return:
    """

    # start_frame = start_frame if start_frame else cmds.playbackOptions(query=True, minTime=True)
    # end_frame = end_frame if end_frame else cmds.playbackOptions(query=True, maxTime=True)
    start_frame =  str(cmds.playbackOptions(query=True, minTime=True))
    end_frame =  str(cmds.playbackOptions(query=True, maxTime=True))


   # command = "-frameRange " + start + " " + end + " -uvWrite -worldSpace " + root + " -file " + save_name

    cache_folder = get_cache_dir_from_current_scene()[0]
    scene_number =  get_cache_dir_from_current_scene()[1]
    if not os.path.exists(cache_folder):
        pathlib.make_dirs(cache_folder)

    filepath=pathlib.normpath(os.path.join(cache_folder, scene_number+"_cache.abc"))
    root = "-root high_model_GRP"
    command = "-frameRange " + start_frame + " " + end_frame + " -uvWrite -worldSpace " + root + " -file " + filepath
    cmds.AbcExport(j=command)
    
    
    
build.rig.ex
	

from smrig import build
reload_hierarchy(build)

build.rig.reference_connect_cache_render_scenes()



AbcExport -j "-frameRange 0 700 -dataFormat ogawa -root |rig_GRP|model_GRP|high_model_GRP|Head_hi -root |rig_GRP|model_GRP|high_model_GRP|Body_hi -root |rig_GRP|model_GRP|high_model_GRP|Eyes_hi -root |rig_GRP|model_GRP|high_model_GRP|Caruncles_hi -root |rig_GRP|model_GRP|high_model_GRP|Teeth_hi -file X:/Character/Rigging/Rig/Jobs/V2/PRODUCTION_V2/FACE/cache/alembic/vid_002_cache/vid_002_cache.abc";


start = 0
end = 120
root = "-root pSphere1 -root pCube1"
save_name = "c:\documents\maya\project\default\cache\alembicTest.abc"
command = "-frameRange " + start + " " + end +" -uvWrite -worldSpace " + root + " -file " + save_name
cmd.AbcExport ( j = command )



cmds.timeControl(rangeVisible=True, query=True)

'''
