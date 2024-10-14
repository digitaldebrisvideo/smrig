from smrig import env
from smrig.lib import naminglib

# rig hierarchy variables
RIG_GROUP = naminglib.format_name("rig", node_type="transform")
PARTS_GROUP = naminglib.format_name("parts", node_type="transform")
JOINTS_GROUP = naminglib.format_name("joints", node_type="transform")
MODEL_GROUP = naminglib.format_name("model", node_type="transform")
LIBRARY_GROUP = naminglib.format_name("lib_GRP", node_type="transform")
NO_TRANSFORM_GROUP = naminglib.format_name("noxform", node_type="transform")

# guide constants
GUIDE_GRP = naminglib.format_name("guides", node_type="transform")
GUIDE_HIERARCHY = ["control", "placer", "joint", "geometry", "noxform"]

# rig set variables
RIG_SET = naminglib.format_name("rig", node_type="objectSet")
CONTROL_SET = naminglib.format_name("control", node_type="objectSet")
CACHE_SET = naminglib.format_name("cache", node_type="objectSet")
RENDER_SET = naminglib.format_name("render", node_type="objectSet")
ENGINE_SET = naminglib.format_name("bindjnts", node_type="objectSet")
LIBRARY_SET = naminglib.format_name("lib", node_type="objectSet")
ENGINE_EXCLUDE_SET = naminglib.format_name("engine_exclude", node_type="objectSet")

# rig ingredient tagging, the ingredient tags are used to keep track of which
# assets are used to build the rig. Upon publishing this attribute will be
# read and the file paths stored in the attributes used for publishing.
INGREDIENT_NODE = RIG_SET
INGREDIENT_ATTRIBUTE = "modelPath"
INGREDIENT_PATH = "{}.{}".format(RIG_SET, INGREDIENT_ATTRIBUTE)

# dynamic constants
ROOT_JOINT = naminglib.format_name(env.prefs.get_side("center"), "root", node_type="joint")
VISIBILITY_CONTROL = naminglib.format_name(env.prefs.get_side("center"), "visibility", node_type="animControl")

# tags for visibility
PART_PARENT_DRIVER_TAG = "partParentDriver"
PART_ATTRIBUTE_DRIVER_TAG = "partAttributeDriver"
PART_CONTROL_GROUP_TAG = "partControlsGroup"
PART_RIG_GROUP_TAG = "partRigGroup"
