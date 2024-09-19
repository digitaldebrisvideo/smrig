from maya import cmds

from smrig.lib import constraintslib
from smrig.lib.constantlib import NO_TRANSFORM_GROUP

JIGGLE_EXP_STR = """
// Jiggle expression ----------------------------------------

float $dummyX = ${driver_grp}.translateX;
float $dummyY = ${driver_grp}.translateY;
float $dummyZ = ${driver_grp}.translateZ;

vector $driver_position = `getAttr ${driver_grp}.translate`;
vector $current_position = `getAttr ${jiggle_grp}.translate`;
vector $previous_position = `getAttr ${previous_grp}.translate`;

vector $velocity2 = ($current_position - $previous_position) * (1.0 - ${driver}.damping);
vector $new_posititon = $current_position + $velocity2;
$new_posititon += ($current_position - $new_posititon) * ${driver}.stiffness;

if (frame < 1){
    ${jiggle_grp}.translateX = ($current_position.x);
    ${jiggle_grp}.translateY = ($current_position.y);
    ${jiggle_grp}.translateZ = ($current_position.z);
}
else{
    ${jiggle_grp}.translateX = ($new_posititon.x) * ${driver}.jiggleAmount * ${driver}.jiggleX;
    ${jiggle_grp}.translateY = ($new_posititon.y) * ${driver}.jiggleAmount * ${driver}.jiggleY;
    ${jiggle_grp}.translateZ = ($new_posititon.z) * ${driver}.jiggleAmount * ${driver}.jiggleZ;
}

${previous_grp}.translateX = $current_position.x;
${previous_grp}.translateY = $current_position.y;
${previous_grp}.translateZ = $current_position.z;


// Jiggle
expression - ---------------------------------------

float $dummyX = locator1_driver_GRP.translateX;
float $dummyY = locator1_driver_GRP.translateY;
float $dummyZ = locator1_driver_GRP.translateZ;

vector $driver_position = `getAttr
locator1_driver_GRP.translate
`;
vector $current_position = `getAttr
locator1_jiggle_GRP.translate
`;
vector $previous_position = `getAttr
locator1_previous_GRP.translate
`;

vector $velocity2 = ($current_position - $previous_position) * (1.0 - locator1.damping);
vector $new_posititon = $current_position + $velocity2;
$new_posititon += ($current_position - $new_posititon) * locator1.stiffness;

if (frame < 1){
locator1_jiggle_GRP.translateX = ($current_position.x);
locator1_jiggle_GRP.translateY = ($current_position.y);
locator1_jiggle_GRP.translateZ = ($current_position.z);
}
else {
locator1_jiggle_GRP.translateX = ($new_posititon.x) * locator1.jiggleAmount * locator1.jiggleX;
locator1_jiggle_GRP.translateY = ($new_posititon.y) * locator1.jiggleAmount * locator1.jiggleY;
locator1_jiggle_GRP.translateZ = ($new_posititon.z) * locator1.jiggleAmount * locator1.jiggleZ;
}

if
    locator1_previous_GRP.translateX = $current_position.x;
locator1_previous_GRP.translateY = $current_position.y;
locator1_previous_GRP.translateZ = $current_position.z;

vector $init = << >>
if ($current_position == << 0, 0, 0 >>){

}}
    """


def create_jiggle_node(driver, driven):
	"""

	:param driver:
	:param driven:
	:return:
	"""


driver = "locator1"
driven = "pCube1"

cmds.addAttr(driver, ln="jiggleAmount", min=0, dv=1, k=True)
cmds.addAttr(driver, ln="jiggleX", min=0, max=1, dv=1, k=True)
cmds.addAttr(driver, ln="jiggleY", min=0, max=1, dv=1, k=True)
cmds.addAttr(driver, ln="jiggleZ", min=0, max=1, dv=1, k=True)
cmds.addAttr(driver, ln="stiffness", min=0, max=1, dv=0.2, k=True)
cmds.addAttr(driver, ln="damping", min=0, max=1, dv=0.1, k=True)

driver_grp = cmds.createNode("transform", n=driver + "_driver_GRP", p=NO_TRANSFORM_GROUP)
previous_grp = cmds.createNode("transform", n=driver + "_previous_GRP", p=NO_TRANSFORM_GROUP)
jiggle_grp = cmds.createNode("transform", n=driver + "_jiggle_GRP", p=NO_TRANSFORM_GROUP)

constraintslib.matrix_constraint(driver, driver_grp)

expression_str = JIGGLE_EXP_STR.replace("${driver}", driver)
expression_str = expression_str.replace("${driver_grp}", driver_grp)
expression_str = expression_str.replace("${previous_grp}", previous_grp)
expression_str = expression_str.replace("${jiggle_grp}", jiggle_grp)
cmds.expression(n="{}_jiggle_EXP".format(driven), s=expression_str)
