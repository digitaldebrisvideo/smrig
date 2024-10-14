import math

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds

from smrig.lib import attributeslib

AXIS = ["x", "y", "z"]
AXIS_VECTORS = {
	"+x": OpenMaya.MVector.kXaxisVector,
	"+y": OpenMaya.MVector.kYaxisVector,
	"+z": OpenMaya.MVector.kZaxisVector,
	"-x": OpenMaya.MVector.kXnegAxisVector,
	"-y": OpenMaya.MVector.kYnegAxisVector,
	"-z": OpenMaya.MVector.kZnegAxisVector
}
DIRECTION_VALUE_MAPPER = {"+": 1, "-": -1}
DIRECTION_NAME_MAPPER = {"+": "Plus", "-": "Minus"}


class HelperSystem(object):
	"""
	The helper system allows helper joints to be created that are driven by
	the rotational values of the provided joint. The rotational values are
	purely calculated on the one axis, this makes the helpers easier to
	manage.

	Multiple helpers can be created for the same node, for calculation speed
	reasons they share parts of the same network. It is important to only
	initialize the class for a node once and create all the joints from there.
	Otherwise duplicate parts of the network will be created.

	Example:
		.. code-block:: python

			system = HelperSystem("L_IndexFinger2_JNT")
			joint = system.create_joint(
				direction="+",
				direction_axis="y",
				rotate_axis="x",
				radius=0.5
			)

	:param str node:
	:param str parent:
	"""

	def __init__(self, node, parent=None):
		# variables
		self._node = node
		self._parent = parent

		# internal variables
		self._local_matrix_plug = None
		self._local_pos_plug = None
		self._local_vector_plugs = {}
		self._angle_plugs = {}

	# ------------------------------------------------------------------------

	@property
	def name(self):
		"""
		:return: Name
		:rtype: str
		"""
		# TODO: nicer way to get name?
		return self.node.rsplit("_", 1)[0]

	@property
	def node(self):
		"""
		:return: Node
		:rtype: str
		"""
		return self._node

	@property
	def parent(self):
		"""
		:return: Parent node
		:rtype: str
		"""
		return self._parent

	# ------------------------------------------------------------------------

	@staticmethod
	def get_spare_axis(*axis):
		"""
		The functionality in this class requires to have two axis specified,
		this utility function can be used to extract the missing axis.

		:param axis:
		:return: Spare axis
		:rtype: str
		"""
		return list((set(AXIS) - set(axis)))[0]

	@staticmethod
	def get_matrix_rotation_match(child_plug, parent_plug):
		"""
		It is possible the parent matrix does not have the same orientation as
		the child. This would result in incorrect rotation if not addressed.
		This function return a matrix that match as close as possible the
		rotation of the child using 90 degree increments.

		:param str child_plug:
		:param str parent_plug:
		:return: OpenMaya.MMatrix
		"""
		# variable
		offset_matrix = OpenMaya.MMatrix()

		# get matrices
		child_matrix = OpenMaya.MMatrix(cmds.getAttr(child_plug))
		parent_matrix = OpenMaya.MMatrix(cmds.getAttr(parent_plug))

		# get local matrix
		local_matrix = parent_matrix * child_matrix.inverse()
		local_matrix = list(local_matrix)

		# get vectors
		offset_vectors = {}
		local_vectors = {
			a: OpenMaya.MVector(local_matrix[start_index:end_index])
			for a, (start_index, end_index) in zip(AXIS, [[0, 3], [4, 7], [8, 11]])
		}

		# build offset vectors
		for a in AXIS:
			local_vector = local_vectors.get(a)
			min_angle = (math.pi * 0.5) - 0.001
			min_vector = None
			for a_direction, vector in AXIS_VECTORS.items():
				angle = local_vector.angle(vector)
				if angle < min_angle:
					min_angle = angle
					min_vector = vector

			offset_vectors[a] = min_vector

		# populate offset matrix
		for i, a in enumerate(AXIS):
			for j in range(3):
				offset_matrix.setElement(i, j, offset_vectors[a][j])

		# return offset matrix
		return offset_matrix

	# ------------------------------------------------------------------------

	def get_parent_matrix_plug(self):
		"""
		Get parent matrix plug, the parent is an optional variable. This
		function will return the right plug if a parent is defined or not.

		:return: Parent matrix plug
		:rtype: str
		"""
		return "{}.worldMatrix".format(self.parent) \
			if self.parent \
			else "{}.parentMatrix".format(self.node)

	def get_parent_inverse_matrix_plug(self):
		"""
		Get parent inverse matrix plug, the parent is an optional variable.
		This function will return the right plug if a parent is defined or
		not.

		:return: Parent inverse matrix plug
		:rtype: str
		"""
		return "{}.worldInverseMatrix".format(self.parent) \
			if self.parent \
			else "{}.parentInverseMatrix".format(self.node)

	# ------------------------------------------------------------------------

	def get_local_matrix_plug(self):
		"""
		The local matrix plug is independent from the forward axis and rotate
		axis. For this reason its plug is stored in a private variable to make
		sure it only gets created once.

		:return: Local matrix plug
		:rtype: str
		"""
		# get existing
		if self._local_matrix_plug:
			return self._local_matrix_plug

		# get parent matrix plug
		child_matrix_plug = "{}.worldMatrix".format(self.node)
		parent_matrix_plug = self.get_parent_matrix_plug()

		# get matrix match
		offset_matrix = self.get_matrix_rotation_match(
			child_matrix_plug,
			parent_matrix_plug
		)

		parent_matrix_plug = self.get_parent_inverse_matrix_plug()

		# create local matrix node
		mm_name = "{}_Helper_MM".format(self.name)
		mm = cmds.createNode("multMatrix", name=mm_name)
		cmds.connectAttr(child_matrix_plug, "{}.matrixIn[0]".format(mm))
		cmds.connectAttr(parent_matrix_plug, "{}.matrixIn[1]".format(mm))
		cmds.setAttr("{}.matrixIn[2]".format(mm), list(offset_matrix), type="matrix")

		# store local matrix plug
		self._local_matrix_plug = "{}.matrixSum".format(mm)
		return self._local_matrix_plug

	def get_local_pos_plug(self):
		"""
		The local pps plug is independent from the forward axis and rotate
		axis. For this reason its plug is stored in a private variable to make
		sure it only gets created once.

		:return: Local pos plug
		:rtype: str
		"""
		# get existing
		if self._local_pos_plug:
			return self._local_pos_plug

		# get matrix plug
		matrix_plug = self.get_local_matrix_plug()

		# create local matrix node
		dm_name = "{}_Helper_DM".format(self.name)
		dm = cmds.createNode("decomposeMatrix", name=dm_name)
		cmds.connectAttr(matrix_plug, "{}.inputMatrix".format(dm))

		# store local matrix plug
		self._local_pos_plug = "{}.outputTranslate".format(dm)
		return self._local_pos_plug

	def get_local_vector_plug(self, direction_axis):
		"""
		The local pps plug is independent from the rotate axis. For this
		reason its plug is stored in a private variable in dictionary format
		to make sure it only gets created once for each forward axis.

		:param str direction_axis: "x", "y" or "z"
		:return: Local vector plug
		:rtype: str
		"""
		# get existing
		vector_plug = self._local_vector_plugs.get(direction_axis)
		if vector_plug:
			return vector_plug

		# get matrix plug
		matrix_plug = self.get_local_matrix_plug()

		# create local vector node
		vp_name = "{}_Helper{}_VP".format(self.name, direction_axis.upper())
		vp = cmds.createNode("vectorProduct", name=vp_name)
		cmds.setAttr("{}.operation".format(vp), 3)
		cmds.setAttr("{}.input1{}".format(vp, direction_axis.upper()), 1)
		cmds.connectAttr(matrix_plug, "{}.matrix".format(vp))

		# get local vector plug
		local_vector_plug = "{}.output".format(vp)

		# store local vector plug
		self._local_vector_plugs[direction_axis] = local_vector_plug

		return local_vector_plug

	def get_angle_plug(self, direction_axis, rotate_axis):
		"""
		Get the angle of rotation in degrees between the parent of the node
		and the node itself.

		:param str direction_axis: "x", "y" or "z"
		:param str rotate_axis: "x", "y" or "z"
		:return: Angle plug
		:rtype: str
		"""
		# get existing
		angle_plug = self._angle_plugs.get(direction_axis + rotate_axis)
		if angle_plug:
			return angle_plug

		# get local vector plug
		vector_plug = self.get_local_vector_plug(direction_axis)
		up_axis = self.get_spare_axis(direction_axis, rotate_axis)

		# base name
		base_name = "{}_Helper{}{}Angle".format(self.name, direction_axis.upper(), rotate_axis.upper())

		# create angle between
		ab_name = "{}_AB".format(base_name)
		ab = cmds.createNode("angleBetween", name=ab_name)
		cmds.setAttr("{}.vector1".format(ab), 0, 0, 0)
		cmds.setAttr("{}.vector1{}".format(ab, direction_axis.upper()), 1)
		cmds.setAttr("{}.vector2".format(ab), 0, 0, 0)
		cmds.connectAttr(vector_plug + direction_axis.upper(), "{}.vector2{}".format(ab, direction_axis.upper()))
		cmds.connectAttr(vector_plug + up_axis.upper(), "{}.vector2{}".format(ab, up_axis.upper()))

		# sometimes the angle between euler values can go over the range of
		# -180 and 180. For this reason we multiply the angle with the axis
		# of the rotation axis to get the correct rotational values.
		md_name = "{}_MD".format(base_name)
		md = cmds.createNode("multiplyDivide", name=md_name)
		cmds.connectAttr("{}.angle".format(ab), "{}.input1{}".format(md, rotate_axis.upper()))
		cmds.connectAttr("{}.axis".format(ab), "{}.input2".format(md))

		# subtract rotation from a standard value of 180, this will
		# give us rotation values between 0 and 360 degrees.
		adl_name = "{}_ADL".format(base_name)
		adl = cmds.createNode("addDoubleLinear", name=adl_name)
		cmds.setAttr("{}.input1".format(adl), 180)
		cmds.connectAttr("{}.output{}".format(md, rotate_axis.upper()), "{}.input2".format(adl))

		# get angle plug
		get_angle_plug = "{}.output".format(adl)

		# store angle plug
		self._angle_plugs[direction_axis + rotate_axis] = get_angle_plug

		return get_angle_plug

	# ------------------------------------------------------------------------

	def create_clamp_plug(self, input_plug, min_plug, max_plug, name):
		"""
		Clamp the input plug between the provided min and max plugs. This will
		allow the max angle to be controlled.

		:param str input_plug:
		:param str min_plug:
		:param str max_plug:
		:param str name:
		:return: Clamp plug
		:rtype: str
		"""
		# create clamp node
		clamp = cmds.createNode("clamp", name=name)
		cmds.connectAttr(input_plug, "{}.inputR".format(clamp))
		cmds.connectAttr(min_plug, "{}.minR".format(clamp))
		cmds.connectAttr(max_plug, "{}.maxR".format(clamp))

		# get clamp plug
		clamp_plug = "{}.outputR".format(clamp)

		return clamp_plug

	def create_multiplier_plug(self, input_plug, name):
		"""
		Get the multiplier based on the rotation value. This value doesn't yet
		take into account the radius or direction. This value is the amount
		the circle should move if the radius is set to 1.

		:param str input_plug:
		:param str name:
		:return: Multiplier plug
		:rtype: str
		"""
		# get sin and cosine of the angle using the euler to quat node
		etq = cmds.createNode("eulerToQuat", name=name)
		cmds.connectAttr(input_plug, "{}.inputRotateX".format(etq))

		# get angle plug
		multiplier_plug = "{}.outputQuatW".format(etq)

		return multiplier_plug

	# ------------------------------------------------------------------------

	def create_joint(self, direction="+", direction_axis="x", rotate_axis="z", radius=1):
		"""
		Create a joint that have its translation driven based on the
		rotational difference between the node and its parent. Attributes will
		be added to the node so the result can be be altered.

		:param str direction:
			The direction determines if the joint is places along the positive
			or negative direction along the direction_axis. ( "+" or "-" )
		:param str direction_axis:
			The direction_axis determines along which axis the joint is
			placed. The direction axis is in object space. ( "x", "y" or "z" )
		:param str rotate_axis:
			The rotation_axis determines along which axis the relative
			rotation is read between the node and its parent matrix. The
			rotation axis is in object space. ( "x", "y" or "z" )
		:param float/int radius:
			The radius at which the joint is placed. The displacement caused
			by the radius value is in object space.
		:return: Helper joint
		:rtype: :class:`~HelperJoint`
		"""
		# get direction variables
		direction_name = DIRECTION_NAME_MAPPER.get(direction, "Pos")
		direction_value = DIRECTION_VALUE_MAPPER.get(direction, 1)

		# multiplier direction value might change depending on the forward and
		# rotate axis. If the forward and rotate are not next to each other
		# the direction will have to be reversed.
		axis = AXIS[:] + ["x"]
		axis_index = axis.index(direction_axis)
		multiplier_direction_value = 1 if axis[axis_index + 1] == rotate_axis else -1

		# get forward axis
		forward_axis = self.get_spare_axis(direction_axis, rotate_axis)

		# based on the forward axis it is possible that the direction itself
		# will have to be reversed. This is to make sure that mirrored joints
		# will receive the same treatment as non-mirrored
		local_pos_plug = self.get_local_pos_plug()
		local_pos_value = cmds.getAttr("{}{}".format(local_pos_plug, forward_axis.upper()))
		direction_value *= local_pos_value / abs(local_pos_value)

		# get base name
		base_name = "{}_Helper{}{}{}".format(self.name, direction_axis.upper(), rotate_axis.upper(), direction_name)

		# validate joint
		joint_name = "{}_JNT".format(base_name)
		if cmds.objExists(joint_name):
			raise RuntimeError("Helper joint '{}' already exists!".format(joint_name))

		# create joint
		cmds.select(clear=True)
		joint = cmds.joint(name=joint_name)
		joint = cmds.parent(joint, self.node)[0]

		# disable segment scale compensation
		cmds.setAttr("{}.segmentScaleCompensate".format(joint), 0)
		cmds.setAttr("{}.jointOrient".format(joint), 0, 0, 0)

		# set joint radius
		parent_radius = cmds.getAttr("{}.radius".format(self.node))
		cmds.setAttr("{}.radius".format(joint), parent_radius * 0.25)

		# create joint attributes
		common_arguments = {"keyable": False, "attributeType": "float"}
		common_rotation_arguments = common_arguments.copy()
		common_rotation_arguments.update({"minValue": 0, "maxValue": 360})

		attributeslib.add_spacer_attribute(joint, "HELPER_CONTROLS")
		cmds.addAttr(joint, niceName="Radius", longName="pac_helper_radius", minValue=0.001, defaultValue=radius,
		             **common_arguments)
		cmds.addAttr(joint, niceName="Current Rotation", longName="pac_helper_current_rotation", defaultValue=0,
		             **common_rotation_arguments)
		cmds.addAttr(joint, niceName="Min Rotation", longName="pac_helper_min_rotation", defaultValue=0,
		             **common_rotation_arguments)
		cmds.addAttr(joint, niceName="Max Rotation", longName="pac_helper_max_rotation", defaultValue=360,
		             **common_rotation_arguments)

		attributeslib.add_spacer_attribute(joint, "HELPER_MULTIPLIER_CONTROLS")
		cmds.addAttr(joint, niceName="Multiplier X", longName="pac_helper_multiplier_x", **common_arguments)
		cmds.addAttr(joint, niceName="Multiplier Y", longName="pac_helper_multiplier_y", **common_arguments)
		cmds.addAttr(joint, niceName="Multiplier Z", longName="pac_helper_multiplier_z", **common_arguments)
		cmds.setAttr("{}.pac_helper_multiplier_{}".format(joint, forward_axis), 1)

		# set attributes to be visible in the channel box
		cmds.setAttr("{}.pac_helper_radius".format(joint), channelBox=True)
		cmds.setAttr("{}.pac_helper_current_rotation".format(joint), channelBox=True)
		cmds.setAttr("{}.pac_helper_min_rotation".format(joint), channelBox=True)
		cmds.setAttr("{}.pac_helper_max_rotation".format(joint), channelBox=True)
		cmds.setAttr("{}.pac_helper_multiplier_x".format(joint), channelBox=True)
		cmds.setAttr("{}.pac_helper_multiplier_y".format(joint), channelBox=True)
		cmds.setAttr("{}.pac_helper_multiplier_z".format(joint), channelBox=True)

		# create angle plug
		angle_plug = self.get_angle_plug(direction_axis, rotate_axis)
		cmds.connectAttr(angle_plug, "{}.pac_helper_current_rotation".format(joint))

		# create clamp node
		clamp_plug = self.create_clamp_plug(
			angle_plug,
			"{}.pac_helper_min_rotation".format(joint),
			"{}.pac_helper_max_rotation".format(joint),
			name="{}AngleClamp_CLMP".format(base_name)
		)

		# create multiplier plug
		multiplier_plug = self.create_multiplier_plug(
			clamp_plug,
			name="{}Angle_ETQ".format(base_name)
		)

		# multiply radius and direction
		direction_mdl_name = "{}Direction_MDL".format(base_name)
		direction_mdl = cmds.createNode("multDoubleLinear", name=direction_mdl_name)
		cmds.setAttr("{}.input1".format(direction_mdl), direction_value)
		cmds.connectAttr("{}.pac_helper_radius".format(joint), "{}.input2".format(direction_mdl))

		# multiply radius and direction
		direction_multiplier_mdl_name = "{}DirectionMultiplier_MDL".format(base_name)
		direction_multiplier_mdl = cmds.createNode("multDoubleLinear", name=direction_multiplier_mdl_name)
		cmds.setAttr("{}.input1".format(direction_multiplier_mdl), multiplier_direction_value)
		cmds.connectAttr("{}.output".format(direction_mdl), "{}.input2".format(direction_multiplier_mdl))

		# multiply with output
		output_mdl_name = "{}LocalPosition_MDL".format(base_name)
		output_mdl = cmds.createNode("multDoubleLinear", name=output_mdl_name)
		cmds.connectAttr(multiplier_plug, "{}.input1".format(output_mdl))
		cmds.connectAttr("{}.output".format(direction_multiplier_mdl), "{}.input2".format(output_mdl))

		# multiply output with user multipliers
		md_name = "{}LocalPosition_MD".format(base_name)
		md = cmds.createNode("multiplyDivide", name=md_name)
		for a in AXIS:
			cmds.connectAttr("{}.output".format(output_mdl), "{}.input1{}".format(md, a.upper()))
			cmds.connectAttr("{}.pac_helper_multiplier_{}".format(joint, a), "{}.input2{}".format(md, a.upper()))

		pma_name = "{}LocalPosition_PMA".format(base_name)
		pma = cmds.createNode("plusMinusAverage", name=pma_name)
		cmds.connectAttr(local_pos_plug, "{}.input3D[0]".format(pma))
		cmds.connectAttr("{}.output".format(md), "{}.input3D[1]".format(pma))
		cmds.connectAttr("{}.output".format(direction_mdl), "{}.input3D[2].input3D{}".format(pma, direction_axis))

		# compose matrix
		cm_name = "{}Output_CM".format(base_name)
		cm = cmds.createNode("composeMatrix", name=cm_name)
		cmds.connectAttr("{}.output3D".format(pma), "{}.inputTranslate".format(cm))

		# get parent matrix plug
		child_matrix_plug = "{}.worldMatrix".format(self.node)
		parent_matrix_plug = self.get_parent_matrix_plug()

		# get matrix match
		offset_matrix = self.get_matrix_rotation_match(
			child_matrix_plug,
			parent_matrix_plug
		)

		# mult matrix
		mm_name = "{}Output_MM".format(base_name)
		mm = cmds.createNode("multMatrix", name=mm_name)
		cmds.connectAttr("{}.outputMatrix".format(cm), "{}.matrixIn[0]".format(mm))
		cmds.setAttr("{}.matrixIn[1]".format(mm), list(offset_matrix.inverse()), type="matrix")
		cmds.connectAttr(parent_matrix_plug, "{}.matrixIn[2]".format(mm))
		cmds.connectAttr("{}.parentInverseMatrix".format(joint), "{}.matrixIn[3]".format(mm))

		# decompose matrix
		dm_name = "{}Output_DM".format(base_name)
		dm = cmds.createNode("decomposeMatrix", name=dm_name)
		cmds.connectAttr("{}.matrixSum".format(mm), "{}.inputMatrix".format(dm))

		# connect to joint
		cmds.connectAttr("{}.outputTranslate".format(dm), "{}.translate".format(joint))
		cmds.connectAttr("{}.outputRotate".format(dm), "{}.jointOrient".format(joint))
		cmds.connectAttr("{}.outputScale".format(dm), "{}.scale".format(joint))

		return HelperJoint(joint)


class HelperJoint(object):
	"""
	The helper joint is simply a class that exposes the helper attributes.
	This means that by calling the help function on this class it will become
	clear which attributes can be read and set on the joint node. The class
	can also be used to extract all of the pac helper attributes and their
	values.

	:param str node:
	"""

	def __init__(self, node):
		# variables
		self._node = node

	# ------------------------------------------------------------------------

	def _get_attr(self, attr):
		"""
		:param str attr:
		:return: Attribute value
		:rtype: float
		:raise ValueError: When the attribute doesn't exist on the node
		"""
		path = "{}.{}".format(self.node, attr)
		if not cmds.objExists(path):
			raise ValueError("Node '{}' doesn't have an attribute '{}'!".format(self.node, attr))

		return cmds.getAttr(path)

	def _set_attr(self, attr, value):
		"""
		:param str attr:
		:param str value:
		:raise ValueError: When the attribute doesn't exist on the node
		"""
		path = "{}.{}".format(self.node, attr)
		if not cmds.objExists(path):
			raise ValueError("Node '{}' doesn't have an attribute '{}'!".format(self.node, attr))

		cmds.setAttr(path, value)

	# ------------------------------------------------------------------------

	@property
	def node(self):
		"""
		:return: Node
		:rtype: str
		"""
		return self._node

	def get_data(self):
		"""
		:return: Attribute and value for storing
		:rtype: dict
		"""
		return {
			"pac_helper_radius": self.get_radius(),
			"pac_helper_min_rotation": self.get_min_rotation(),
			"pac_helper_max_rotation": self.get_max_rotation(),
			"pac_helper_multiplier_x": self.get_multiplier_x(),
			"pac_helper_multiplier_y": self.get_multiplier_y(),
			"pac_helper_multiplier_z": self.get_multiplier_z(),
		}

	# ------------------------------------------------------------------------

	def get_radius(self):
		"""
		:return: Radius
		:rtype: float
		"""
		return self._get_attr("pac_helper_radius")

	def set_radius(self, radius):
		"""
		:param float/int radius:
		"""
		self._set_attr("pac_helper_radius", radius)

	# ------------------------------------------------------------------------

	def get_min_rotation(self):
		"""
		:return: Min rotation
		:rtype: float
		"""
		return self._get_attr("pac_helper_min_rotation")

	def set_min_rotation(self, min_rotation):
		"""
		:param float/int min_rotation:
		"""
		self._set_attr("pac_helper_min_rotation", min_rotation)

	def get_max_rotation(self):
		"""
		:return: Radius
		:rtype: float
		"""
		return self._get_attr("pac_helper_max_rotation")

	def set_max_rotation(self, max_rotation):
		"""
		:param float/int max_rotation:
		"""
		self._set_attr("pac_helper_max_rotation", max_rotation)

	def set_rotation_range(self, min_rotation, max_rotation):
		"""
		:param float/int min_rotation:
		:param float/int max_rotation:
		"""
		self.set_min_rotation(min_rotation)
		self.set_max_rotation(max_rotation)

	# ------------------------------------------------------------------------

	def get_multiplier_x(self):
		"""
		:return: Multiplier X
		:rtype: float
		"""
		return self._get_attr("pac_helper_multiplier_x")

	def set_multiplier_x(self, multiplier_x):
		"""
		:param float/int multiplier_x:
		"""
		self._set_attr("pac_helper_multiplier_x", multiplier_x)

	def get_multiplier_y(self):
		"""
		:return: Multiplier Y
		:rtype: float
		"""
		return self._get_attr("pac_helper_multiplier_y")

	def set_multiplier_y(self, multiplier_y):
		"""
		:param float/int multiplier_y:
		"""
		self._set_attr("pac_helper_multiplier_y", multiplier_y)

	def get_multiplier_z(self):
		"""
		:return: Multiplier Z
		:rtype: float
		"""
		return self._get_attr("pac_helper_multiplier_z")

	def set_multiplier_z(self, multiplier_z):
		"""
		:param float/int multiplier_z:
		"""
		self._set_attr("pac_helper_multiplier_z", multiplier_z)

	def set_multiplier(self, multiplier_x, multiplier_y, multiplier_z):
		"""
		:param float/int multiplier_x:
		:param float/int multiplier_y:
		:param float/int multiplier_z:
		"""
		self.set_multiplier_x(multiplier_x)
		self.set_multiplier_y(multiplier_y)
		self.set_multiplier_z(multiplier_z)

	# ------------------------------------------------------------------------

	radius = property(get_radius, set_radius)
	min_rotation = property(get_min_rotation, set_min_rotation)
	max_rotation = property(get_max_rotation, set_max_rotation)
	multiplier_x = property(get_multiplier_x, set_multiplier_x)
	multiplier_y = property(get_multiplier_y, set_multiplier_y)
	multiplier_z = property(get_multiplier_z, set_multiplier_z)
