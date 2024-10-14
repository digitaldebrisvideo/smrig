import os

import maya.cmds as cmds
from smrig import dataio, env
from smrig.lib import pathlib

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"


def get_char_bsh():
	"""
	This function, `get_char_bsh()`, retrieves the file paths for the base and mouth blender shape (bsh) files related to the current lookdev asset.

	Parameters:
	    None

	Returns:
	    Tuple (str, str): The file paths for the base and mouth bsh files respectively.

	Example usage:
	    base, mouth = get_char_bsh()
	"""

	lookdev_data = env.asset.get_models()[0]
	lookdev_filepath = lookdev_data["file_path"]
	lookdev_split = lookdev_filepath.split("/")
	model_only_scene = lookdev_filepath.replace("/" + lookdev_split[-1], "")
	scene_directory = model_only_scene.replace("/" + lookdev_split[-2], "")
	char_bsh_dir = pathlib.normpath(os.path.join(scene_directory, "Blends"))
	base_bsh_file = pathlib.normpath(os.path.join(char_bsh_dir, "Head_Base_Blends.bsh"))
	mouth_bsh_file = pathlib.normpath(os.path.join(char_bsh_dir, "Head_Mouth_Blends.bsh"))

	return (base_bsh_file, mouth_bsh_file)


def load_custom_blends():
	"""
	Load custom blends for a character's head.

	This function loads two sets of custom blends for a character's head: "Head_Base_Blends" and "Head_Mouth_Blends". It does the following:

	1. Load "Head_Base_Blends" blendshape file:
	     - Retrieves the path of the character's base blendshape file using the get_char_bsh() function.
	     - Checks if the blendshape file exists in the specified path.
	     - If the file exists:
	          - Removes any existing "Head_Base_Blends" blendshape node from the scene.
	          - Loads the blendshape file using the dataio.load() function.
	     - If the file does not exist:
	          - Prints a message indicating that character-specific blends for "Head_Base_Blends" do not exist, and the default base blendshape should be used.

	2. Load "Head_Mouth_Blends" blendshape file:
	     - Retrieves the path of the character's mouth blendshape file using the get_char_bsh() function.
	     - Checks if the blendshape file exists in the specified path.
	     - If the file exists:
	          - Removes any existing "Head_Mouth_Blends" blendshape node from the scene.
	          - Loads the blendshape file using the dataio.load() function.
	     - If the file does not exist:
	          - Prints a message indicating that character-specific blends for "Head_Mouth_Blends" do not exist, and the default base blendshape should be used.
	"""

	# load base bsh file

	char_base_bsh = get_char_bsh()[0]
	if os.path.isfile(char_base_bsh):
		if cmds.objExists("Head_Base_Blends"):
			cmds.delete("Head_Base_Blends")
			dataio.load(file_path=char_base_bsh)
	else:
		print("character specific blends for Head_Base_Blends do not exist. using default base")

	# load mouth bsh file

	char_mouth_bsh = get_char_bsh()[1]
	if os.path.isfile(char_mouth_bsh):
		if cmds.objExists("Head_Mouth_Blends"):
			cmds.delete("Head_Mouth_Blends")
		dataio.load(file_path=char_mouth_bsh)
	else:
		print("character specific blends for Head_Mouth_Blends do not exist. using default base")
