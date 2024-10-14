import math

from maya import cmds

from smrig.dataio.types import matrix_constraints
from smrig.lib import animationlib
from smrig.lib import constraintslib
from smrig.lib import rivetlib
from smrig.lib import transformslib
from smrig.lib import utilslib

AUTO_WHEEL_EXP_STR = """
// Auto wheel expression ----------------------------------------

float $dummyX = ${dir_grp}.translateX;
float $dummyY = ${dir_grp}.translateY;
float $dummyZ = ${dir_grp}.translateZ;

vector $dir_vector = `getAttr ${dir_grp}.translate`;
vector $move_vector = `getAttr ${move_grp}.translate`;
vector $previous_vector = `getAttr ${previous_grp}.translate` ;

float $radius = ${wheel_radius} * ${world_scale_attr};

vector $wheel_vector = ($dir_vector - $move_vector);
vector $motion_vector = ($move_vector - $previous_vector);

float $distance = mag( $motion_vector );
$dot = dotProduct( $motion_vector, $wheel_vector, 1 );

if (frame < 1)
    ${move_grp}.wheelRotate = 0;
else{
    ${move_grp}.wheelRotate = (${move_grp}.wheelRotate + 360 / (6.28318530718 * $radius) * ($dot * $distance) * (${move_grp}.autoWheelEnable)) + ${move_grp}.wheelRotateOffset ;
}

${previous_grp}.translateX = ($move_vector.x);
${previous_grp}.translateY = ($move_vector.y);
${previous_grp}.translateZ = ($move_vector.z);
"""


def get_radius(verts=None):
	"""
	Get radius from two verts:

	:param verts: Two verts
	:return:
	"""
	verts = verts if verts else cmds.ls(sl=1, fl=1)
	if len(verts) != 2:
		raise Exception("Select only two verts, a center point and an outer circumference vert.")

	l0 = transformslib.xform.match_locator(verts[0])
	l1 = transformslib.xform.match_locator(verts[1])

	cmds.parent(l0, l1)
	cmds.setAttr(l0 + ".tx", 0)

	radius = utilslib.distance.get(l0, l1)
	cmds.delete(l0, l1)

	return radius


def create_auto_wheel_expression(drive_control_parent,
                                 wheel_radius,
                                 wheel_joints,
                                 world_scale_attr=None,
                                 wheel_control=None,
                                 main_control=None):
	"""
	Auto wheel expression.. Wheel joint MUST be oriented to world.

	:param str drive_control_parent: Wheel parent node
	:param float wheel_radius:
	:param list/str wheel_joints:
	:param str world_scale_attr: rig world scale attribute
	:param str wheel_control: where to put the  wheel spin attribute
	:param str main_control: where to put the auto wheel enable attribute
	:return:
	"""
	wheel_joints = utilslib.conversion.as_list(wheel_joints)

	auto_wheel_grp = cmds.createNode("transform", n=wheel_joints[0] + "_autoWheel_GRP")
	transformslib.xform.match(wheel_joints[0], auto_wheel_grp, rotate=False, scale=False)

	dir_grp = cmds.createNode("transform", n=wheel_joints[0] + "_autoWheel_direction_GRP")
	transformslib.xform.match(wheel_joints[0], dir_grp, rotate=False, scale=False)
	cmds.xform(dir_grp, r=1, t=[0, 0, wheel_radius])

	previous_grp = cmds.createNode("transform", n=wheel_joints[0] + "_autoWheel_previous_GRP")
	transformslib.xform.match(wheel_joints[0], previous_grp, rotate=False, scale=False)

	constraintslib.matrix_constraint(drive_control_parent, auto_wheel_grp)
	constraintslib.matrix_constraint(drive_control_parent, dir_grp)

	cmds.addAttr(auto_wheel_grp, ln="autoWheelEnable", k=1, min=0, max=1, dv=1)
	cmds.addAttr(auto_wheel_grp, ln="wheelRotateOffset", k=1)
	cmds.addAttr(auto_wheel_grp, ln="wheelRotate")

	if cmds.objExists("noxform_GRP"):
		cmds.parent(auto_wheel_grp, dir_grp, previous_grp, "noxform_GRP")

	for jnt in wheel_joints:
		cmds.connectAttr(auto_wheel_grp + ".wheelRotate", jnt + ".rx", f=True)

	expression_str = AUTO_WHEEL_EXP_STR.replace("${dir_grp}", dir_grp)
	expression_str = expression_str.replace("${move_grp}", auto_wheel_grp)
	expression_str = expression_str.replace("${previous_grp}", previous_grp)
	expression_str = expression_str.replace("${wheel_radius}", str(wheel_radius))
	expression_str = expression_str.replace("${world_scale_attr}", world_scale_attr if world_scale_attr else "1.0")
	cmds.expression(n="autoWheel_EXP#", s=expression_str)

	if wheel_control:
		if not cmds.objExists(wheel_control + ".wheelSpin"):
			cmds.addAttr(wheel_control, ln="wheelSpin", k=1)

		adl = cmds.createNode("addDoubleLinear")
		cmds.connectAttr(wheel_control + ".wheelSpin", adl + ".i1")
		cmds.connectAttr(auto_wheel_grp + ".wheelRotate", adl + ".i2")

		for jnt in wheel_joints:
			cmds.connectAttr(adl + ".o", jnt + ".rx", f=True)

	if main_control:
		if not cmds.objExists(main_control + ".autoWheel"):
			cmds.addAttr(main_control, ln="autoWheel", k=1, min=0, max=1, dv=1)

		cmds.connectAttr(main_control + ".autoWheel", auto_wheel_grp + ".autoWheelEnable")

	return auto_wheel_grp


def connect_tread_joints(curve, joints, attribute_driver=None, world_up_object=None, aim=True):
	"""
	Connect tread joints to curve via curve rivet,
	aim constrain and SDK them to spin in infinite cycle.

	:param str curve:
	:param list joints:
	:param str attribute_driver:
	:param str world_up_object:
	:param bool aim:
	:return:
	"""
	attribute_driver = attribute_driver if attribute_driver else curve
	world_up_object = world_up_object if world_up_object else curve

	# create rivets, joints and aim joints
	rivets = rivetlib.create_curve_rivet(curve, joints)

	if aim:
		for i in range(len(joints)):
			aim_jnt = joints[0] if i == len(joints) - 1 else joints[i + 1]
			cmds.aimConstraint(aim_jnt,
			                   joints[i],
			                   aim=[0, 0, 1],
			                   u=[1, 0, 0],
			                   wu=[1, 0, 0],
			                   wut="objectRotation",
			                   wuo=world_up_object)

	# sdk first rivet and drive all others
	if not cmds.objExists(attribute_driver + ".treadCycle"):
		cmds.addAttr(attribute_driver, ln="treadCycle", k=True)

	tread_driver = attribute_driver + ".treadCycle"
	for rivet in rivets:
		offset = cmds.getAttr(rivet + ".parameter")
		cmds.setDrivenKeyframe(rivet + ".parameter", cd=tread_driver, dv=offset, v=0, itt="spline", ott="spline")
		cmds.setDrivenKeyframe(rivet + ".parameter", cd=tread_driver, dv=1.0 + offset, v=1, itt="spline", ott="spline")

		sdk = animationlib.get_anim_curves(rivet)
		animationlib.set_inifity(sdk, pre="cycle", post="cycle")

	return tread_driver


def calculate_revolutions_per_tread(curve, wheel_radius):
	"""
	Return the value of wheel revolutions per tread.
	math: arc len / diameter

	:param str curve:
	:param float wheel_radius:
	:return:
	"""
	return cmds.arclen(curve, ch=0) / (2 * math.pi * wheel_radius)


def connect_tread_to_wheel_rotation(attribute_driver, tread_driver, curve, wheel_radius):
	"""
	Connect auto wheel wheelRotate attribute to tread driver cycle attribute.
	math: tread_cycle = wheel_rotation / 360.0 * revolutions / revolutions

	:param str attribute_driver:
	:param str tread_driver:
	:param str curve:
	:param float wheel_radius:
	:return:
	"""
	md1 = cmds.createNode("multiplyDivide")
	md2 = cmds.createNode("multiplyDivide")

	cmds.connectAttr(attribute_driver, md1 + ".i1x")
	cmds.setAttr(md1 + ".i2x", 360.0)
	cmds.setAttr(md1 + ".operation", 2)

	cmds.connectAttr(md1 + ".ox", md2 + ".i1x")
	cmds.setAttr(md2 + ".i2x", calculate_revolutions_per_tread(curve, wheel_radius))
	cmds.setAttr(md2 + ".operation", 2)

	cmds.connectAttr(md2 + ".ox", tread_driver, f=1)


def connect_wheel_to_tread_rotation(tread_driver, driven_attribute, wheel_radius):
	"""
	Connect auto wheel wheelRotate attribute to tread driver cycle attribute.
	math: wheel_rotation = 360 / (6.28318530718 * $radius) * tread_driver

	:param str tread_driver:
	:param str driven_attribute:
	:param float wheel_radius:
	:return:
	"""
	md = cmds.createNode("multiplyDivide", n="wtf_NMD")
	cmds.setAttr(md + ".i1x", 360 / wheel_radius * 6.28318530718)
	cmds.connectAttr(tread_driver, md + ".i2x")
	cmds.connectAttr(md + ".ox", driven_attribute, f=1)


def snap_pivots_wheel_jnts():
	"""
	This requires matrix constraints to already exist from wheel jnt to geo.

	:return: selection of adjusted geo node so you can write out hte new constraints.
	"""
	jnts = cmds.ls("*_wheel_JNT")
	data = matrix_constraints.get_data(cmds.ls("*_MTC"))

	selection = []
	drivers = []
	drivens = []
	for con, dat in data.items():

		driven = dat.get("driven")
		driver = dat.get("driver")

		if driver in jnts:
			cmds.delete(con)
			drivers.append(driver)
			drivens.append(driven)

	for driver, driven in zip(drivers, drivens):
		parent = cmds.listRelatives(driven, p=1)[0]
		cmds.parent(driven, driver)
		cmds.makeIdentity(driven, apply=1, t=1, r=1, s=1, n=0, pn=1)
		cmds.select(driven, hi=1)
		cmds.xform(cmds.ls(sl=1), piv=[0, 0, 0])
		cmds.parent(driven, parent)

		cmds.parentConstraint(driver, driven)
		selection.extend(utilslib.conversion.as_list(driven))

	cmds.select(selection)
	return selection
