import maya.cmds as cmds
from smrig.env import prefs
from smrig.lib import attributeslib
from smrig.lib import colorlib
from smrig.lib import constraintslib
from smrig.lib import controlslib
from smrig.lib import geometrylib
from smrig.lib import nodeslib
from smrig.lib import transformslib
from smrig.lib import utilslib

TAG_PLACER = "smrigGuidePlacer"
TAG_JOINT = "smrigGuideJoint"
TAG_CONTROL_PIVOT = "smrigGuideControlPivot"
TAG_CONTROL = "smrigGuideControl"
PLACER_SUFFIX = prefs.get_suffix("jointPlacer")


class GuideMixin(object):
	"""
	This is a mixin for adding guide build, mirrorpart, duplicate and other functionality to a part module.
	"""
	side = ""
	name = ""
	guide_group = None
	guide_control_group = None
	guide_placer_group = None
	guide_joint_group = None
	guide_geometry_group = None
	error_message = "This is a mixin that should not be run on its own. Use basepart.py instead."

	def __init__(self):
		pass

	# Placeholder functions --------------------------------------------------------------------------------------

	def format_name(self, *args, **kwargs):
		"""
		Placeholder for format node name function in basepart.

		:param args:
		:param kwargs:
		:return:
		"""
		raise RuntimeError(self.error_message)

	def create_node(self, *args, **kwargs):
		"""
		Placeholder for format node name function in basepart.

		:param args:
		:param kwargs:
		:return:
		"""
		raise RuntimeError(self.error_message)

	# Guide placer functions --------------------------------------------------------------------------------------

	def create_placer(self,
	                  name,
	                  side=None,
	                  translate=None,
	                  rotate=None,
	                  num_groups=2,
	                  display_handle=False):
		"""
		Create a joint placer

		:param name:
		:param side:
		:param translate:
		:param rotate:
		:param num_groups:
		:param display_handle:
		:return:
		:rtype: :class:`smrig.lib.controlslib.common.Control`
		"""
		name = self.format_name(name, side=side)

		placer = controlslib.create_control(
			name,
			self.name,
			translate=translate,
			rotate=rotate,
			num_groups=num_groups,
			control_type="jointPlacer")

		parent = placer.groups[0]
		cmds.delete(placer.path)
		cmds.createNode("joint", n=placer.path, p=parent)
		cmds.setAttr(placer.path + ".segmentScaleCompensate", 0)

		attributeslib.tag.add_tag_attribute(placer.path, controlslib.common.TAG)
		attributeslib.tag.add_tag_attribute(placer.path, controlslib.common.TAG_GROUPS, num_groups)
		attributeslib.tag.add_tag_attribute(placer.path, controlslib.common.TAG_SHAPE, "joint")
		attributeslib.tag.add_tag_attribute(placer.path, TAG_PLACER)

		color = colorlib.get_color_index_from_name("darkpurple")
		nodeslib.display.set_display_color(placer.path, color)

		cmds.setAttr("{}.radius".format(placer.path), 1.1, k=0, cb=0)
		cmds.setAttr("{}.displayHandle".format(placer.path), display_handle)

		attributeslib.set_attributes(placer.path, ["v"], lock=True, keyable=False)
		attributeslib.set_attributes(placer.groups, ["v"], lock=True, keyable=False)

		if self.guide_group and cmds.objExists(self.guide_group):
			cmds.parent(placer.groups[-1], self.guide_placer_group)

		return placer

	def create_placers(self,
	                   name,
	                   side=None,
	                   translate=None,
	                   rotate=None,
	                   num_groups=2,
	                   num_placers=3,
	                   display_handle=False):
		"""
		Create joint placers

		:param name:
		:param side:
		:param translate:
		:param rotate:
		:param num_groups:
		:param num_placers:
		:param display_handle:
		:return:
		"""
		name = utilslib.conversion.as_list(name)
		placers = []
		for idx in range(1, num_placers + 1, 1):
			placers.append(self.create_placer(name + [idx],
			                                  side=side,
			                                  translate=translate,
			                                  rotate=rotate,
			                                  num_groups=num_groups,
			                                  display_handle=display_handle))

		return placers

	def create_placer_chain(self,
	                        name,
	                        side=None,
	                        translate=None,
	                        rotate=None,
	                        num_groups=2,
	                        num_placers=3,
	                        display_handle=False):
		"""
		Create joint placer chain

		:param name:
		:param side:
		:param translate:
		:param rotate:
		:param num_groups:
		:param num_placers:
		:param display_handle:
		:return:
		"""
		placers = self.create_placers(name,
		                              side=side,
		                              translate=translate,
		                              rotate=rotate,
		                              num_groups=num_groups,
		                              num_placers=num_placers,
		                              display_handle=display_handle)
		if len(placers) > 1:
			for i, placer, in enumerate(placers):
				if i:
					cmds.parent(placer.groups[-1], placers[i - 1].path)

		return placers

	# Guide joint functions --------------------------------------------------------------------------------------

	def create_joint(self,
	                 name=None,
	                 side=None,
	                 placer_driver=None,
	                 constraints="parentConstraint",
	                 maintain_offset=False,
	                 parent=None,
	                 use_placer_name=False):
		"""
		Create a guide joint

		:param name:
		:param side:
		:param placer_driver:
		:param str/list constraints:
		:param maintain_offset:
		:param parent:
		:param use_placer_name:
		:return:
		"""
		parent = parent if parent else self.guide_joint_group
		joint = self.create_node("joint",
		                         name,
		                         side=side,
		                         generate_new_index=False,
		                         parent=parent)

		if placer_driver and use_placer_name:
			joint = cmds.rename(joint, placer_driver.path.replace("PLC", "JNT"))

		cmds.setAttr(joint + ".segmentScaleCompensate", 0)

		if self.guide_group and cmds.objExists(self.guide_group):
			attributeslib.tag.add_tag_attribute(joint, TAG_JOINT)
			cmds.connectAttr("{}.jointDisplayLocalAxis".format(self.guide_group), "{}.displayLocalAxis".format(joint))

		if placer_driver:
			constraints = [c for c in utilslib.conversion.as_list(constraints) if c]

			for constraint in constraints:
				con_name = "{}_{}".format(joint, prefs.get_suffix(constraint))

				if constraint == "pointConstraint":
					cmds.pointConstraint(placer_driver, joint, mo=maintain_offset, n=con_name)

				elif constraint == "orientConstraint":
					cmds.orientConstraint(placer_driver, joint, mo=maintain_offset, n=con_name)

				elif constraint == "parentConstraint":
					cmds.parentConstraint(placer_driver, joint, mo=maintain_offset, n=con_name)

				elif constraint == "scaleConstraint":
					cmds.scaleConstraint(placer_driver, joint, mo=maintain_offset, n=con_name)

		return joint

	def create_joints(self,
	                  name=None,
	                  side=None,
	                  placer_drivers=None,
	                  constraints="parentConstraint",
	                  maintain_offset=False,
	                  parent=None,
	                  use_placer_name=False,
	                  num_joints=3,
	                  *args,
	                  **kwargs):
		"""
		Create multiple guide joints.

		:param name:
		:param side:
		:param placer_drivers:
		:param constraints:
		:param maintain_offset:
		:param parent:
		:param use_placer_name:
		:param num_joints:
		:param args:
		:param kwargs:
		:return:
		"""
		name = utilslib.conversion.as_list(name)
		placer_drivers = utilslib.conversion.as_list(placer_drivers)
		placer_drivers = placer_drivers if placer_drivers else [None] * num_joints
		constraints = utilslib.conversion.as_list(constraints)

		joints = []
		for idx in range(1, num_joints + 1, 1):
			joints.append(self.create_joint(name=name + [idx],
			                                side=side,
			                                placer_driver=placer_drivers[idx - 1],
			                                constraints=constraints,
			                                maintain_offset=maintain_offset,
			                                use_placer_name=use_placer_name,
			                                parent=parent))

		if "aimConstraint" in constraints:
			if "mirror_value" not in kwargs.keys():
				kwargs["mirror_value"] = self.mirror_value
			constraintslib.aim_constraint_chain(placer_drivers, joints, *args, **kwargs)

		return joints

	def create_joint_chain(self,
	                       name,
	                       side=None,
	                       placer_drivers=None,
	                       constraints="parentConstraint",
	                       maintain_offset=False,
	                       parent=None,
	                       use_placer_name=False,
	                       num_joints=3,
	                       *args,
	                       **kwargs):
		"""
		Create chain of guide joints

		:param name:
		:param side:
		:param placer_drivers:
		:param constraints:
		:param maintain_offset:
		:param parent:
		:param use_placer_name:
		:param num_joints:
		:param args:
		:param kwargs:
		:return:
		"""
		joints = self.create_joints(name,
		                            side=side,
		                            placer_drivers=placer_drivers,
		                            constraints=constraints,
		                            maintain_offset=maintain_offset,
		                            parent=parent,
		                            use_placer_name=use_placer_name,
		                            num_joints=num_joints,
		                            *args,
		                            **kwargs)

		if len(joints) > 1:
			for i, joint, in enumerate(joints):
				if i:
					cmds.parent(joint, joints[i - 1])

		return joints

	def create_control(self,
	                   name,
	                   side=None,
	                   shape=None,
	                   color=None,
	                   axis="y",
	                   scale=1,
	                   translate=None,
	                   rotate=None,
	                   driver=None,
	                   constraints="parentConstraint",
	                   maintain_offset=False,
	                   locked_pivot_attrs=None,
	                   create_offset_controls=True,
	                   num_offset_controls=0,
	                   translate_cvs=None,
	                   rotate_cvs=None):
		"""
		Create a reference anim control.

		:param name:
		:param side:
		:param shape:
		:param color:
		:param axis:
		:param scale:
		:param translate:
		:param rotate:
		:param driver:
		:param constraints:
		:param maintain_offset:
		:param locked_pivot_attrs:
		:param create_offset_controls:
		:param num_offset_controls:
		:param translate_cvs:
		:param rotate_cvs:
		:return:
		"""
		ctrl_name = self.format_name(name, side=side)

		ctrl = controlslib.create_control(
			name=ctrl_name,
			generate_new_index=False,
			num_groups=0,
			translate=translate,
			rotate=rotate,
			shape=shape,
			color=color,
			scale=scale,
			num_offset_controls=4 if create_offset_controls else 0,
			axis=axis)

		pivot = controlslib.create_control(
			name=ctrl_name,
			generate_new_index=False,
			num_groups=0,
			translate=translate,
			rotate=rotate,
			shape="axis",
			axis="y",
			color=color,
			scale=1,
			control_type="animControlPivot")

		pivot_grp = cmds.createNode("transform", n="{}_{}".format(pivot.path, prefs.get_suffix("transform")))
		cmds.parent(pivot.path, pivot_grp)
		cmds.parent(ctrl.path, pivot.path)

		cmds.addAttr(ctrl.path, ln="mirrorMode", at="enum", en="TRS:TR:T", k=1)
		cmds.setAttr("{}.{}".format(ctrl.path, controlslib.common.TAG_GROUPS), 2)

		nodeslib.display.set_display_color(pivot.shapes[0], 13, shapes_only=True)
		nodeslib.display.set_display_color(pivot.shapes[1], 14, shapes_only=True)
		nodeslib.display.set_display_color(pivot.shapes[2], 6, shapes_only=True)

		attributeslib.tag.add_tag_attribute(pivot.path, TAG_CONTROL_PIVOT)
		attributeslib.tag.add_tag_attribute(ctrl.path, TAG_CONTROL)

		locked_pivot_attrs = locked_pivot_attrs if locked_pivot_attrs else []
		attributeslib.set_attributes(pivot.path, locked_pivot_attrs, lock=True, keyable=False)
		attributeslib.set_attributes([ctrl.path, pivot.path], ["v"], lock=True, keyable=False)

		if create_offset_controls:
			cmds.addAttr(ctrl.path, ln="numOffsetControls", at="long", dv=num_offset_controls, k=1, min=0, max=4)

			for idx, offset_control in enumerate(ctrl.offset_controls):
				cmds.setAttr("{}.{}".format(offset_control.path, controlslib.common.TAG_GROUPS), 2 + idx)
				attributeslib.tag.add_tag_attribute(offset_control.path, TAG_CONTROL)

				cnd = cmds.createNode("condition", n="{}_CND".format(offset_control.path))
				cmds.connectAttr("{}.numOffsetControls".format(ctrl.path), "{}.firstTerm".format(cnd))
				cmds.setAttr("{}.secondTerm".format(cnd), idx + 1)
				cmds.setAttr("{}.operation".format(cnd), 3)
				cmds.setAttr("{}.colorIfTrueR".format(cnd), 1)
				cmds.setAttr("{}.colorIfFalseR".format(cnd), 0)
				cmds.setAttr("{}.ihi".format(cnd), 0)

				cmds.setAttr("{}.v".format(offset_control.path), l=0)
				cmds.connectAttr("{}.outColorR".format(cnd), "{}.v".format(offset_control.path))
				attributeslib.set_attributes(offset_control.path, ["v"], lock=True, keyable=False)

		if translate:
			transformslib.xform.match(translate, pivot.groups[-1], pivot=True, rotate=False)

		if rotate:
			transformslib.xform.match(rotate, pivot.groups[-1], translate=False, rotate=True)

		if driver:
			constraints = [c for c in utilslib.conversion.as_list(constraints) if c]

			for constraint in constraints:

				con_name = "{}_{}".format(pivot_grp, prefs.get_suffix(constraint))

				if constraint == "pointConstraint":
					cmds.pointConstraint(driver, pivot_grp, mo=maintain_offset, n=con_name)

				elif constraint == "orientConstraint":
					cmds.orientConstraint(driver, pivot_grp, mo=maintain_offset, n=con_name)

				elif constraint == "parentConstraint":
					cmds.parentConstraint(driver, pivot_grp, mo=maintain_offset, n=con_name)

				elif constraint == "scaleConstraint":
					cmds.scaleConstraint(driver, pivot_grp, mo=maintain_offset, n=con_name)

		if self.guide_group and cmds.objExists(self.guide_group):
			cmds.parent(ctrl.groups[-1], self.guide_control_group)
			for shape in pivot.shapes:
				cmds.connectAttr(self.guide_group + ".controlDisplayLocalAxis", shape + ".v")

		if translate_cvs:
			cmds.xform("{}.cv[*]".format(ctrl.path), r=1, ro=translate_cvs)

		if rotate_cvs:
			cmds.xform("{}.cv[*]".format(ctrl.path), r=1, ro=rotate_cvs)

		return ctrl

	def create_controls(self,
	                    name,
	                    side=None,
	                    drivers=None,
	                    num=3,
	                    translates=None,
	                    rotates=None,
	                    shape=None,
	                    color=None,
	                    axis="y",
	                    scale=1,
	                    constraints="parentConstraint",
	                    maintain_offset=False,
	                    locked_pivot_attrs=None,
	                    create_offset_controls=True,
	                    num_offset_controls=0):
		"""
		Create multiple controls

		:param name:
		:param side:
		:param drivers:
		:param num:
		:param translates:
		:param rotates:
		:param shape:
		:param color:
		:param axis:
		:param scale:
		:param constraints:
		:param maintain_offset:
		:param locked_pivot_attrs:
		:param create_offset_controls:
		:param num_offset_controls:
		:return:
		"""
		name = utilslib.conversion.as_list(name)
		drivers = utilslib.conversion.as_list(drivers)
		drivers = drivers if drivers else [None] * num

		translates = utilslib.conversion.as_list(translates)
		translates = translates if translates else [None] * num

		rotates = utilslib.conversion.as_list(rotates)
		rotates = rotates if rotates else [None] * num

		joints = []
		for idx in range(1, num + 1, 1):
			joints.append(self.create_control(name + [idx],
			                                  side=side,
			                                  shape=shape,
			                                  color=color,
			                                  axis=axis,
			                                  scale=scale,
			                                  translate=translates[idx - 1],
			                                  rotate=rotates[idx - 1],
			                                  driver=drivers[idx - 1],
			                                  constraints=constraints,
			                                  maintain_offset=maintain_offset,
			                                  locked_pivot_attrs=locked_pivot_attrs,
			                                  create_offset_controls=create_offset_controls,
			                                  num_offset_controls=num_offset_controls))
		return joints

	def create_guide_surface(self, name, width=8, length_ratio=1):
		"""
		Create a mirrorable guide nurbs surface surface.

		:param name:
		:param width:
		:param length_ratio:
		:return:
		"""
		surf = self.format_name(name, node_type="nurbsSurface")
		surf = cmds.nurbsPlane(ax=[0, 0, 1], u=4, v=4, w=width, lr=length_ratio, ch=False, n=surf)[0]
		surf = geometrylib.nurbs.rebuild_surface(surf)

		geometrylib.nurbs.assign_ribbon_shader(surf)
		cmds.addAttr(surf, ln="rbGuideSurface", at="message")
		cmds.parent(surf, self.guide_geometry_group)

		return surf
