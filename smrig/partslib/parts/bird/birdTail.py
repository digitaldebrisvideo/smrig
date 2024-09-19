# -*- smrig: part  -*-
import logging

from maya import cmds
from smrig.partslib import BIN_PATH
from smrig.partslib.common import basepart
from smrig.lib import geometrylib
from smrig.lib import colorlib
from smrig.lib import utilslib
from smrig.lib import attributeslib
from smrig.lib import selectionlib
from smrig.lib import constraintslib
from smrig.lib import deformlib
from smrig.lib import mathlib
from smrig.lib import transformslib
from smrig.lib import kinematicslib
from smrig.lib import rivetlib
from smrig.lib import constantlib
from smrig.lib.winglib import model
from smrig.lib.deformlib import wrap

import os

log = logging.getLogger("smrig.partslib.birdTail")


class BirdTail(basepart.Basepart):
    """
    birdTail rig part module.
    """

    BUILD_LAST = False

    pri_feathers = None
    pri_jnts = None
    pricv_feathers = None
    pricv_jnts = None

    def __init__(self, *guide_node, **options):
        super(BirdTail, self).__init__(*guide_node, **options)

        self.register_option("side", "string", "C")
        self.register_option("name", "string", "")
        self.register_option("parent", "parent_driver", "C_hip_JNT", value_required=True)
        self.register_option("numPrimaryFeathers", "int", 8, min=3, value_required=True)

        self.register_option("primaryFeatherGeo", "single_selection", "smrig_primaryTailFeather")
        self.register_option("primaryCovertsFeatherGeo", "single_selection", "smrig_primaryTailCovertsFeather")

        self.register_option("primaryOffset", "float", 0.0, value_required=True, min=0)
        self.register_option("primaryAngle", "float", 8.0, value_required=True, min=0)
        self.register_option("primaryCovertsOffset", "float", 0.05, value_required=True, min=0)
        self.register_option("primaryCovertsAngle", "float", 6.0, value_required=True, min=0)

    @property
    def parent(self):
        return self.options.get("parent").get("value")

    @property
    def numPrimaryFeathers(self):
        return self.options.get("numPrimaryFeathers").get("value")

    # geo properties -------------------------------------------------------------

    @property
    def primaryFeatherGeo(self):
        return self.options.get("primaryFeatherGeo").get("value")

    @property
    def primaryCovertsFeatherGeo(self):
        return self.options.get("primaryCovertsFeatherGeo").get("value")

    @property
    def all_feather_geo(self):
        return [self.primaryFeatherGeo,
                self.primaryCovertsFeatherGeo]

    # offset and angle properties -------------------------------------------------------------

    @property
    def primaryOffset(self):
        return self.options.get("primaryOffset").get("value")

    @property
    def primaryAngle(self):
        return self.options.get("primaryAngle").get("value")

    @property
    def primaryCovertsOffset(self):
        return self.options.get("primaryCovertsOffset").get("value")

    @property
    def primaryCovertsAngle(self):
        return self.options.get("primaryCovertsAngle").get("value")

    def build_guide(self):
        """
        This method holds the actual guide build code for part.

        Guide build properties and functions

        :return: None
        :rtype: None
        """
        # Create main wing joints and controls
        placers = self.create_placers("tail", num_placers=2)
        joints = self.create_joint_chain("tail",
                                         num_joints=2,
                                         placer_drivers=placers,
                                         constraints=["pointConstraint", "aimConstraint"])

        ctrls = self.create_controls("tail",
                                     num=1,
                                     drivers=joints[:-1],
                                     shape="circle",
                                     axis="x",
                                     color=self.primary_color)

        flap_ctrl = self.create_control(["tail", "flap"],
                                        driver=joints[-1],
                                        shape="diamond",
                                        color=self.secondary_color)

        flap_base_ctrl = self.create_control(["tail", "flap", "base"],
                                             driver=joints[-2],
                                             shape="lollipop",
                                             color=self.secondary_color)

        cmds.xform(placers[1], t=[6, 0, 0], ws=True)

        attributeslib.set_attributes(self.guide_geometry_group, ["t", "r"], lock=False, keyable=True)
        cmds.pointConstraint(joints[0], self.guide_geometry_group)

        cmds.aimConstraint(joints[-1],
                           self.guide_geometry_group,
                           aim=[1, 0, 0],
                           u=[0, 1, 0],
                           wut="scene")

        # create primary curve placer
        targets = [[0.48, 0.0, 0.591], [0.61, -0.003, 0.455], [0.682, 0.0, 0.0], [0.61, -0.003, -0.455], [0.48, 0.0, -0.591]]
        self.create_curve_guides("primary", targets, "lightblue")

        targets = [[1.663, 0.0, 2.24], [2.522, 0.0, 1.613], [2.733, 0.0, 0.0], [2.522, 0.0, -1.613], [1.663, 0.0, -2.24]]
        self.create_curve_guides("primaryCoverts", targets, "lightblue")

        targets = [[3.107, 0.0, 3.979], [4.898, 0.0, 2.862], [5.81, 0.0, 0.0], [4.898, 0.0, -2.862], [3.107, 0.0, -3.979]]
        self.create_curve_guides("primaryTip", targets, "lightblue")

        for geo in self.all_feather_geo:
            if not cmds.objExists(geo) and not cmds.objExists("{}:{}".format(utilslib.scene.STASH_NAMESPACE, geo)):
                cmds.file(os.path.join(BIN_PATH, "default_tailFeather_geo.mb"), rnn=True, i=True)
                cmds.parent("|smrig_tailFeatherGeo_tmp_GRP", "guides_GRP")
                break

        cmds.xform(self.guide_group, ro=[0, 90, 0])

    def create_curve_guides(self, name="", targets=[], color=None):
        """

        :param name:
        :return:
        """
        crv_name = self.format_name(["tail", name], node_type="nurbsCurve")
        crv = geometrylib.curve.create_curve_from_points(targets, name=crv_name, degree=3, periodic=False)
        cmds.parent(crv, self.guide_geometry_group)
        cidx = colorlib.get_color_index_from_name(color)
        colorlib.set_color(crv, color)

        return crv

    def build_wing_geo(self):
        """
        This creates the wing geo with bound joints .. Use this to shape your wing geo for the actual model.
        Rememeber to run finalize_wing_geo once everything is laid out.

        :return:
        """
        # primary
        tip_crv = self.format_name(["tail", "primaryTip"], node_type="nurbsCurve")
        self.pri_feathers, self.pri_jnts = model.build_feather_section_geo(
            [self.side, self.name, 'tail', 'primary'],
            self.format_name(["tail", "primary"], node_type="nurbsCurve"),
            self.format_name(["tail", "primaryTip"], node_type="nurbsCurve"),
            aim_crv=None,
            feather_geo=self.primaryFeatherGeo,
            num_feathers=self.numPrimaryFeathers,
            num_joints=6,
            offset=self.primaryOffset,
            angle=self.primaryAngle * self.mirror_value)

        # primary coverts
        if self.primaryCovertsFeatherGeo:
            self.pricv_feathers, self.pricv_jnts = model.build_feather_section_geo(
                [self.side, self.name, 'tail', 'primaryCoverts'],
                self.format_name(["tail", "primary"], node_type="nurbsCurve"),
                self.format_name(["tail", "primaryCoverts"], node_type="nurbsCurve"),
                aim_crv=tip_crv,
                feather_geo=self.primaryCovertsFeatherGeo,
                num_feathers=self.numPrimaryFeathers,
                num_joints=6,
                offset=self.primaryCovertsOffset,
                angle=self.primaryCovertsAngle * self.mirror_value)

    def finalize_wing_geo(self):
        """
        This copies the covert and alula feather weights to the primary feathers,
        also the marginal and secondary coverts tothe secondary feathers.
        Also removes those extras joints chains

        :return:
        """
        # copy weights to main joints
        [cmds.delete(c, ch=True) for c in self.pricv_feathers]

        for sgeo, targets in zip(self.pri_feathers, self.pricv_feathers):
            deformlib.skincluster.copy_bind(sgeo, targets)

        cmds.delete(selectionlib.get_parent(self.pricv_jnts[0]))

    def build_rig(self):
        """

        :return: None
        :rtype: None
        """
        names = [self.format_name(["tail", i + 1], node_type="animControl") for i in range(1)]
        wing_jnts = [self.format_name(["tail", i + 1], node_type="joint") for i in range(1)]
        wing_ctrls = self.create_control_chain_from_guide(names)

        for ctrl, jnt in zip(wing_ctrls, wing_jnts):
            cmds.parentConstraint(ctrl.last_node, jnt, mo=True)

        # get surfs and end points
        pri_crv = self.get_guide_node(self.format_name(["tail", "primary"], node_type="nurbsCurve"))
        pri_tip_crv = self.get_guide_node(self.format_name(["tail", "primaryTip"], node_type="nurbsCurve"))
        cmds.xform(pri_crv, pri_tip_crv,  r=1, s=[1, 0, 1])

        pri_pts = [p[:-1] for p in geometrylib.curve.get_uniform_points_on_curve(pri_crv, 3)]
        pri_tip_pts = [p[:-1] for p in geometrylib.curve.get_uniform_points_on_curve(pri_tip_crv, 3)]

        # Create ctrls ----------------------------------------------------------------------------
        pri1_ctrls = self.build_flap_ctrls("primary", 1, pri_pts[0], pri_tip_pts[0])
        pri2_ctrls = self.build_flap_ctrls("primary", 2, pri_pts[1], pri_tip_pts[1])
        pri3_ctrls = self.build_flap_ctrls("primary", 3, pri_pts[2], pri_tip_pts[2])
        cmds.parent(pri1_ctrls[0].groups[-1], pri2_ctrls[0].groups[-1], pri3_ctrls[0].groups[-1], wing_ctrls[0])

        # create surfs ----------------------------------------------------------------------------
        thickness = utilslib.distance.get(pri1_ctrls[0], pri1_ctrls[1]) * 0.2

        ori0 = self.create_node("transform", name=["tail", "flap", "primary", 0, "ori"], p=pri1_ctrls[0].last_node)
        ori1 = self.create_node("transform", name=["tail", "flap", "primary", 1, "ori"], p=pri2_ctrls[0].last_node)
        ori2 = self.create_node("transform", name=["tail", "flap", "primary", 2, "ori"], p=pri3_ctrls[0].last_node)
        transformslib.xform.match(ori0, [ori1, ori2], translate=False, rotate=True)

        name = self.format_name(["tail", "primary", "drv", 1], node_type="nurbsSurface")
        pri1_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          degree=1,
                                                          axis="y",
                                                          width=thickness,
                                                          targets=[ori0,
                                                                   ori1,
                                                                   ori2])

        ori0 = self.create_node("transform", name=["tail", "flap", "primary", 0, "ori"], p=pri1_ctrls[1].last_node)
        ori1 = self.create_node("transform", name=["tail", "flap", "primary", 1, "ori"], p=pri2_ctrls[1].last_node)
        ori2 = self.create_node("transform", name=["tail", "flap", "primary", 2, "ori"], p=pri3_ctrls[1].last_node)
        transformslib.xform.match(ori0, [ori1, ori2], translate=False, rotate=True)

        name = self.format_name(["tail", "primary", "drv", 2], node_type="nurbsSurface")
        pri2_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          degree=1,
                                                          axis="y",
                                                          width=thickness,
                                                          targets=[ori0,
                                                                   ori1,
                                                                   ori2])

        ori0 = self.create_node("transform", name=["tail", "flap", "primary", 0, "ori"], p=pri1_ctrls[2].last_node)
        ori1 = self.create_node("transform", name=["tail", "flap", "primary", 1, "ori"], p=pri2_ctrls[2].last_node)
        ori2 = self.create_node("transform", name=["tail", "flap", "primary", 2, "ori"], p=pri3_ctrls[2].last_node)
        transformslib.xform.match(ori0, [ori1, ori2], translate=False, rotate=True)

        name = self.format_name(["tail", "primary", "drv", 3], node_type="nurbsSurface")
        pri3_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          degree=1,
                                                          axis="y",
                                                          width=thickness,
                                                          targets=[ori0,
                                                                   ori1,
                                                                   ori2])

        # Build feather joint rings ----------------------------------------------------
        pri_joint_chains = self.parent_feather_joints(wing_jnts[0])

        for chain in pri_joint_chains:
            self.build_feather_rig(chain, pri1_surf, pri2_surf, pri3_surf, self.get_rig_group())

        # feather attrs
        cmds.addAttr(wing_ctrls[0], ln="spread", k=1)
        cmds.addAttr(wing_ctrls[0], ln="curl", k=1)
        cmds.addAttr(wing_ctrls[0], ln="centerCurl", k=1)
        cmds.addAttr(wing_ctrls[0], ln="leftCurl", k=1)
        cmds.addAttr(wing_ctrls[0], ln="rightCurl", k=1)

        cmds.connectAttr(wing_ctrls[0].path+".spread", pri1_ctrls[0].groups[0]+".ry")
        attributeslib.connection.negative_connection(wing_ctrls[0].path+".spread", pri3_ctrls[0].groups[0]+".ry")

        for ctrl in pri1_ctrls+pri2_ctrls+pri3_ctrls:
            cmds.connectAttr(wing_ctrls[0].path + ".curl", ctrl.groups[1] + ".rx")

        for ctrl in pri1_ctrls:
            cmds.connectAttr(wing_ctrls[0].path + ".leftCurl", ctrl.groups[0] + ".rx")

        for ctrl in pri2_ctrls:
            cmds.connectAttr(wing_ctrls[0].path + ".centerCurl", ctrl.groups[0] + ".rx")

        for ctrl in pri3_ctrls:
            cmds.connectAttr(wing_ctrls[0].path + ".rightCurl", ctrl.groups[0] + ".rx")

        # cleanup -------------------------------------------------------------------------
        cmds.parent(wing_ctrls[0].groups[-1], self.get_control_group())

        for ct in wing_ctrls:
            attributeslib.set_attributes(ct.all_controls, ["t", "s"], lock=True, keyable=False)

        for ct in [pri1_ctrls, pri2_ctrls, pri3_ctrls]:
            attributeslib.set_attributes([ct[0].path, ct[1].path, ct[2].path], ["s"], lock=True, keyable=False)

    def build_flap_ctrls(self, name, index, start, end):
        """

        :return:
        """
        ref_base_ctrl = self.format_name(["tail", "flap", "base"], node_type="animControl")
        ref_ctrl = self.format_name(["tail", "flap"], node_type="animControl")

        cname = self.format_name(["tail", name, index, "flap", "base"], node_type="animControl")
        ct1 = self.create_control_from_guide(cname, ref_ctrl=ref_base_ctrl)

        cname = self.format_name(["tail", name, index, "flap", 1], node_type="animControl")
        ct2 = self.create_control_from_guide(cname, ref_ctrl=ref_ctrl)

        cname = self.format_name(["tail", name, index, "flap", 2], node_type="animControl")
        ct3 = self.create_control_from_guide(cname, ref_ctrl=ref_ctrl)

        cmds.xform(ct1.groups + ct2.groups + ct3.groups, a=1, t=[0, 0, 0], ro=[0, 0, 0])
        cmds.parent(ct2.groups[-1], ct1.last_node)
        cmds.parent(ct3.groups[-1], ct2.last_node)

        tmp = cmds.createNode("transform")
        cmds.xform(ct1.groups[-1], ws=True, t=start)
        cmds.xform(tmp, ws=True, t=end)

        cmds.setAttr(ct1.groups[-1] + ".sx", -1)
        cmds.delete(cmds.aimConstraint(tmp,
                                       ct1.groups[-2],
                                       aim=[0, 0, 1],
                                       u=[0, 1, 0],
                                       wut="scene"), tmp)

        cmds.xform(ct2.groups[-1], ws=True, t=mathlib.get_point_between(start, end))
        cmds.xform(ct3.groups[-1], ws=True, t=end)

        return ct1, ct2, ct3

    def parent_feather_joints(self, parent):
        """

        :param parent:
        :return:
        """
        sgrp = self.get_guide_node(self.format_name(["tail", "primary", "feathers", "joints"], node_type="transform"))
        pri_fjnts_grp = cmds.duplicate(sgrp)

        parent_gep = self.create_node("transform", name=["tail", "feather", "joints"], p=parent)
        cmds.parent(pri_fjnts_grp[0], parent_gep)

        jnts = selectionlib.get_children(pri_fjnts_grp[0], all_descendents=False)
        pri_joint_chains = [selectionlib.get_children(j, all_descendents=True) + [j] for j in jnts]
        [lst.reverse() for lst in pri_joint_chains]

        return pri_joint_chains

    def build_feather_rig(self, chain, surf1, surf2, surf3, parent):
        """

        :param chain:
        :param surf1:
        :param surf2:
        :param surf3:
        :param parent:
        :return:
        """
        pos = [cmds.xform(chain[0], q=1, ws=1, t=1), cmds.xform(chain[-1], q=1, ws=1, t=1)]
        pos.insert(1, mathlib.get_point_between(pos[0], pos[1]))

        grp1 = cmds.createNode("transform", name=chain[0] + "_start_GRP")
        grp2 = cmds.createNode("transform", name=chain[0] + "_mid_GRP")
        grp3 = cmds.createNode("transform", name=chain[0] + "_end_GRP")

        grp1_off = cmds.createNode("transform", name=chain[0] + "_start_off_GRP")
        grp2_off = cmds.createNode("transform", name=chain[0] + "_mid_off_GRP")
        grp3_off = cmds.createNode("transform", name=chain[0] + "_end_off_GRP")

        cmds.xform(grp1, grp1_off, ws=1, t=pos[0])
        cmds.xform(grp2, grp2_off, ws=1, t=pos[1])
        cmds.xform(grp3, grp3_off, ws=1, t=pos[2])

        crv = geometrylib.curve.create_curve_link([grp1, grp2, grp3], name=chain[0] + "_CRV", degree=2)
        ik_handle, crv = kinematicslib.ik.create_spline_ik_handle(chain[0], chain[-1], curve=crv)
        start_loc, end_loc = kinematicslib.ik.create_advanced_twist_locators(ik_handle)
        cmds.parent(start_loc, grp1)
        cmds.parent(end_loc, grp3)

        cmds.parent(crv, ik_handle, self.noxform_group)
        cmds.hide(ik_handle)

        rivetlib.create_surface_rivet(surf1, grp1_off, maintain_offset=False)
        rivetlib.create_surface_rivet(surf2, grp2_off, maintain_offset=False)
        rivetlib.create_surface_rivet(surf3, grp3_off, maintain_offset=False)

        cmds.parent(grp1, grp1_off)
        cmds.parent(grp2, grp2_off)
        cmds.parent(grp3, grp3_off)

        cmds.parent(grp1_off, grp2_off, grp3_off, parent)
