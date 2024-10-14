# -*- smrig: part  -*-
import logging

from smrig.partslib.common import basepart

log = logging.getLogger("smrig.partslib.boilerplate")


class Boilerplate(basepart.Basepart):
	"""
	boilerplate rig part module.
	"""

	BUILD_LAST = False

	def __init__(self, *guide_node, **options):
		super(Boilerplate, self).__init__(*guide_node, **options)

		self.register_option("side", "string", "L")
		self.register_option("name", "string", "")
		self.register_option("parent", "parent_driver", "C_root_JNT", value_required=True)

	def parent_skeleton(self):
		"""
		Empty function for handling custom skeleton parenting.
		Its recommended to use try statements in this one.

		:return:
		"""
		pass

	def build_guide(self):
		"""
		This method holds the actual guide build code for part.

		Guide build properties and functions
		.. code-block:: python

			self.guide_node
			self.guide_control_group
			self.guide_locator_group
			self.guide_joint_group
			self.guide_geometry_group
			self.guide_no_transform_group

			self.guide_scale_attribute
			self.mirror_value

			self.${option_name} # ie. self.side, self.name, self.parent

			self.primary_color
			self.secondary_color
			self.detail_color

			self.format_name("myNode_name_GRP") # properly format a name with side and name

		To create guide controls and control chains
		.. code-block:: python
			self.create_guide_control(shape="cube", descriptor="myControl", color=self.primary_color, scale=1.0)

		To create guide locator joints and chains
		.. code-block:: python
			self.create_joint_locator(descriptor="myJoint", constraints=["pointConstraint"])
			self.create_joint_locator_chain(num_chain=3,
											chain_locators=False,
											descriptor="myJoint",
											constraints=["pointConstraint"])

		:rtype: None
		"""
		pass

	def build_rig(self):
		"""
		This method holds the actual control rig build code for part.

		To access rig hook groups object containing groups for parenting controls, locators, joints, surfaces, no transform
		and a worldScale attribute.

		.. code-block:: python
			self.rig_groups.hook.parent.control
			self.rig_groups.hook.parent.joint
			self.rig_groups.hook.parent.driver
			self.rig_groups.no_transform
			self.rig_groups.world_scale

		To create an anim control based off a guide control
		.. code-block:: python
			self.create_control_from_guide(self.controls[0], translate=True, rotate=True, scale=False, num_offsets=1)

		To create extra/custom control sets
		.. code-block:: python
			self.create_sub_control_set("extraFK", controls)

		To create extra/custom visibility attributes.
		.. code-block:: python
			self.create_visibility_link([self.controls], attribute_name="secondaryControls", shapes_only=False, default_value=1)

		:rtype: None
		"""
		pass
