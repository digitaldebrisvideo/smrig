"""
Imports the `contextlib` module, which provides utilities for working with context managers.
"""
import json
import os
import sys
from os import environ
from sys import path as syspath
from sys import platform

from smrig.build import mh
from smrig.lib import pathlib

# if you use Maya, use absolute path
ROOT_DIR = r"C:/Users/briol/Documents/maya/scripts/SMRIG_DEV/dna_calibration"
WORK_DIR = r"C:/Users/briol/Documents/maya/scripts/SMRIG_DEV/dna_calibration/work"

# work_dir  =  pathlib.normpath(os.path.join(mh.get_mh_path_dir(), ))
# WORK_DIR =  f"{work_dir}/work"

MAYA_VERSION = "2023"  # or 2023
ROOT_LIB_DIR = f"{ROOT_DIR}/lib/Maya{MAYA_VERSION}"
LIB_DIR = f"{ROOT_LIB_DIR}/windows"
DATA_DIR = f"{ROOT_DIR}/data"

# Add bin directory to maya plugin path
if "MAYA_PLUG_IN_PATH" in environ:
	separator = ":" if platform == "linux" else ";"
	environ["MAYA_PLUG_IN_PATH"] = separator.join([environ["MAYA_PLUG_IN_PATH"], LIB_DIR])
else:
	environ["MAYA_PLUG_IN_PATH"] = LIB_DIR

# Adds directories to path
paths = [ROOT_DIR, DATA_DIR, LIB_DIR]
for p in paths:
	if p not in sys.path:
		sys.path.insert(0, p)
	if p not in syspath:
		syspath.insert(0, ROOT_DIR)
		syspath.insert(0, DATA_DIR)
		syspath.insert(0, LIB_DIR)

# Imports
from maya import cmds, mel
import maya.OpenMaya as om
from dna_viewer import (DNA, Config, RigConfig, build_meshes, build_rig, get_skin_weights_from_scene,
                        set_skin_weights_to_scene)
from dnacalib import (CommandSequence, DNACalibDNAReader, SetVertexPositionsCommand, VectorOperation_Add,
                      SetNeutralJointTranslationsCommand,
                      SetNeutralJointRotationsCommand, RotateCommand)
from dna import (BinaryStreamReader, BinaryStreamWriter, DataLayer_All, FileStream, Status, )
from vtx_color import MESH_SHADER_MAPPING, VTX_COLOR_MESHES, VTX_COLOR_VALUES


# Methods
def read_dna(path):
	"""
	This function reads DNA data from a file.

	Parameters:
	    path (str): The path of the file to read.

	Returns:
	    BinaryStreamReader: A reader object that can be used to access the DNA data.

	Raises:
	    RuntimeError: If there is an error loading the DNA data.

	Example:
	    reader = read_dna("dna_file.bin")
	"""
	stream = FileStream(path, FileStream.AccessMode_Read, FileStream.OpenMode_Binary)
	reader = BinaryStreamReader(stream, DataLayer_All)
	reader.read()
	if not Status.isOk():
		status = Status.get()
		raise RuntimeError(f"Error loading DNA: {status.message}")
	return reader


def save_dna(reader, path):
	"""
	Save DNA to a file.

	:param reader: The DNA reader object.
	:param path: The file path to save the DNA.
	:raises RuntimeError: If there is an error saving the DNA.
	"""
	stream = FileStream(path, FileStream.AccessMode_Write, FileStream.OpenMode_Binary)
	writer = BinaryStreamWriter(stream)
	writer.setFrom(reader)
	writer.write()

	if not Status.isOk():
		status = Status.get()
		raise RuntimeError(f"Error saving DNA: {status.message}")

	print(f"DNA {path} successfully saved.")


def show_meshes(dna_path, add_skinning=False, add_blend_shapes=False):
	"""
	This code is a function that builds meshes in a 3D scene based on DNA data.

	Parameters:
	- dna_path: The path to the DNA file that contains the mesh data.
	- add_skinning (optional): A boolean flag indicating whether to add skinning information to the created meshes. Default is False.
	- add_blend_shapes (optional): A boolean flag indicating whether to add blend shapes to the created meshes. Default is False.

	Returns:
	- None

	Description:
	The function starts by clearing the current 3D scene using the 'cmds.file(force=True, new=True)' command. It then creates a DNA object based on the provided DNA file path.

	Next, a configuration object is created using the Config class, which sets various options for building the meshes. The available options are:

	- add_joints: A boolean flag indicating whether to add joints to the created meshes. Default is True.
	- add_blend_shapes: A boolean flag indicating whether to add blend shapes to the created meshes. Default is False.
	- add_skin_cluster: A boolean flag indicating whether to add skinning information to the created meshes. Default is False.
	- add_ctrl_attributes_on_root_joint: A boolean flag indicating whether to add control attributes on the root joint of the created meshes. Default is True.
	- add_animated_map_attributes_on_root_joint: A boolean flag indicating whether to add animated map attributes on the root joint of the created meshes. Default is True.
	- add_mesh_name_to_blend_shape_channel_name: A boolean flag indicating whether to add the mesh name to the blend shape channel name. Default is True.
	- add_key_frames: A boolean flag indicating whether to add key frames to the created meshes. Default is True.

	Finally, the 'build_meshes' function is called with the DNA object and the configuration object as arguments to build the meshes in the 3D scene.

	Note:
	This documentation follows the plain format for Python docstrings and does not include example code, author information, version information, or usage examples. It also does not document type member properties and does not use HTML tags.
	"""
	cmds.file(force=True, new=True)

	dna = DNA(dna_path)

	# Builds and returns the created mesh paths in the scene
	config = Config(
		add_joints=True,
		add_blend_shapes=add_blend_shapes,
		add_skin_cluster=add_skinning,
		add_ctrl_attributes_on_root_joint=True,
		add_animated_map_attributes_on_root_joint=True,
		add_mesh_name_to_blend_shape_channel_name=True,
		add_key_frames=True
	)

	# Build meshes
	build_meshes(dna, config)


def assemble_scene(dna_path, analog_gui_path, gui_path, additional_assemble_script):
	"""
	This function is used to assemble a scene with a rig based on specific DNA, GUI, and additional script inputs.

	Parameters:
	- dna_path: A string representing the file path to the DNA file.
	- analog_gui_path: A string representing the file path to the analog GUI file.
	- gui_path: A string representing the file path to the GUI file.
	- additional_assemble_script: A string representing the file path to an additional assemble script.

	Returns:
	None

	Note:
	- This function uses the DNA, GUI, and additional script inputs to create a RigConfig object.
	- The function then calls the build_rig function passing the DNA and RigConfig objects as arguments.
	- After the rig is built, the function retrieves the translation values of the "neck_01" joint and uses them to move the "CTRL_faceGUI" object by adding 20 units to the X-axis and 5 units to the Y-axis.

	Example usage:
	assemble_scene("path/to/dna", "path/to/analog_gui", "path/to/gui", "path/to/additional_script")
	"""
	dna = DNA(dna_path)
	config = RigConfig(
		gui_path=gui_path,
		analog_gui_path=analog_gui_path,
		aas_path=additional_assemble_script,
		add_animated_map_attributes_on_root_joint=True,
		add_key_frames=True,
		add_mesh_name_to_blend_shape_channel_name=True
	)

	# Creates the rig
	build_rig(dna=dna, config=config)
	translation = cmds.xform("neck_01", ws=True, query=True, translation=True)
	cmds.xform("CTRL_faceGUI", ws=True, t=[translation[0] + 20, translation[1] + 5, translation[2]])


def get_mesh_vertex_positions_from_scene(meshName):
	"""
	This function takes a string parameter `meshName` as input and returns a list of vertex positions of a specified mesh in a 3D scene.

	Parameters:
	- `meshName` (str): The name of the mesh to retrieve vertex positions from.

	Returns:
	- List[List[float]]: A list of vertex positions represented as lists of three floats [x, y, z].

	Exceptions:
	- RuntimeError: If the specified mesh is missing in the scene, a warning message is printed and None is returned.

	Example usage:

	```
	positions = get_mesh_vertex_positions_from_scene("myMesh")
	if positions is not None:
	    for vertex in positions:
	        print(vertex)
	```
	"""
	try:
		sel = om.MSelectionList()
		sel.add(meshName)

		dag_path = om.MDagPath()
		sel.getDagPath(0, dag_path)

		mf_mesh = om.MFnMesh(dag_path)
		positions = om.MPointArray()

		mf_mesh.getPoints(positions, om.MSpace.kObject)
		return [
			[positions[i].x, positions[i].y, positions[i].z]
			for i in range(positions.length())
		]
	except RuntimeError:
		print(f"{meshName} is missing, skipping it")
		return None


def run_joints_command(reader, calibrated):
	"""
	This function runs joints command to set the neutral translations and rotations of all joints in the reader.

	Parameters:
	- reader: The reader object that provides joint information.
	- calibrated: A boolean value indicating whether the joints should be calibrated.

	Returns:
	- None

	Steps:
	1. Create empty lists to store joint translations and rotations.
	2. Iterate through all the joints in the reader.
	3. Get the name of the current joint.
	4. Retrieve the translation and rotation values of the joint using Maya's xform and joint commands.
	5. Create instances of SetNeutralJointTranslationsCommand and SetNeutralJointRotationsCommand with the collected translation and rotation values respectively.
	6. Create an instance of CommandSequence to collect all commands into a sequence.
	7. Add the set_new_joints_translations and set_new_joints_rotations commands to the sequence.
	8. Run the sequence of commands with the calibrated parameter.
	9. Check if there were any errors during the command execution.
	10. If error occurred, raise a RuntimeError with the error message.
	"""
	# Making arrays for joints' transformations and their corresponding mapping arrays
	joint_translations = []
	joint_rotations = []

	for i in range(reader.getJointCount()):
		joint_name = reader.getJointName(i)

		translation = cmds.xform(joint_name, query=True, translation=True)
		joint_translations.append(translation)

		rotation = cmds.joint(joint_name, query=True, orientation=True)
		joint_rotations.append(rotation)

	# This is step 5 sub-step a
	set_new_joints_translations = SetNeutralJointTranslationsCommand(joint_translations)
	# This is step 5 sub-step b
	set_new_joints_rotations = SetNeutralJointRotationsCommand(joint_rotations)

	# Abstraction to collect all commands into a sequence, and run them with only one invocation
	commands = CommandSequence()
	# Add vertex position deltas (NOT ABSOLUTE VALUES) onto existing vertex positions
	commands.add(set_new_joints_translations)
	commands.add(set_new_joints_rotations)

	commands.run(calibrated)
	# Verify that everything went fine
	if not Status.isOk():
		status = Status.get()
		raise RuntimeError(f"Error run_joints_command: {status.message}")


def run_vertices_command(calibrated, old_vertices_positions, new_vertices_positions, mesh_index):
	"""
	This function takes in several parameters and performs the following steps:

	1. Calculate the deltas between the old vertex positions and the new vertex positions.
	2. Create a new command to set the vertex positions based on the deltas.
	3. Create a sequence of commands.
	4. Add the new command to the sequence.
	5. Run the sequence of commands with the `calibrated` parameter.
	6. Verify if the status of the operations is OK. If not, raise an error.

	Parameters:
	- calibrated: A boolean value indicating whether the vertices are calibrated.
	- old_vertices_positions: A list of old vertex positions.
	- new_vertices_positions: A list of new vertex positions.
	- mesh_index: The index of the mesh.

	Raises:
	- RuntimeError: If there is an error during the execution of the commands.

	Note:
	- The function assumes that the `SetVertexPositionsCommand` and `CommandSequence` classes are defined elsewhere.

	Example Usage:
	calibrated = True
	old_vertices_positions = [[1, 2, 3], [4, 5, 6]]
	new_vertices_positions = [[2, 3, 4], [5, 6, 7]]
	mesh_index = 0

	run_vertices_command(calibrated, old_vertices_positions, new_vertices_positions, mesh_index)

	"""
	# Making deltas between old vertices positions and new one
	deltas = []
	for new_vertex, old_vertex in zip(new_vertices_positions, old_vertices_positions):
		delta = []
		for new, old in zip(new_vertex, old_vertex):
			delta.append(new - old)
		deltas.append(delta)

	# This is step 5 sub-step c
	new_neutral_mesh = SetVertexPositionsCommand(
		mesh_index, deltas, VectorOperation_Add
	)
	commands = CommandSequence()
	# Add nex vertex position deltas (NOT ABSOLUTE VALUES) onto existing vertex positions
	commands.add(new_neutral_mesh)
	commands.run(calibrated)

	# Verify that everything went fine
	if not Status.isOk():
		status = Status.get()
		raise RuntimeError(f"Error run_vertices_command: {status.message}")


def prepare_rotated_dna(dna_path, rotated_dna_path):
	"""
	This function prepares a rotated version of a DNA sequence file.

	:param dna_path: The file path of the original DNA sequence.
	:param rotated_dna_path: The file path where the rotated DNA sequence will be saved.

	:returns: The rotated DNA sequence as a DNA object.

	This function takes in the file path of a DNA sequence and prepares a rotated version of it. It first reads the DNA contents from the original file using the `read_dna` function. Then, it creates a `DNACalibDNAReader` object `calibrated` that serves as an input/output parameter to the commands. Next, it applies a rotation transformation to the `calibrated` DNA object using the `RotateCommand` with the specified angles. The rotation modifies the `calibrated` DNA object in-place. After the rotation is applied, the rotated DNA object is saved to the specified `rotated_dna_path` using the `save_dna` function. Finally, the rotated DNA sequence is returned as a `DNA` object.

	Note that this function assumes the presence of the `read_dna`, `save_dna`, and `DNA` classes/functions, which are not shown here.
	"""
	reader = read_dna(dna_path)

	# Copies DNA contents and will serve as input/output parameter to commands
	calibrated = DNACalibDNAReader(reader)

	# Modifies calibrated DNA in-place
	rotate = RotateCommand([90.0, 0.0, 0.0], [0.0, 0.0, 0.0])
	rotate.run(calibrated)

	save_dna(calibrated, rotated_dna_path)
	return DNA(rotated_dna_path)


def get_dna(dna_path, rotated_dna_path):
	"""
	This module contains a function `get_dna` that retrieves DNA data from a given path.

	# Function: get_dna
	        def get_dna(dna_path, rotated_dna_path):

	This function takes two arguments:
	- `dna_path`: A string representing the path to the DNA file.
	- `rotated_dna_path`: A string representing the path to the rotated DNA file.

	The function checks if the up axis is set to "z". If it is, the function calls the `prepare_rotated_dna` function to prepare the rotated DNA data, using the `dna_path` and `rotated_dna_path` arguments. Otherwise, it creates a new instance of the `DNA` class using only the `dna_path` argument.

	The function does not return any value.

	Note: The code snippet provided is incomplete, as it does not include the implementation of the `prepare_rotated_dna` function and the `DNA` class. Please make sure to provide the complete code for the module if you require more detailed documentation.
	"""
	if up_axis == "z":
		return prepare_rotated_dna(dna_path, rotated_dna_path)
	return DNA(dna_path)


def build_meshes_for_lod(dna, lod):
	"""
	This function is used to build meshes for a given level of detail (LOD). It takes in a DNA object and the desired LOD as parameters and returns the created mesh paths in the scene.

	Parameters:
	- "dna": A DNA object used to build the meshes.
	- "lod": The desired level of detail for the meshes.

	Returns:
	- A list of paths of the created meshes in the scene.

	Example usage:

	dna = create_dna()  # Create a DNA object
	lod = 2  # LOD level 2

	mesh_paths = build_meshes_for_lod(dna, lod)  # Build meshes for the given LOD

	for path in mesh_paths:
	    print(path)  # Print the path of each created mesh
	"""
	# Create config
	config = Config(
		group_by_lod=False,
		create_display_layers=False,
		lod_filter=[lod],
		add_mesh_name_to_blend_shape_channel_name=True,
	)

	# Builds and returns the created mesh paths in the scene
	return build_meshes(dna, config)


def create_skin_cluster(influences, mesh, skin_cluster_name, maximum_influences):
	"""
	This function creates a skin cluster in Maya.

	Parameters:
	- influences (list of str): A list of bone influences for the skin cluster.
	- mesh (str): The name of the mesh to be skinned.
	- skin_cluster_name (str): The desired name of the new skin cluster.
	- maximum_influences (int): The maximum number of influences allowed per vertex in the skin cluster.

	Returns:
	- skinCluster (str): The name of the created skin cluster.

	Example usage:
	influences = ['joint1', 'joint2', 'joint3']
	mesh = 'pSphere1'
	skin_cluster_name = 'skinCluster1'
	maximum_influences = 3

	skinCluster = create_skin_cluster(influences, mesh, skin_cluster_name, maximum_influences)
	"""
	cmds.select(influences[0], replace=True)
	cmds.select(mesh, add=True)
	skinCluster = cmds.skinCluster(
		toSelectedBones=True,
		name=skin_cluster_name,
		maximumInfluences=maximum_influences,
		skinMethod=0,
		obeyMaxInfluences=True,
	)
	if len(influences) > 1:
		cmds.skinCluster(
			skinCluster, edit=True, addInfluence=influences[1:], weight=0.0
		)
	return skinCluster


def create_head_and_body_scene(mesh_names, body_file, neck_joints, root_joint, facial_root_joints):
	"""
	This function is used to create a new scene by importing a body file and applying skin weights to the corresponding meshes.

	Parameters:
	- mesh_names: a list of names of the meshes to be imported into the scene
	- body_file: the file path of the body file to be imported
	- neck_joints: a list of names of the neck joints for each facial root joint
	- root_joint: the name of the root joint in the body file
	- facial_root_joints: a list of names of the facial root joints

	Returns:
	- None

	Note:
	- This function imports the body file and deletes any existing skin clusters on the meshes.
	- It then sets the orientation of the root joint based on the specified up axis.
	- It re-parents the facial root joints under the corresponding neck joints.
	- Finally, it creates new skin clusters on the meshes and sets the skin weights.

	Example usage:
	mesh_names = ['head', 'body']
	body_file = 'path/to/body/file.obj'
	neck_joints = ['neck_01', 'neck_02']
	root_joint = 'root'
	facial_root_joints = ['facial_01', 'facial_02']

	create_head_and_body_scene(mesh_names, body_file, neck_joints, root_joint, facial_root_joints)
	"""
	scene_mesh_names = []
	skinweights = []

	for mesh_name in mesh_names:
		if cmds.objExists(mesh_name):
			scene_mesh_names.append(mesh_name)
			skinweights.append(get_skin_weights_from_scene(mesh_name))
			cmds.delete(f"{mesh_name}_skinCluster")

	for facial_joint in facial_root_joints:
		cmds.parent(facial_joint, world=True)
	cmds.delete(root_joint)

	cmds.file(body_file, options="v=0", type="mayaAscii", i=True)
	if up_axis == "y":
		cmds.joint("root", edit=True, orientation=[-90.0, 0.0, 0.0])
	for facial_joint, neck_joint in zip(facial_root_joints, neck_joints):
		cmds.parent(facial_joint, neck_joint)

	for mesh_name, skinweight in zip(scene_mesh_names, skinweights):
		create_skin_cluster(
			skinweight.joints,
			mesh_name,
			f"{mesh_name}_skinCluster",
			skinweight.no_of_influences,
		)
		set_skin_weights_to_scene(mesh_name, skinweight)


def set_fbx_options(orientation):
	"""
	This function, set_fbx_options, executes several FBX-related commands from the imported plugin in Maya. It sets various options for the FBX export process.

	Parameters:
	- orientation: The desired up axis for the FBX export. This can be one of the following values: "y", "Y", "z", "Z" (default is "y").

	Behaviour:
	- Retrieves the minimum and maximum time values from the playback options in Maya.
	- Resets the FBX export settings to default.
	- Bakes complex animations, starting from the minimum time to the maximum time.
	- Enables exporting constraints, skeleton definitions, input connections, smoothing groups, skins, and shapes.
	- Disables exporting cameras and lights.
	- Sets the up axis for the FBX export using the provided orientation value.
	- Deselects all objects in Maya.

	Note:
	- This function requires the FBX plugin to be imported in Maya.

	Example Usage:
	set_fbx_options("y")
	"""
	# Executes FBX relate commands from the imported plugin
	min_time = cmds.playbackOptions(minTime=True, query=True)
	max_time = cmds.playbackOptions(maxTime=True, query=True)

	cmds.FBXResetExport()
	mel.eval("FBXExportBakeComplexAnimation -v true")
	mel.eval(f"FBXExportBakeComplexStart -v {min_time}")
	mel.eval(f"FBXExportBakeComplexEnd -v {max_time}")
	mel.eval("FBXExportConstraints -v true")
	mel.eval("FBXExportSkeletonDefinitions -v true")
	mel.eval("FBXExportInputConnections -v true")
	mel.eval("FBXExportSmoothingGroups -v true")
	mel.eval("FBXExportSkins -v true")
	mel.eval("FBXExportShapes -v true")
	mel.eval("FBXExportCameras -v false")
	mel.eval("FBXExportLights -v false")
	cmds.FBXExportUpAxis(orientation)
	# Deselects objects in Maya
	cmds.select(clear=True)


def create_shader(name):
	"""
	This function creates a shader and a shading group in Autodesk Maya.

	:param name: The name of the shader and shading group.
	:type name: str
	:return: The name of the created shading group.
	:rtype: str
	"""
	cmds.shadingNode("blinn", asShader=True, name=name)

	shading_group = str(
		cmds.sets(
			renderable=True,
			noSurfaceShader=True,
			empty=True,
			name=f"{name}SG",
		)
	)
	cmds.connectAttr(f"{name}.outColor", f"{shading_group}.surfaceShader")
	return shading_group


def add_shader(lod):
	"""
	This function adds shaders to meshes based on a given level of detail (LOD).

	Parameters:
	- lod: An integer representing the level of detail to add the shader for.

	Returns:
	None

	Raises:
	None

	Example usage:
	add_shader(2)
	"""
	for shader_name, meshes in MESH_SHADER_MAPPING.items():
		shading_group = create_shader(shader_name)
		for mesh in meshes:
			if f"lod{lod}" in mesh:
				try:
					cmds.select(mesh, replace=True)
					cmds.sets(edit=True, forceElement=shading_group)
				except Exception as e:
					print(f"Skipped adding shader for mesh {mesh}. Reason {e}")


def set_vertex_color(lod):
	"""
	This function is used to set the vertex color of specified meshes.

	Parameters:
	    - lod (int): The level of detail for the meshes.

	This function iterates over the list of mesh names and checks if the mesh name contains the string "lod{lod}". If it does, the function selects the mesh and iterates over the corresponding vertex color values. It then applies the vertex color to each vertex of the mesh.

	If any exception occurs during the process, the function prints an error message and continues to the next mesh.

	Note: This function assumes that the `cmds` module is available and imported.

	Example:

	    # Set vertex colors for LOD 1 meshes
	    set_vertex_color(1)

	    # Set vertex colors for LOD 2 meshes
	    set_vertex_color(2)
	"""
	for m, mesh_name in enumerate(VTX_COLOR_MESHES):
		try:
			if f"lod{lod}" in mesh_name:
				cmds.select(mesh_name)
				for v, rgb in enumerate(VTX_COLOR_VALUES[m]):
					cmds.polyColorPerVertex(f"{mesh_name}.vtx[{v}]", g=rgb[1], b=rgb[2])
		except Exception as e:
			print(f"Skipped adding vtx color for mesh {mesh_name}. Reason {e}")
			continue


def export_fbx(lod_num, meshes, root_jnt, chr_name, fbx_dir):
	"""
	Exports the given LOD meshes and facial root joint as an FBX file.

	Parameters:
	- lod_num (int): The LOD number of the character.
	- meshes (list): A list of meshes to be included in the FBX export.
	- root_jnt (str): The name of the facial root joint to be included in the FBX export.
	- chr_name (str): The name of the character.
	- fbx_dir (str): The directory where the FBX file will be exported to.

	Returns:
	None

	"""
	# Selects every mesh in the given lod
	for item in meshes:
		cmds.select(item, add=True)
	# Adds facial root joint to selection
	cmds.select(root_jnt, add=True)
	# Sets the file path
	export_file_name = f"{fbx_dir}/{chr_name}_lod{lod_num}.fbx"
	# Exports the fbx
	mel.eval(f'FBXExport -f "{export_file_name}" -s true')


def export_fbx_for_lod(dna, lod, add_vtx_color, chr_name, body_file, fbx_dir, neck_joints, root_joint, fbx_root_jnt,
                       facial_root_joints, orientation):
	"""
	This function exports a FBX file for a specific level of detail (LOD) for a character model.

	Parameters:
	- dna: The DNA (genetic code) of the character.
	- lod: The level of detail for which to export the FBX file.
	- add_vtx_color: Indicates whether to add vertex color to the exported FBX file.
	- chr_name: The name of the character.
	- body_file: The file containing the character's body information.
	- fbx_dir: The directory where the FBX file will be saved.
	- neck_joints: The joints in the character's neck.
	- root_joint: The root joint of the character.
	- fbx_root_jnt: The root joint of the exported FBX file.
	- facial_root_joints: The root joints of the character's facial features.
	- orientation: The orientation of the character in the exported FBX file.

	Returns:
	None.

	This function first builds the meshes for the specified LOD using the given DNA. It then creates a scene for the character's head and body using the mesh data and other parameters. Various FBX-related commands are executed using an imported plugin. The FBX options, such as the orientation, are set. Finally, the resulting FBX file is exported.

	Note: This function assumes the existence of certain helper functions like 'build_meshes_for_lod', 'create_head_and_body_scene', 'set_fbx_options', 'add_shader', 'set_vertex_color', and 'export_fbx', which are not shown in this code snippet.
	"""
	# Creates the meshes for the given lod
	result = build_meshes_for_lod(dna, lod)
	meshes = result.get_all_meshes()
	# Executes FBX relate commands from the imported plugin
	create_head_and_body_scene(meshes, body_file, neck_joints, root_joint, facial_root_joints)
	set_fbx_options(orientation)
	# Saves the result
	if add_vtx_color:
		add_shader(lod)
		set_vertex_color(lod)
	export_fbx(lod, meshes, fbx_root_jnt, chr_name, fbx_dir)


def transfer_joints_positions_distance(a, b):
	"""
	This function calculates the squared distance between two sets of joint positions.

	Parameters:
	- a (list): The first set of joint positions as a list of three floating-point numbers representing x, y, and z coordinates.
	- b (list): The second set of joint positions as a list of three floating-point numbers representing x, y, and z coordinates.

	Returns:
	- distance (float): The squared Euclidean distance between the two sets of joint positions.

	Example:
	a = [1.0, 2.0, 3.0]
	b = [4.0, 5.0, 6.0]
	distance = transfer_joints_positions_distance(a, b)
	print(distance)  # Output: 27.0
	"""
	return pow((a[0] - b[0]), 2) + pow((a[1] - b[1]), 2) + pow((a[2] - b[2]), 2)


def find_and_save_joint_positions_in_file(reader, joints, file_path):
	"""
	This function finds and saves the joint positions in a file. It takes three parameters:
	- reader: The reader object used to read the mesh.
	- joints: A list of joint names whose positions are to be found and saved.
	- file_path: The path of the file where the joint positions will be saved.

	The function performs the following steps:
	1. Gets the name of the mesh from the reader object.
	2. Initializes an empty dictionary to store the joint positions.
	3. For each joint in the joints list:
	    - Selects the joint in the scene using Maya's `cmds.select` command.
	    - Retrieves the world-space position of the joint using Maya's `cmds.xform` command.
	    - Finds the nearest point on the mesh surface to the joint position using Maya's `mel.eval` function.
	    - Sets the x, y, and z position attributes of the nearest point using Maya's `cmds.setAttr` command.
	    - Gets the index of the face closest to the nearest point using Maya's `cmds.getAttr` command.
	    - Retrieves the vertex information of the closest face using Maya's `cmds.polyInfo` command.
	    - Finds the closest vertex to the joint position from the vertex information.
	    - Calculates the distance between the joint position and the selected vertex using the `transfer_joints_positions_distance` function.
	    - Updates the closest vertex and distance if a closer vertex is found.
	    - Stores the index of the closest vertex in the output dictionary with the joint name as the key.
	4. Opens the file specified by the `file_path` parameter in write mode.
	5. Writes the output dictionary to the file in JSON format using the `json.dump` function.

	Note: The `transfer_joints_positions_distance` function used in the code is not defined here and should be implemented separately.
	"""
	mesh = reader.getMeshName(0)
	output = {}
	for joint_name in joints:
		cmds.select(joint_name)

		joint_pos = cmds.xform(joint_name, q=True, ws=True, translation=True)
		near_point = mel.eval(f"nearestPointOnMesh {mesh}")
		cmds.setAttr(f"{near_point}.inPositionX", joint_pos[0])
		cmds.setAttr(f"{near_point}.inPositionY", joint_pos[1])
		cmds.setAttr(f"{near_point}.inPositionZ", joint_pos[2])
		best_face = cmds.getAttr(f"{near_point}.nearestFaceIndex")

		face_vtx_str = cmds.polyInfo(f"{mesh}.f[{best_face}]", fv=True)
		buffer = face_vtx_str[0].split()
		closest_vtx = 0
		dist = 10000
		for v in range(2, len(buffer)):
			vtx = buffer[v]
			vtx_pos = cmds.xform(f"{mesh}.vtx[{vtx}]", q=True, ws=True, translation=True)
			new_dist = transfer_joints_positions_distance(joint_pos, vtx_pos)
			if new_dist < dist:
				dist = new_dist
				closest_vtx = vtx
		output[joint_name] = closest_vtx

	with open(file_path, 'w') as out_file:
		json.dump(output, out_file, indent=4)


########################################################################################################################
########################################################################################################################
# output_dir = pathlib.normpath(os.path.join(mh.get_mh_path_dir(), "final.dna"))
# temp_dir = pathlib.normpath(os.path.join(mh.get_mh_path_dir(), "temp"))
output_dir = (f"/{WORK_DIR}/output")
temp_dir = (f"/{WORK_DIR}/temp")
base_dir = f"{DATA_DIR}/head_base.mb"
joint_position_file = f"{temp_dir}/joint_position.json"
character_dna = f"{DATA_DIR}/mh4/dna_files/BaseMH.dna"
mesh_dna = f"{WORK_DIR}/dna/BaseMH_mesh.dna"
jnt_dna = f"{WORK_DIR}/dna/BaseMH_jnt.dna"
# final_dna = pathlib.normpath(os.path.join(mh.get_mh_path_dir(), "Rig", "MH_Rig", "final_dna.dna"))
final_dna = f"{WORK_DIR}/output/final.dna"
rotated_dna = f"{WORK_DIR}/dna/BaseMH_final.rotated.dna"
body_file = f"{WORK_DIR}/model/BaseMH_skel.ma"
# review_scene = pathlib.normpath(os.path.join(mh.get_mh_path_dir(), "Rig", "MH_Rig", "review_dna.dna"))
review_scene = f"{WORK_DIR}/output/review.mb"
gui_path = f"{DATA_DIR}/gui.ma"
analog_gui_path = f"{DATA_DIR}/analog_gui.ma"
aas_path = f"{DATA_DIR}/additional_assemble_script.py"
up_axis = "y"
head_mesh = "head_lod0_mesh"
facial_root_joints = ["FACIAL_C_FacialRoot", "FACIAL_C_Neck1Root", "FACIAL_C_Neck2Root"]
neck_joints = ["head", "neck_01", "neck_02"]
root_joint = "spine_04"
add_vtx_color = True
fbx_root = "root"
character_name = "BaseMH"


########################################################################################################################
########################################################################################################################
# This is step 1.
##################################
def step_one():
	"""
	This code performs various functions related to loading plugins, creating folders, and executing a series of steps for processing DNA data.

	Step One:

	This step loads a plugin called "nearestPointOnMesh.mll" if it is not already loaded using the `cmds.pluginInfo` and `cmds.loadPlugin` functions.

	Creating Folders:

	This code checks if the specified folders `WORK_DIR`, `output_dir`, and `temp_dir` already exist using the `os.path.exists` function. If any of the folders do not exist, it creates them using the `os.makedirs` function.

	Steps:

	The code calls the `show_meshes` function with the argument `character_dna`, which is responsible for displaying meshes related to the DNA data.

	Next, it calls the `read_dna` function with the argument `character_dna` to read the DNA data.

	After that, it instantiates a `DNACalibDNAReader` object called `calibrated` by passing the `reader` variable as a parameter.

	Finally, it prints the message "STEP ONE DONE" to the console.

	Please note that this code does not return any values or have any visible output besides the printed message.
	"""
	if not cmds.pluginInfo("nearestPointOnMesh.mll", q=True, l=True):
		cmds.loadPlugin("nearestPointOnMesh.mll")

	# Create folders
	if not os.path.exists(WORK_DIR):
		os.makedirs(WORK_DIR)
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	if not os.path.exists(temp_dir):
		os.makedirs(temp_dir)

	# Steps
	show_meshes(character_dna)
	reader = read_dna(character_dna)
	calibrated = DNACalibDNAReader(reader)
	print("STEP ONE DONE")


##################################
# This is step 2
##################################
def step_two():
	"""
	This code snippet is a part of a larger script that involves reading DNA data and calibrating a DNA reader. The mainbuild purpose of this specific code block is to perform the following steps:

	1. Read DNA data:
	   - The function `read_dna(character_dna)` is called to read the DNA data stored in the variable `character_dna`.
	   - The returned DNA data is assigned to the variable `reader`.

	2. Calibrate DNA reader:
	   - The class `DNACalibDNAReader` is instantiated with the `reader` object as its argument.
	   - The calibrated DNA reader object is assigned to the variable `calibrated`.

	3. Import 3D model:
	   - The file path for the 3D model, stored in the variable `model`, is created using the `os.path.join()` and `pathlib.normpath()` functions.
	   - The 3D model file is imported into the current scene using the `cmds.file()` function with the `i=True` (import) flag and `mergeNamespacesOnClash=True` option.
	   - The imported 3D model is merged into the current namespace using `namespace=":"`.

	4. Find and save joint positions:
	   - The function `listRelatives()` from the `cmds` module is called to retrieve all child joints of the joint "neck_01" in the current scene.
	   - The joint positions are found and saved in a file using the `find_and_save_joint_positions_in_file()` function, which takes the `reader` object, list of joints (`jnts`), and a file name as arguments.

	Note: The code assumes that the required modules (`pathlib` and `os`) and the `mh` module (for `get_mh_rigbuild_dir()` function) are imported and available in the script.

	It is important to note that this code appears to be a part of a larger script, and its correct execution depends on the proper implementation of the other parts of the script.
	"""
	reader = read_dna(character_dna)
	calibrated = DNACalibDNAReader(reader)
	model = pathlib.normpath(os.path.join(mh.get_mh_rigbuild_dir(), "metahuman", "sourceAssets", "mh_2_sm_model.mb"))
	cmds.file(model, i=True, mergeNamespacesOnClash=True, namespace=":")
	jnts = cmds.listRelatives("neck_01", ad=True, type="joint")
	find_and_save_joint_positions_in_file(reader, jnts, joint_position_file)


##################################
# This is step 3
##################################
def step_three():
	"""
	This code snippet is a part of a software development project and is responsible for performing certain operations on DNA data. Here's a brief explanation of the code:

	Function: step_three()
	- This function is used to perform a series of operations on DNA data.
	- It takes no input parameters.
	- It does not return any value.

	Variable: reader
	- This variable is used to store the result of the function read_dna(character_dna).

	Variable: calibrated
	- This variable is used to store the result of creating a DNACalibDNAReader object with the 'reader' as its argument.

	Variable: lod_mesh
	- This variable is used to store the name of a LOD mesh.

	Variable: sm_mesh
	- This variable is used to store the name of a SM mesh.

	Function: run_vertices_command()
	- This function is used to run a command on the vertices of two meshes.
	- It takes four input parameters:
	    - calibrated: The calibrated DNA reader object.
	    - get_mesh_vertex_positions_from_scene(lod_mesh): The vertex positions of the LOD mesh obtained from the scene.
	    - get_mesh_vertex_positions_from_scene(sm_mesh): The vertex positions of the SM mesh obtained from the scene.
	    - An integer representing the command type.

	Commands:
	- Four run_vertices_command() functions are called with different LOD and SM mesh names and command types.
	- These commands perform operations on DNA data.

	Function: save_dna()
	- This function is used to save the calibrated DNA data to the 'mesh_dna' variable.

	Note: This documentation assumes that there are other functions and variables defined elsewhere in the code, but they are not included in the given snippet.
	"""
	reader = read_dna(character_dna)
	calibrated = DNACalibDNAReader(reader)

	lod_mesh = "head_lod0_mesh"
	sm_mesh = "head_MH2SM"
	run_vertices_command(
		calibrated, get_mesh_vertex_positions_from_scene(lod_mesh),
		get_mesh_vertex_positions_from_scene(sm_mesh), 0
	)

	lod_mesh = "teeth_lod0_mesh"
	sm_mesh = "teeth_MH2SM"
	run_vertices_command(
		calibrated, get_mesh_vertex_positions_from_scene(lod_mesh),
		get_mesh_vertex_positions_from_scene(sm_mesh), 1
	)

	lod_mesh = "eyeLeft_lod0_mesh"
	sm_mesh = "eyeLeft_MH2SM"
	run_vertices_command(
		calibrated, get_mesh_vertex_positions_from_scene(lod_mesh),
		get_mesh_vertex_positions_from_scene(sm_mesh), 3
	)

	lod_mesh = "eyeRight_lod0_mesh"
	sm_mesh = "eyeRight_MH2SM"
	run_vertices_command(
		calibrated, get_mesh_vertex_positions_from_scene(lod_mesh),
		get_mesh_vertex_positions_from_scene(sm_mesh), 4
	)

	save_dna(calibrated, mesh_dna)


##################################
# This is step 4
##################################

def step_four():
	"""
	This code snippet is a part of a software that performs certain operations on 3D meshes and joints in Autodesk Maya.

	The mainbuild purpose of this code is to snap joints to the closest areas on the corresponding mesh objects.

	The code can be broken down into the following steps:

	1. Import necessary modules:

	    - The `mh` module might be a custom module or an external library for working with meshes and joints in Autodesk Maya.
	    - The `cmds` module is a standard module in Autodesk Maya that provides functions for interacting with the Maya API.

	2. Define a function named `step_four()`:

	    - This function does not take any parameters.
	    - It calls the `build_meshes()` function, passing the `mesh_dna` variable as an argument.
	    - It assigns the result of the `read_dna()` function, with `mesh_dna` as an argument, to the `reader` variable.
	    - It creates a new instance of the `DNACalibDNAReader` class, passing the `reader` variable as an argument, and assigns it to the `calibrated` variable.
	    - It imports a 3D model file specified by the `base` variable into the Maya scene, using the `file()` function. The `i` parameter indicates import, and the `mergeNamespacesOnClash` and `namespace` parameters handle namespace conflicts.

	3. Define two lists, `leye_jnts` and `reye_jnts`, which contain names of joint objects.

	4. Combine the two lists `leye_jnts` and `reye_jnts` to create a new list `eye_jnts`.

	5. Use the `listRelatives()` function from the `cmds` module to find the children joints of the "neck_01" joint and assign them to the `offset_jnts` variable.

	6. Create a list named `parents` with the names "neck_01", "neck_02", and "head".

	7. Create an empty list named `eye_head_jnts`.

	8. Iterate over the elements in `eye_jnts`:

	    - If the current element is also in `offset_jnts`, remove it from `offset_jnts` and proceed.
	    - Use the `listRelatives()` function to find any joint objects further up the hierarchy from the current element.
	    - Remove the current element and any joint objects found in the previous step from `offset_jnts`.
	    - Add the joint objects found in the previous step to the `eye_head_jnts` list.

	9. Iterate over the elements in `parents`:

	    - If the current element is in `offset_jnts`, remove it from `offset_jnts`.

	10. Select the joints in `offset_jnts` using the `select()` function.

	11. Call the `mh_snap_joints_to_closest()` function from the `mh` module:

	    - Pass the mesh object named "eyeLeft_base", the corresponding detailed mesh object named "eyeLeft_lod0_mesh", and the `leye_jnts` list as arguments.
	    - This function likely snaps the `leye_jnts` joints to the closest areas on the "eyeLeft_base" mesh.

	12. Call the `mh_snap_joints_to_closest()` function again:

	    - Pass the mesh object named "eyeRight_base", the corresponding detailed mesh object named "eyeRight_lod0_mesh", and the `reye_jnts` list as arguments.
	    - This function likely snaps the `reye_jnts` joints to the closest areas on the "eyeRight_base" mesh.

	13. Call the `mh_snap_joints_to_closest()` function again:

	    - Pass the mesh object named "head_base", the corresponding detailed mesh object named "head_lod0_mesh", and the `offset_jnts` list as arguments.
	    - This function likely snaps the `offset_jnts` joints to the closest areas on the "head_base" mesh.

	14. Call the `mh_snap_all_joint_locs()` function from the `mh` module.

	15. Call the `save_dna()` function, passing the `calibrated` and `jnt_dna` as arguments. The purpose and implementation of this function are not clear from the given code snippet.

	Please note that this documentation is based on the code provided and may not encompass the entire functionality of the software.
	"""
	build_meshes(mesh_dna)
	reader = read_dna(mesh_dna)
	calibrated = DNACalibDNAReader(reader)
	cmds.file(base, i=True, mergeNamespacesOnClash=True, namespace=":")

	# snap joints
	leye_jnts = ['FACIAL_L_EyelidUpperB', 'FACIAL_L_EyelidUpperA', 'FACIAL_L_Eye', 'FACIAL_L_EyelidLowerA',
	             'FACIAL_L_EyelidLowerB']
	reye_jnts = ['FACIAL_R_EyelidUpperB', 'FACIAL_R_EyelidUpperA', 'FACIAL_R_Eye', 'FACIAL_R_EyelidLowerA',
	             'FACIAL_R_EyelidLowerB']
	eye_jnts = leye_jnts + reye_jnts

	offset_jnts = cmds.listRelatives("neck_01", ad=True, type="joint")
	parents = ["neck_01", "neck_02", "head"]

	eye_head_jnts = []

	for eye in eye_jnts:
		if eye in offset_jnts:
			head_geo = cmds.listRelatives(eye, ad=True, type="joint")
			offset_jnts.remove(eye)
			if head_geo:
				for hg in head_geo:
					offset_jnts.remove(hg)
					eye_head_jnts.append(hg)
	for p in parents:
		if p in offset_jnts:
			offset_jnts.remove(p)

	cmds.select(offset_jnts)

	mh.mh_snap_joints_to_closest(mesh="eyeLeft_base", dmesh="eyeLeft_lod0_mesh", joints=leye_jnts)
	mh.mh_snap_joints_to_closest(mesh="eyeRight_base", dmesh="eyeRight_lod0_mesh", joints=reye_jnts)
	mh.mh_snap_joints_to_closest(mesh="head_base", dmesh="head_lod0_mesh", joints=offset_jnts)

	mh.mh_snap_all_joint_locs()
	save_dna(calibrated, jnt_dna)


##################################
# This is step 5
# animated Maps LODs
##################################
def step_five():
	"""
	This code is a function that performs a series of steps to read DNA data, modify it, and save it.

	The steps performed by this code are as follows:
	1. Calls the function 'read_dna()' with the parameter 'jnt_dna' to read the DNA data and returns a 'reader' object.
	2. Creates a FileStream object named 'stream' with the 'final_dna' file and sets the access mode as write and open mode as binary.
	3. Creates a BinaryStreamWriter object named 'writer' with the 'stream' object.
	4. Sets the writer object from the reader object using the 'setFrom()' method.
	5. Defines a list named 'new_lods' with the values [2, 3, 4].
	6. Retrieves the animated map LODs from the reader object using the 'getAnimatedMapLODs()' method and assigns it to the variable 'anim_lods'.
	7. Iterates over the 'new_lods' list and for each value of 'lod', performs the following:
	   - Sets the LOD animated map mapping for the 'writer' object using the 'setLODAnimatedMapMapping()' method.
	   - Assigns the value of the first element of 'anim_lods' to the 'lod' index in 'anim_lods'.
	8. Sets the animated map LODs for the 'writer' object using the 'setAnimatedMapLODs()' method with the modified 'anim_lods' list.
	9. Writes the modified DNA data to the stream using the 'write()' method of the 'writer' object.
	10. Checks if the status of the write operation is not OK using the 'Status.isOk()' method.
	11. If the status is not OK, retrieves the error message from the 'Status.get()' method and raises a RuntimeError with the error message.

	Note: This code does not provide any input/output parameters or return a value. It assumes the necessary classes and functions are imported and exist. The documentation does not include implementation details or type information.
	"""
	reader = read_dna(jnt_dna)

	stream = FileStream(final_dna, FileStream.AccessMode_Write, FileStream.OpenMode_Binary)
	writer = BinaryStreamWriter(stream)
	writer.setFrom(reader)

	new_lods = [2, 3, 4]
	anim_lods = reader.getAnimatedMapLODs()
	for lod in new_lods:
		writer.setLODAnimatedMapMapping(lod, 0)
		anim_lods[lod] = anim_lods[0]

	writer.setAnimatedMapLODs(anim_lods)
	writer.write()
	if not Status.isOk():
		status = Status.get()
		raise RuntimeError(f"Error saving DNA: {status.message}")


##################################
# This is step 6
# Propagate changes to dna, 5th step
##################################
def step_six():
	"""
	Assemble Scene

	This function assembles a scene using the given parameters.

	Parameters:
	- final_dna: A string representing the final DNA of the scene.
	- analog_gui_path: A string representing the path to the analog GUI.
	- gui_path: A string representing the path to the GUI.
	- aas_path: A string representing the path to the AAS.

	Returns:
	None

	Example:
	```
	assemble_scene(final_dna, analog_gui_path, gui_path, aas_path)
	```

	Note:
	- This function is responsible for renaming and saving the scene file.
	"""
	assemble_scene(final_dna, analog_gui_path, gui_path, aas_path)
	cmds.file(rename=review_scene)
	cmds.file(save=True)
