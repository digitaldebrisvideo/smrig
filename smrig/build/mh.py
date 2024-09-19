import logging
import os

import maya.cmds as cmds
import maya.mel as mel
from smrig import env
from smrig.lib import pathlib, utilslib, transformslib, attributeslib, selectionlib

log = logging.getLogger("smrig.build.mh")
from smrig import build


def get_mh_path_dir(asset=None):
	"""
	Get the path directory for an asset in the MH (MetaHuman) project.

	Parameters:
	- asset (str): The name of the asset. If not specified, the function will return the path directory for the entire MH project.

	Returns:
	- str: The path directory for the asset in the MH project.

	Note:
	- This function assumes that the MH project has a specific directory structure where each asset has its own directory within the project.
	"""

	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	model_filepath = env.asset.get_models()[0].get("file_path")
	folder = model_filepath.replace(model_filepath.split("/")[-1], "")
	rig_folder = pathlib.normpath(os.path.join(folder, "Rig", "MH_Rig"))
	return rig_folder


def get_mh_rigbuild_dir(asset=None):
	"""
	get_mh_rigbuild_dir(asset=None)

	This function retrieves the rigbuild directory path for a given asset or the current asset if none is specified.

	Parameters:
	- asset (optional): The asset to retrieve the rigbuild directory for. If not specified, it defaults to the current asset.

	Returns:
	- rigbuildpath (string): The absolute path of the rigbuild directory.

	Example:
	get_mh_rigbuild_dir(asset="Character01")
	"""
	asset = asset if asset else env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	model_filepath = env.asset.get_models()[0].get("file_path")
	folders = model_filepath.split("scenes")[0]
	rigbuildpath = pathlib.normpath(os.path.join(folders, "rigbuild", "dataio"))

	if not os.path.exists(rigbuildpath):
		pathlib.make_dirs(rigbuildpath)

	return rigbuildpath


def get_asset_output():
	"""
	This function is used to get the output asset name from the environment.

	Parameters:
	    None

	Returns:
	    str: The output asset name

	Example:
	    >>> get_asset_output()
	    'scene_name'
	"""
	model_filepath = env.asset.get_models()[0].get("file_path")
	scene_name = model_filepath.split("/")[-1].replace(".mb", "")
	return (scene_name)


def set_workspace():
	"""
	Sets the workspace for the current asset.

	This function sets the workspace for the current asset by sourcing the workspace.mel file. The workspace.mel file is located in the same directory as the asset's model file.

	If the asset is not set, an error message is logged and the function returns.

	If the workspace file does not exist, the function returns a message stating that the workspace is not set.

	Parameters:
	None

	Returns:
	None if the workspace file exists and is sourced successfully.
	Message stating that the workspace is not set if the workspace file does not exist.

	"""
	# source workspacefile

	asset = env.asset.get_asset()

	if not asset:
		log.error("Asset not set")
		return

	model_filepath = env.asset.get_models()[0].get("file_path")
	split_file = model_filepath.split("scenes")
	workspace_file = pathlib.normpath(os.path.join(split_file[0], "workspace.mel"))

	if not os.path.isfile(workspace_file):
		return ("workspace not set because workspace does not exist")
	cmd = f"source \"{workspace_file}\""
	mel.eval(cmd)


def set_lookdev_workspace():
	"""
	Sets the look development workspace to the project's root directory.

	The set_lookdev_workspace function sets the current workspace in Maya to the root directory of the current project.

	Parameters:
	None

	Returns:
	None

	Raises:
	None

	Example:
	set_lookdev_workspace()
	"""

	workspace_path = pathlib.normpath(build.mh.get_mh_path_dir().split("scenes")[0])
	if os.path.exists(workspace_path):
		mel.eval('setProject "{0}"'.format(workspace_path))


def load_modified_metahuman_model(file_path=None):
	"""
	Function: load_modified_metahuman_model

	This function is used to load a modified version of the metahuman model file.

	Parameters:
	- file_path (str): The file path of the modified model file. If not provided, it will use the default file path.

	Returns:
	None

	Example:
	load_modified_metahuman_model(file_path="path/to/modified_model.mb")
	"""
	# load starter file
	# model_filepath = env.asset.get_models()[0].get("file_path")
	char_mh = pathlib.normpath(os.path.join(get_mh_rigbuild_dir(), "metahuman", "sourceAssets", "mh_2_sm_model.mb"))
	utilslib.scene.load(file_path=char_mh, action="import", namespace=None, rnn=False, force=True)


# def load_MH_starter_rig(file_path=None):
# 	"""
#
# 	:param str file_path:
# 	:return:
# 	"""
#
#
# 	dna_file = mhdna.py.CHARACTER_DNA
# 	# scene_path = pathlib.normpath(os.path.join(get_mh_rigbuild_dir(), "metahuman", "sourceAssets", "metahuman_source", "dna_calibration", "output",
# 	# 				 "BaseMH_modified.mb"))
# 	if os.path.exists(scene_path):
# 		utilslib.scene.load(file_path=scene_path, action="import", namespace=None, rnn=False, force=True)
# 	else:
# 		return ("cannot find the starter MH file")


def change_dna_path_attribute_resave():
	"""
	The function `change_dna_path_attribute_resave` is responsible for changing the DNA path attribute and resaving the Maya scene file.

	Parameters:
	    None

	Returns:
	    If the DNA file is not found, a message stating "cannot find dna file, make sure you have run prep model button in START tab" is returned.

	Usage:
	    This function should be called when you want to update the DNA path attribute of an embedded Archetype in Maya and save the scene file.

	Example:
	    ```python
	    change_dna_path_attribute_resave()
	    ```

	Note:
	    1. This function assumes that the necessary modules and functions have been imported beforehand.
	    2. This function uses the `pathlib` module from the Python standard library.
	"""
	dna_path = pathlib.normpath(
		os.path.join(get_mh_rigbuild_dir(), "metahuman", "sourceAssets", "metahuman_source", "dna_calibration", "data",
		             "BaseMH_modified.dna"))
	if not cmds.objExists("rl4Embedded_Archetype"):
		return ("cannot find dna file, make sure you have run prep model button in START tab")

	cmds.setAttr("rl4Embedded_Archetype.dnaFilePath", dna_path, type="string")
	path = env.asset.get_models()[0].get("file_path")
	scene = path.split("/")[-3]
	cmds.file(rename=scene + "_MH_Rig.mb")
	cmds.file(save=True, type="mayaBinary")


def match_mh_mesh_to_custom_mesh(model_filepath=None):
	"""
	match_mh_mesh_to_custom_mesh(model_filepath=None):
	    This function matches a MetaHuman mesh to a custom mesh in the scene.

	Parameters:
	    - model_filepath (optional): The file path of the custom mesh to import. If not provided, the function will use the first model file path available in the environment.

	Returns:
	    - If the custom mesh file does not exist, the function returns a string message indicating that the file does not exist.
	    - Otherwise, the function imports the custom mesh and performs various transformations and exports the modified mesh in both binary and OBJ formats.

	Notes:
	    - The function assumes the existence of certain files and directories, such as the MetaHuman wrapped file and the target mesh names ('Head_hi' and 'Teeth_hi').
	    - The 'transformslib' and 'utilslib' libraries are used for performing various operations on the scene.

	Example:
	    # Match MetaHuman mesh to custom mesh using default file path
	    match_mh_mesh_to_custom_mesh()

	    # Match MetaHuman mesh to custom mesh using specific file path
	    match_mh_mesh_to_custom_mesh('path/to/custom_mesh.obj')
	"""

	# wrap_file  = pathlib.normpath(os.path.join(get_mh_rigbuild_dir() , "metahuman" ,"sourceAssets", "MH_SM_wrapped.mb"))
	wrap_file = pathlib.normpath(os.path.join(build.mhdna.ROOT_DIR, "data", "source_assets", "MH_SM_wrapped.mb"))
	# wrap_file  = pathlib.normpath(os.path.join (, "MH_SM_wrapped.mb"))

	if not wrap_file:
		return ("File does not exist.  Make sure you have run Prep Model in previous step")

	utilslib.scene.load(file_path=wrap_file, action="import", namespace=None, rnn=False)

	if not model_filepath:
		model_filepath = env.asset.get_models()[0].get("file_path")
		if not os.path.exists(model_filepath):
			return ("cannot find {} ").format(model_filepath)

	utilslib.scene.load(model_filepath, action="import", rnn=False, namespace="")

	# right eye
	cmds.select("Eyes_hi.vtx[0:1054]")
	transformslib.xform.match_locator()
	r_eye_loc = cmds.ls(sl=1)[0]
	transformslib.xform.match(r_eye_loc, "SM_Eye_R_hi", translate=True, rotate=False, scale=False, pivot=False)

	cmds.select("Eyes_hi.vtx[1055:2109]")
	transformslib.xform.match_locator()
	l_eye_loc = cmds.ls(sl=1)[0]
	transformslib.xform.match(l_eye_loc, "SM_Eye_L_hi", translate=True, rotate=False, scale=False, pivot=False)

	targets = ['Head_hi', 'Teeth_hi']
	for t in targets:
		bs = cmds.blendShape(t, "SM_" + t)
		cmds.setAttr(bs[0] + "." + t, 1)

	models = ['teeth_MH2SM', 'eyeRight_MH2SM', 'eyeLeft_MH2SM', 'head_MH2SM']
	cmds.select(models)
	cmds.delete(ch=1)
	cmds.makeIdentity(apply=1, t=1, r=1, s=1, n=0, pn=1)

	folder = pathlib.normpath(os.path.join(get_mh_rigbuild_dir(), "metahuman", "sourceAssets"))
	export_file = pathlib.normpath(os.path.join(folder, "mh_2_sm_model.mb"))
	if os.path.isfile(export_file):
		os.remove(export_file)
	utilslib.scene.export(export_file, action="export_selection", file_type="mayaBinary")

	for model in models:
		if cmds.objExists(model):
			export_file = pathlib.normpath(os.path.join(folder, model + ".obj"))
			if os.path.exists(export_file):
				os.remove(export_file)
			cmds.select(model)
			utilslib.scene.export(export_file, action="export_selection", file_type="OBJexport")


def import_mh_objs(models=None):
	"""
	This function imports Metahuman objects into the scene.

	@param models: Optional. A list of Metahuman models to import. Default value is ['teeth_MH2SM', 'eyeRight_MH2SM', 'eyeLeft_MH2SM', 'head_MH2SM'].
	@return: A list of imported mesh nodes.

	The function first constructs the folder path by joining the Metahuman rigbuild directory with the sourceAssets folder using the `get_mh_rigbuild_dir()` function. It then initializes an empty list `mesh_nodes` to store the imported mesh nodes.

	If no `models` argument is provided, it uses the default list of models. Otherwise, it uses the provided list.

	For each model in the `models` list, it constructs the object directory path by joining the folder path with the model name followed by ".obj". It then imports the object nodes using the `utilslib.scene.load()` function, specifying the action as "import" and rnn as True. The imported object nodes are returned as a list.

	For each imported object node, it checks if the node type is "mesh". If it is, it retrieves the parent node using the `selectionlib.get_parent()` function and checks if it contains the string "MH_model_GRP". If it does, it renames the parent node by replacing "MH_model_GRP" with an empty string. The renamed mesh node is then appended to the `mesh_nodes` list.

	Finally, the function returns the `mesh_nodes` list containing the imported mesh nodes.

	Note: This function assumes the availability of the `pathlib`, `os`, `cmds`, and `utilslib` libraries.
	"""

	folder = pathlib.normpath(os.path.join(get_mh_rigbuild_dir(), "metahuman", "sourceAssets"))
	mesh_nodes = []
	if not models:
		models = ['teeth_MH2SM', 'eyeRight_MH2SM', 'eyeLeft_MH2SM', 'head_MH2SM']
	if models:
		models = [model for model in models if models]

	for model in models:
		obj_dir = pathlib.normpath(os.path.join(folder, model + ".obj"))
		obj_nodes = utilslib.scene.load(obj_dir, action="import", rnn=True)
		for obj_node in obj_nodes:
			node_type = cmds.nodeType(obj_node)
			if node_type == "mesh":
				par = selectionlib.get_parent(obj_node, full_path=False)
				if "MH_model_GRP" in par:
					mesh_node = cmds.rename(par, par.replace("MH_model_GRP", ""))
					mesh_nodes.append(mesh_node)

	return (mesh_nodes)


def mh_snap_joints_to_closest(mesh="head_lod0_base", dmesh="head_MH2SM", joints=None):
	"""
	This function snaps a list of joints to the closest point on a mesh. It takes the following parameters:

	- mesh (string): The name of the source mesh.
	- dmesh (string): The name of the destination mesh.
	- joints (list): The list of joints to snap.

	If no joints are provided, the function returns the message "need some joints to snap".

	For each joint in the list, the function performs the following steps:
	1. Breaks connections for the translation and rotation attributes of the joint.
	2. Creates a matching locator for the joint.
	3. Creates a point constraint between the locator and the joint.
	4. Retrieves the position of the locator.
	5. Creates a 'closestPointOnMesh' node and connects it to the source mesh.
	6. Sets the closest point on the mesh based on the locator position.
	7. Retrieves the index of the closest vertex on the mesh.
	8. Creates matching locators for the source and destination meshes based on the vertex index.
	9. Parents the joint locator under the source locator.

	Note that the function does not return any values.
	"""
	if not joints:
		return ("need some joints to snap")

	for joint in joints:
		attributeslib.connection.break_connections(nodes=joint, attributes=["tx", "ty", "tz", "rx", "ry", "rz"])
		jloc = transformslib.xform.match_locator(source=joint, name=joint + "_jloc", node_type="locator")
		cons = cmds.pointConstraint(jloc, joint, mo=0)
		pp = cmds.pointPosition(jloc)
		closest_point_node = cmds.createNode('closestPointOnMesh')
		cmds.connectAttr(mesh + '.outMesh', closest_point_node + '.inMesh')
		cmds.setAttr(closest_point_node + '.inPosition', pp[0], pp[1], pp[2])
		vtx = cmds.getAttr(closest_point_node + ".closestVertexIndex")
		loc = transformslib.xform.match_locator(source=mesh + ".vtx[" + str(vtx) + "]", name=joint + "_sloc",
		                                        node_type="locator")
		sloc = joint + "_sloc"
		dloc = transformslib.xform.match_locator(source=dmesh + ".vtx[" + str(vtx) + "]", name=joint + "_dloc",
		                                         node_type="locator")
		dloc = joint + "_dloc"
		cmds.parent(jloc, sloc)


def mh_snap_all_joint_locs():
	"""
	This function is used to snap all joint locators to their corresponding destination and source locators. It also deletes the constraints and destination/source locators after snapping.

	Example usage:
	    mh_snap_all_joint_locs()

	"""
	jlocs = cmds.ls("*_jloc")
	for j in jlocs:
		dloc = j.replace("jloc", "dloc")
		sloc = j.replace("jloc", "sloc")
		cons1 = cmds.pointConstraint(dloc, sloc, mo=0)
	constraints = cmds.listRelatives("neck_01", ad=True, type="constraint")
	dlocs = cmds.ls("*_dloc")
	print(dlocs)
	slocs = cmds.ls("*_sloc")
	print(slocs)
	cmds.delete(constraints, dlocs, slocs)


def blendshape_extract_deltas(target_meshes=None, source_meshes=None):
	"""
	This function extracts blendshape deltas between target and source meshes.

	Parameters:
	- target_meshes (list): Optional. A list of target mesh names.
	- source_meshes (list): Optional. A list of source mesh names.

	Returns:
	None

	Note:
	- If target_meshes is not provided, the default target meshes will be used.
	- If source_meshes is not provided, the default source meshes will be used.

	Example:
	blendshape_extract_deltas(['head_lod0_mesh', 'teeth_lod0_mesh'], ['head_MH2SM', 'teeth_MH2SM'])
	"""

	targets = ['head_lod0_mesh', 'teeth_lod0_mesh', 'eyeLeft_lod0_mesh', 'eyeRight_lod0_mesh']
	sources = ['head_MH2SM', 'teeth_MH2SM', 'eyeLeft_MH2SM', 'eyeRight_MH2SM']

	target_meshes = target_meshes if target_meshes else targets
	source_meshes = source_meshes if source_meshes else sources

	for i, target in enumerate(target_meshes):
		dup = cmds.duplicate(target)[0]
		bs = cmds.blendShape(dup, source_meshes[i], target)
		cmds.setAttr(bs[0] + ".weight[0]", -1)
		cmds.setAttr(bs[0] + ".weight[1]", 1)
		cmds.delete(dup)
