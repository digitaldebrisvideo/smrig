import logging

import maya.cmds as cmds
import maya.mel as mel

from smrig import env
from smrig.lib import constantlib
from smrig.lib import nodepathlib
from smrig.lib import selectionlib
from smrig.lib import transformslib
from smrig.lib.mocaplib import pose
from smrig.lib.mocaplib.constants import JOINT_LABEL_MAPPING, JOINT_CONTROL_MAPPING, MOCAP_BLEND_RIG_TOKEN

log = logging.getLogger("smrig.mocaplib.hik")


def find_character_node(top_node):
	"""

	:param top_node:
	:return:
	"""
	joints = selectionlib.get_children(top_node, all_descendents=True, types="joint", full_path=True)
	for joint in joints:
		node = cmds.listConnections(joint, type="HIKCharacterNode")
		if node:
			return node[0]


def create_character(name):
	"""
	Create an HIK character definition.

	:param str name:
	:return: HIK character node
	:rtype: str
	"""
	character = mel.eval('hikCreateCharacter("{}")'.format(name))
	try:
		mel.eval('hikUpdateCharacterList; hikSelectDefinitionTab')
	except:
		pass
	set_character_control_properties(character)
	return character


def set_character_control_properties(character):
	"""

	:return:
	"""
	property = cmds.listConnections(character, type="HIKProperty2State")
	cmds.setAttr("{}.ForceActorSpace".format(property[0]), 1)
	cmds.setAttr("{}.HipsHeightCompensationMode".format(property[0]), 0)
	cmds.setAttr("{}.AnkleHeightCompensationMode".format(property[0]), 0)

	attrs = ["ReachActorRightWrist",
	         "ReachActorRightWristRotation",
	         "ReachActorLeftWristRotation",
	         "ReachActorLeftHandPinky",
	         "ReachActorLeftHandRing",
	         "ReachActorLeftHandMiddle",
	         "ReachActorLeftHandIndex",
	         "ReachActorLeftHandThumb",
	         "ReachActorLeftElbow",
	         "ReachActorRightElbow",
	         "ReachActorChest",
	         "ReachActorHead",
	         "ReachActorHeadRotation",
	         "ReachActorChestRotation",
	         "ReachActorRightKnee",
	         "ReachActorLeftKnee",
	         "ReachActorRightHandIndex",
	         "ReachActorRightHandThumb",
	         "ReachActorRightHandMiddle",
	         "ReachActorRightHandRing",
	         "ReachActorRightHandPinky",
	         "ReachActorLeftToesBase",
	         "ReachActorRightToesBase",
	         "ReachActorLeftWrist"]
	for attr in attrs:
		cmds.setAttr("{}.{}".format(property[0], attr), 1)


def set_character_object(joint, character, index):
	"""
	Connect a single joint to HIK character attribute.

	:param joint:
	:param character:
	:param index:
	:return:
	"""
	if cmds.objExists(joint):
		try:
			mel.eval('setCharacterObject("{0}","{1}", {2}, 0);'.format(joint, character, index))

		except:
			cmds.warning('Could not connect {0} to character: {1} at index: {2}'.format(joint, character, index))


def connect_joints_by_label(root, character):
	"""
	Connect joints in given hierarchy by joint side and label to given HIK character node.

	:param str root: Root joint of skeleton
	:param str character: HIK character node.
	:return: Connected joitns
	:rtype: list
	"""
	hik_label_iterators = {k: iter(v) for k, v in JOINT_LABEL_MAPPING.items()}
	joints = selectionlib.get_children(root, all_descendents=True, types="joint", full_path=True) + [root]

	connected_joints = []
	for joint in reversed(joints):
		if not cmds.nodeType(joint) == "joint":
			continue

		side = cmds.getAttr("{}.side".format(joint), asString=True)
		label = cmds.getAttr("{}.type".format(joint), asString=True)
		label = cmds.getAttr("{}.otherType".format(joint), asString=True) if label == "Other" else label
		key = "{}_{}".format(side, label)

		if key in hik_label_iterators.keys():
			index = next(hik_label_iterators[key])
			if index:
				set_character_object(joint, character, index)
				connected_joints.append(joint)

	return selectionlib.sort_by_hierarchy(connected_joints)


def characterize_rig(root=None, character_name=None):
	"""
	Create a HIK character definition and connect joints based on labels.

	:param str root: Top node for mocap skeleton.
	:param str/None character_name:
	:return: character HIK node
	:rtype: str
	"""
	root = root if root else constantlib.ROOT_JOINT
	character_name = character_name if character_name else env.asset.get_asset() + "_mocap_HIK"

	namespace = nodepathlib.get_namespace(root)
	pose.set_pose("t_pose", namespace=namespace)
	character = create_character(character_name)
	connect_joints_by_label(root, character)
	return character


def disconnect_mocap_blend(namespace, descriptor=None):
	"""
	Characterize and
	:param namespace:
	:return:
	"""
	descriptor = MOCAP_BLEND_RIG_TOKEN if descriptor is None else descriptor
	nodes = cmds.ls("{}:*{}Bake*".format(namespace, descriptor))
	if nodes:
		cmds.delete(nodes)


def connect_mocap_blend(namespace):
	"""

	:param namespace:
	:return:
	"""
	descriptor = MOCAP_BLEND_RIG_TOKEN

	if cmds.ls("{}:*{}Bake*".format(namespace, descriptor)):
		return

	bake_controls = ["{}:C_world_CTL".format(namespace)]
	for controls in JOINT_CONTROL_MAPPING.values():
		for control in controls:
			bake_controls.append("{}:{}".format(namespace, control))

	pose.set_pose("a_pose", namespace=namespace)

	for driver, controls in JOINT_CONTROL_MAPPING.items():
		driver = "{}:{}".format(namespace, driver.format(descriptor))

		for control in controls:
			control = "{}:{}".format(namespace, control)

			try:
				con_name = "{}_{}_PRC".format(control, "{}Bake".format(descriptor))
				cmds.parentConstraint(driver, control, mo=1, n=con_name)

			except:
				try:
					con_name = "{}_{}_OC".format(control, "{}Bake".format(descriptor))
					cmds.orientConstraint(driver, control, mo=1, n=con_name)

				except:
					try:
						cmds.connectAttr(driver + ".ry", control + ".ry")

					except:
						loc_name = "{}_{}_LOC".format(control, "{}Bake".format(descriptor))
						con_name = "{}_{}_PC".format(control, "{}Bake".format(descriptor))
						loc = transformslib.xform.match_locator(control, name=loc_name)
						cmds.pointConstraint(loc, control, mo=1, n=con_name)
						cmds.parent(loc, driver)

	pose.set_pose("t_pose", namespace=namespace)


def update_hik_ui():
	"""

	:return:
	"""
	try:
		mel.eval("""ToggleCharacterControls;
                    ToggleCharacterControls;
                    hikUpdateCharacterList(); hikSelectDefinitionTab();
                    hikUpdateDefinitionButtonState();
                    hikUpdateContextualUI;
                    hikUpdateCustomRigUI; 
                    hikUpdateCurrentCharacterFromUI();""")
	except:
		pass


def set_source_character(anim_char, mocap_char):
	"""

	:param anim_char:
	:param mocap_char:
	:return:
	"""
	mel.eval("""$source = "{0}";
                hikSetCurrentCharacter $source;
                string $character = hikGetCurrentCharacter();
                hikSelectLastTab( $character );

                hikSetCurrentSourceFromCharacter($character);
                hikUpdateSourceList();

                hikDefinitionUpdateCharacterLists;
                hikDefinitionUpdateBones;""".format(anim_char))

	update_hik_ui()

	arg = 'string $source = "{0}";'.format(mocap_char)
	arg += """
            waitCursor -state true;

            $source = stringRemovePrefix( $source, " " );
            hikSetCurrentSource( $source );
            int $isRemote = ( endsWith( $source, "(remote)" ) ) ? true : false;
            $character = hikGetCurrentCharacter();
            hikEnableCharacter( $character, 2 );

            if ( !hikIsNoneCharacter( $source ) ) {

                string $labelControlRig = (uiRes("m_hikGlobalUtils.kControlRig"));
                string $labelStance= (uiRes("m_hikGlobalUtils.kStance"));
                if( $source == $labelControlRig ) {
                    int $hasControlRig = hikHasControlRig($character);
                    if( $hasControlRig ) {
                        hikSetRigInput($character);
                        hikSetLiveState( $character, 1 );
                        hikSelectControlRigTab();
                    }
                    else {
                        hikCreateControlRig();
                    }
                }
                else {
                    if( !hikCheckDefinitionLocked($character) ) {
                        hikSelectDefinitionTab();
                        waitCursor -state false;
                    }
                    if( $source == $labelStance) {
                        hikSetStanceInput($character);
                    }
                    else {
                        hikEnableCharacter( $character, 1 );

                        if ( $isRemote )
                            hikSetLiveCharacterInput( $character );
                        else
                            hikSetCharacterInput( $character, $source );

                        if ( hikHasCustomRig( $character ) )
                            hikSelectCustomRigTab;
                        else
                            hikSelectControlRigTab;
                    }
                }
            }

            hikUpdateLiveConnectionUI;
            hikUpdateCurrentCharacterFromUI();
            waitCursor -state false;"""

	mel.eval(arg)
	update_hik_ui()


def bake_to_controls(namespace,
                     repo_world_control=True,
                     sample_by=1,
                     bake_srt=True,
                     skip_srt=[],
                     minimize_rotation=False,
                     remove_flip_joints=[],
                     frame_range=None
                     ):
	"""
	Bake mocap anim to controls.

	:param namespace:
	:param repo_world_control:
	:param sample_by:
	:param bake_srt:
	:param skip_srt:
	:param minimize_rotation:
	:param remove_flip_joints:
	:param frame_range:
	:return:
	"""
	descriptor = MOCAP_BLEND_RIG_TOKEN
	junk = cmds.ls("{}:*{}Bake*".format(namespace, descriptor))

	bake_controls = []
	for controls in JOINT_CONTROL_MAPPING.values():
		for control in controls:
			bake_controls.append("{}:{}".format(namespace, control))

	if frame_range:
		cmds.playbackOptions(min=frame_range[0], max=frame_range[1])

	if repo_world_control:
		start_frame = cmds.playbackOptions(query=True, minTime=True)
		cmds.currentTime(start_frame)

		cmds.cutKey("{}:C_world_CTL".format(namespace), at=["translate", "rotate"])
		cmds.xform("{}:C_world_CTL".format(namespace),
		           ws=1,
		           t=cmds.xform("{}:C_cog_CTL".format(namespace), q=1, ws=1, t=1),
		           ro=cmds.xform("{}:C_cog_CTL".format(namespace), q=1, ws=1, ro=1)
		           )

		cmds.setAttr("{}:C_world_CTL.ty".format(namespace), 0)
		cmds.setAttr("{}:C_world_CTL.rx".format(namespace), 0)
		cmds.setAttr("{}:C_world_CTL.rz".format(namespace), 0)

		cmds.setKeyframe("{}:C_world_CTL".format(namespace), at=["translate", "rotate"], time=start_frame)

	bake.bake_animation(
		cmds.ls(bake_controls),
		sample_by,
		bake_srt,
		skip_srt,
		minimize_rotation,
		remove_flip_joints,
		attributes=["translate", "rotate"]
	)

	junk = cmds.ls(junk)
	if junk:
		cmds.delete(junk)

	log.info("Finished Bake!")
