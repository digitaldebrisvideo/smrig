# -*- smrig: part  -*-
import logging

from maya import cmds
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

log = logging.getLogger("smrig.partslib.wing")


class Wing(basepart.Basepart):
    """
    wing rig part module.
    """

    BUILD_LAST = False

    pri_feathers = None
    pri_jnts = None
    pricv_feathers = None
    pricv_jnts = None
    al_feathers = None
    al_jnts = None
    sec_feathers = None
    sec_jnts = None
    seccv_feathers = None
    seccv_jnts = None
    margcv_feathers = None
    margcv_jnts = None

    def __init__(self, *guide_node, **options):
        super(Wing, self).__init__(*guide_node, **options)

        self.register_option("side", "string", "L")
        self.register_option("name", "string", "")
        self.register_option("parent", "parent_driver", "L_shoulder_JNT", value_required=True)
        self.register_option("numPrimaryFeathers", "int", 10, min=3, value_required=True)
        self.register_option("numSecondaryFeathers", "int", 16, min=3, value_required=True)

        self.register_option("primaryFeatherGeo", "single_selection", "smrig_primaryFeather")
        self.register_option("secondaryFeatherGeo", "single_selection", "smrig_secondaryFeather")
        self.register_option("primaryCovertsFeatherGeo", "single_selection", "smrig_primaryCovertsFeather")
        self.register_option("secondaryCovertsFeatherGeo", "single_selection", "smrig_secondaryCovertsFeather")
        self.register_option("alulaFeatherGeo", "single_selection", "smrig_aulaFeather")
        self.register_option("marginalCovertsFeatherGeo", "single_selection", "smrig_marginalCovertsFeather")

        self.register_option("primaryOffset", "float", 0.0, value_required=True, min=0)
        self.register_option("primaryAngle", "float", 8.0, value_required=True, min=0)
        self.register_option("secondaryOffset", "float", 0.0, value_required=True, min=0)
        self.register_option("secondaryAngle", "float", 8.0, value_required=True, min=0)
        self.register_option("primaryCovertsOffset", "float", 0.05, value_required=True, min=0)
        self.register_option("primaryCovertsAngle", "float", 6.0, value_required=True, min=0)
        self.register_option("secondaryCovertsOffset", "float", 0.06, value_required=True, min=0)
        self.register_option("secondaryCovertsAngle", "float", 6.0, value_required=True, min=0)
        self.register_option("alulaOffset", "float", 0.1, value_required=True, min=0)
        self.register_option("alulaAngle", "float", 4.0, value_required=True, min=0)
        self.register_option("marginalCovertsOffset", "float", 0.12, value_required=True, min=0)
        self.register_option("marginalCovertsAngle", "float", 4.0, value_required=True, min=0)

    @property
    def parent(self):
        return self.options.get("parent").get("value")

    @property
    def numPrimaryFeathers(self):
        return self.options.get("numPrimaryFeathers").get("value")

    @property
    def numSecondaryFeathers(self):
        return self.options.get("numSecondaryFeathers").get("value")

    # geo properties -------------------------------------------------------------

    @property
    def primaryFeatherGeo(self):
        return self.options.get("primaryFeatherGeo").get("value")

    @property
    def secondaryFeatherGeo(self):
        return self.options.get("secondaryFeatherGeo").get("value")

    @property
    def primaryCovertsFeatherGeo(self):
        return self.options.get("primaryCovertsFeatherGeo").get("value")

    @property
    def secondaryCovertsFeatherGeo(self):
        return self.options.get("secondaryCovertsFeatherGeo").get("value")

    @property
    def alulaFeatherGeo(self):
        return self.options.get("alulaFeatherGeo").get("value")

    @property
    def marginalCovertsFeatherGeo(self):
        return self.options.get("marginalCovertsFeatherGeo").get("value")

    @property
    def all_feather_geo(self):
        return [self.primaryFeatherGeo,
                self.secondaryFeatherGeo,
                self.primaryCovertsFeatherGeo,
                self.secondaryCovertsFeatherGeo,
                self.alulaFeatherGeo,
                self.marginalCovertsFeatherGeo]

    # offset and angle properties -------------------------------------------------------------

    @property
    def primaryOffset(self):
        return self.options.get("primaryOffset").get("value")

    @property
    def primaryAngle(self):
        return self.options.get("primaryAngle").get("value")

    @property
    def secondaryOffset(self):
        return self.options.get("secondaryOffset").get("value")

    @property
    def secondaryAngle(self):
        return self.options.get("secondaryAngle").get("value")

    @property
    def primaryCovertsOffset(self):
        return self.options.get("primaryCovertsOffset").get("value")

    @property
    def primaryCovertsAngle(self):
        return self.options.get("primaryCovertsAngle").get("value")

    @property
    def secondaryCovertsOffset(self):
        return self.options.get("secondaryCovertsOffset").get("value")

    @property
    def secondaryCovertsAngle(self):
        return self.options.get("secondaryCovertsAngle").get("value")

    @property
    def alulaOffset(self):
        return self.options.get("alulaOffset").get("value")

    @property
    def alulaAngle(self):
        return self.options.get("alulaAngle").get("value")

    @property
    def marginalCovertsOffset(self):
        return self.options.get("marginalCovertsOffset").get("value")

    @property
    def marginalCovertsAngle(self):
        return self.options.get("marginalCovertsAngle").get("value")

    def build_guide(self):
        """
        This method holds the actual guide build code for part.

        Guide build properties and functions

        :return: None
        :rtype: None
        """

        # Create mainbuild wing joints and controls
        placers = self.create_placers("wing", num_placers=5)
        joints = self.create_joint_chain("wing", num_joints=5, placer_drivers=placers,
                                         constraints=["pointConstraint", "aimConstraint"])
        ctrls = self.create_controls("wing", num=4, drivers=joints[:-1], shape="cube", color=self.primary_color)

        flap_ctrl = self.create_control(["wing", "flap"], driver=joints[-1], shape="diamond",
                                        color=self.secondary_color)
        flap_base_ctrl = self.create_control(["wing", "flap", "base"], driver=joints[-2], shape="lollipop",
                                             color=self.secondary_color)

        up_plc = self.create_placer(["wing", "upv"])
        cmds.xform(up_plc, t=[0, 0, -4])

        cmds.xform(placers[1], t=[4, 0, -2], ws=True)
        cmds.xform(placers[2], t=[8, 0, 0], ws=True)
        cmds.xform(placers[3], t=[10, 0, 0], ws=True)
        cmds.xform(placers[4], t=[25, 0.0, -5], ws=True)

        attributeslib.set_attributes(self.guide_geometry_group, ["t", "r"], lock=False, keyable=True)
        cmds.pointConstraint(joints[0], self.guide_geometry_group)

        aim = 1 if self.mirror_value > 0 else 1
        up = -1 if self.mirror_value > 0 else 1

        cmds.aimConstraint(joints[-1],
                           self.guide_geometry_group,
                           wuo=up_plc.path,
                           aim=[aim, 0, 0],
                           u=[0, 0, up],
                           wut="object")

        # create primary curve placer
        targets = [[8.0, 0.0, 0.0], [9.0, 0.0, 0.167], [10.683, 0.0, -0.101], [11.917, -0.024, -0.292]]
        self.create_curve_guides("primary", targets, "lightblue")

        targets = [[7.982, 0.0, -1.063], [8.945, 0.0, -1.319], [10.783, 0.0, -1.409], [12.882, 0.0, -0.631]]
        self.create_curve_guides("alula", targets, "lightblue")

        targets = [[8.0, 0.0, -4.0], [10.415, 0.0, -4.216], [14.642, 0.0, -3.977], [18.37, 0.0, -2.499]]
        self.create_curve_guides("primaryCoverts", targets, "lightblue")

        targets = [[8.0, 0.0, -8.0], [11.754, 0.0, -8.273], [18.852, 0.0, -7.884], [25.076, 0.0, -4.67]]
        self.create_curve_guides("primaryTip", targets, "lightblue")

        targets = [[-0.489, 0.0, 0.225], [2.892, -0.089, -1.376], [4.749, -0.12, -1.649], [8.835, 0.136, 0.421]]
        self.create_curve_guides("secondary", targets, "turquoise")

        targets = [[0.0, 0.0, -3.269], [2.435, -0.13, -4.545], [6.853, -0.253, -4.612], [8.745, 0.059, -1.019]]
        self.create_curve_guides("marginalCoverts", targets, "turquoise")

        targets = [[0.0, 0.0, -6.452], [1.733, -0.13, -7.033], [6.09, -0.253, -6.174], [9.39, 0.059, -3.624]]
        self.create_curve_guides("secondaryCoverts", targets, "turquoise")

        targets = [[0.0, 0.0, -10.0], [1.724, -0.13, -10.48], [7.045, -0.253, -10.305], [11.386, 0.009, -6.995]]
        self.create_curve_guides("secondaryTip", targets, "turquoise")

        for geo in self.all_feather_geo:
            if not cmds.objExists(geo) and not cmds.objExists("{}:{}".format(utilslib.scene.STASH_NAMESPACE, geo)):
                self.load_default_feather_geo()
                break

    def load_default_feather_geo(self):
        """

        :return:
        """
        model.load_default_feather_geo()
        cmds.parent("|smrig_featherGeo_tmp_GRP1", "layout_GRP")

    def create_curve_guides(self, name="", targets=[], color=None):
        """

        :param name:
        :return:
        """
        crv_name = self.format_name(["wing", name], node_type="nurbsCurve")
        crv = geometrylib.curve.create_curve_from_points(targets, name=crv_name, degree=3, periodic=False)
        cmds.parent(crv, self.guide_geometry_group)
        cidx = colorlib.get_color_index_from_name(color)
        colorlib.set_color(crv, color)

        return crv

    def build_wing_geo(self):
        """
        This creates the wing geo with bound joints . Use this to shape your wing geo for the actual model.
        Rememeber to run finalize_wing_geo once everything is laid out.

        :return:
        """

        # primary
        tip_crv = self.format_name(["wing", "primaryTip"], node_type="nurbsCurve")
        self.pri_feathers, self.pri_jnts = model.build_feather_section_geo(
            [self.side, self.name, 'wing', 'primary'],
            self.format_name(["wing", "primary"], node_type="nurbsCurve"),
            self.format_name(["wing", "primaryTip"], node_type="nurbsCurve"),
            aim_crv=None,
            feather_geo=self.primaryFeatherGeo,
            num_feathers=self.numPrimaryFeathers,
            num_joints=6,
            offset=self.primaryOffset,
            angle=self.primaryAngle * self.mirror_value)

        # primary coverts
        self.pricv_feathers, self.pricv_jnts = model.build_feather_section_geo(
            [self.side, self.name, 'wing', 'primaryCoverts'],
            self.format_name(["wing", "primary"], node_type="nurbsCurve"),
            self.format_name(["wing", "primaryCoverts"], node_type="nurbsCurve"),
            aim_crv=tip_crv,
            feather_geo=self.primaryCovertsFeatherGeo,
            num_feathers=self.numPrimaryFeathers,
            num_joints=6,
            offset=self.primaryCovertsOffset,
            angle=self.primaryCovertsAngle * self.mirror_value)

        # alula
        self.al_feathers, self.al_jnts = model.build_feather_section_geo(
            [self.side, self.name, 'wing', 'alula'],
            self.format_name(["wing", "primary"], node_type="nurbsCurve"),
            self.format_name(["wing", "alula"], node_type="nurbsCurve"),
            aim_crv=tip_crv,
            feather_geo=self.alulaFeatherGeo,
            num_feathers=self.numPrimaryFeathers,
            num_joints=6,
            offset=self.alulaOffset,
            angle=self.alulaAngle * self.mirror_value)

        # secondary
        tip_crv = self.format_name(["wing", "secondaryTip"], node_type="nurbsCurve")
        self.sec_feathers, self.sec_jnts = model.build_feather_section_geo(
            [self.side, self.name, 'wing', 'secondary'],
            self.format_name(["wing", "secondary"], node_type="nurbsCurve"),
            self.format_name(["wing", "secondaryTip"], node_type="nurbsCurve"),
            aim_crv=None,
            feather_geo=self.secondaryFeatherGeo,
            num_feathers=self.numSecondaryFeathers,
            num_joints=6,
            offset=self.secondaryOffset,
            angle=self.secondaryAngle * self.mirror_value)

        self.seccv_feathers, self.seccv_jnts = model.build_feather_section_geo(
            [self.side, self.name, 'wing', 'secondaryCoverts'],
            self.format_name(["wing", "secondary"], node_type="nurbsCurve"),
            self.format_name(["wing", "secondaryCoverts"], node_type="nurbsCurve"),
            aim_crv=tip_crv,
            feather_geo=self.secondaryCovertsFeatherGeo,
            num_feathers=self.numSecondaryFeathers,
            num_joints=6,
            offset=self.secondaryCovertsOffset,
            angle=self.secondaryCovertsAngle * self.mirror_value)

        self.margcv_feathers, self.margcv_jnts = model.build_feather_section_geo(
            [self.side, self.name, 'wing', 'marginalCoverts'],
            self.format_name(["wing", "secondary"], node_type="nurbsCurve"),
            self.format_name(["wing", "marginalCoverts"], node_type="nurbsCurve"),
            aim_crv=tip_crv,
            feather_geo=self.marginalCovertsFeatherGeo,
            num_feathers=self.numSecondaryFeathers,
            num_joints=6,
            offset=self.marginalCovertsOffset,
            angle=self.marginalCovertsAngle * self.mirror_value)

    def finalize_wing_geo(self):
        """
        This copies the covert and alula feather weights to the primary feathers,
        also the marginal and secondary coverts tothe secondary feathers.
        Also removes those extras joints chains

        :return:
        """
        # copy weights to mainbuild joints
        [cmds.delete(c, ch=True) for c in self.pricv_feathers + self.al_feathers]

        for sgeo, targets in zip(self.pri_feathers, self.pricv_feathers):
            deformlib.skincluster.copy_bind(sgeo, targets)

        for sgeo, targets in zip(self.pri_feathers, self.al_feathers):
            deformlib.skincluster.copy_bind(sgeo, targets)

        cmds.delete(selectionlib.get_parent(self.pricv_jnts[0]))
        cmds.delete(selectionlib.get_parent(self.al_jnts[0]))

        # secondary -----------------

        # copy weights to mainbuild joints
        [cmds.delete(c, ch=True) for c in self.seccv_feathers + self.margcv_feathers]

        for sgeo, targets in zip(self.sec_feathers, self.seccv_feathers):
            deformlib.skincluster.copy_bind(sgeo, targets)

        for sgeo, targets in zip(self.sec_feathers, self.margcv_feathers):
            deformlib.skincluster.copy_bind(sgeo, targets)

        cmds.delete(selectionlib.get_parent(self.seccv_jnts[0]))
        cmds.delete(selectionlib.get_parent(self.margcv_jnts[0]))

    def build_rig(self):
        """

        :return: None
        :rtype: None
        """
        names = [self.format_name(["wing", i + 1], node_type="animControl") for i in range(4)]
        wing_jnts = [self.format_name(["wing", i + 1], node_type="joint") for i in range(4)]
        wing_ctrls = self.create_control_chain_from_guide(names)

        for ctrl, jnt in zip(wing_ctrls, wing_jnts):
            cmds.parentConstraint(ctrl.last_node, jnt, mo=True)

        # get surfs and end points
        pri_crv = self.get_guide_node(self.format_name(["wing", "primary"], node_type="nurbsCurve"))
        pri_tip_crv = self.get_guide_node(self.format_name(["wing", "primaryTip"], node_type="nurbsCurve"))
        sec_crv = self.get_guide_node(self.format_name(["wing", "secondary"], node_type="nurbsCurve"))
        sec_tip_crv = self.get_guide_node(self.format_name(["wing", "secondaryTip"], node_type="nurbsCurve"))
        cmds.xform(pri_crv, pri_tip_crv, sec_crv, sec_tip_crv, r=1, s=[1, 0, 1])

        pri_tip_pts = [p[:-1] for p in geometrylib.curve.get_uniform_points_on_curve(pri_tip_crv, 4)]
        sec_tip_pts = [p[:-1] for p in geometrylib.curve.get_uniform_points_on_curve(sec_tip_crv, 4)]

        # get start points ----------------------------------------------------------------------------
        start = cmds.xform(wing_jnts[2], q=1, ws=1, t=1)
        end = cmds.xform(wing_jnts[3], q=1, ws=1, t=1)
        pri_pts = [start,
                   mathlib.get_point_between(start, end, 0.333),
                   mathlib.get_point_between(start, end, 0.666),
                   end]

        start = cmds.xform(wing_jnts[1], q=1, ws=1, t=1)
        end = cmds.xform(wing_jnts[2], q=1, ws=1, t=1)
        sec_pts = [cmds.xform(wing_jnts[0], q=1, ws=1, t=1),
                   start,
                   mathlib.get_point_between(start, end, 0.5),
                   end]

        # Create ctrls ----------------------------------------------------------------------------
        pri1_ctrls = self.build_flap_ctrls("primary", 1, pri_pts[0], pri_tip_pts[0])
        pri2_ctrls = self.build_flap_ctrls("primary", 2, pri_pts[1], pri_tip_pts[1])
        pri3_ctrls = self.build_flap_ctrls("primary", 3, pri_pts[2], pri_tip_pts[2])
        pri4_ctrls = self.build_flap_ctrls("primary", 4, pri_pts[3], pri_tip_pts[3])

        sec1_ctrls = self.build_flap_ctrls("secondary", 1, sec_pts[0], sec_tip_pts[0])
        sec2_ctrls = self.build_flap_ctrls("secondary", 2, sec_pts[1], sec_tip_pts[1])
        sec3_ctrls = self.build_flap_ctrls("secondary", 3, sec_pts[2], sec_tip_pts[2])
        sec4_ctrls = self.build_flap_ctrls("secondary", 4, sec_pts[3], sec_tip_pts[3])

        # connect parents and blends ----------------------------------------------------------------------------
        self.parent_blend_flap_ctrls(sec1_ctrls[0],
                                     parent=wing_ctrls[0],
                                     blend0=wing_ctrls[0].groups[-1],
                                     blend1=wing_ctrls[0],
                                     blend_value=1)

        self.parent_blend_flap_ctrls(sec2_ctrls[0],
                                     parent=wing_ctrls[0],
                                     blend0=wing_ctrls[0].last_node,
                                     blend1=wing_ctrls[1].last_node,
                                     blend_value=0.5)

        self.parent_blend_flap_ctrls(sec3_ctrls[0],
                                     parent=wing_ctrls[1],
                                     blend0=wing_ctrls[1].last_node,
                                     blend1=wing_ctrls[2].last_node,
                                     blend_value=0.5)

        self.parent_blend_flap_ctrls(sec4_ctrls[0],
                                     parent=wing_ctrls[1],
                                     blend0=wing_ctrls[1].last_node,
                                     blend1=wing_ctrls[2].last_node,
                                     blend_value=1)

        # pri ctrls ---------------------------------------------
        self.parent_blend_flap_ctrls(pri1_ctrls[0],
                                     parent=wing_ctrls[2],
                                     blend0=wing_ctrls[1].last_node,
                                     blend1=wing_ctrls[2].last_node,
                                     blend_value=1)

        self.parent_blend_flap_ctrls(pri2_ctrls[0],
                                     parent=wing_ctrls[2],
                                     blend0=wing_ctrls[2].last_node,
                                     blend1=wing_ctrls[3].last_node,
                                     blend_value=0.333)

        self.parent_blend_flap_ctrls(pri3_ctrls[0],
                                     parent=wing_ctrls[2],
                                     blend0=wing_ctrls[2].last_node,
                                     blend1=wing_ctrls[3].last_node,
                                     blend_value=0.666)

        self.parent_blend_flap_ctrls(pri4_ctrls[0],
                                     parent=wing_ctrls[2],
                                     blend0=wing_ctrls[2].last_node,
                                     blend1=wing_ctrls[3].last_node,
                                     blend_value=1)

        # create surfs ----------------------------------------------------------------------------
        ori0 = self.create_node("transform", name=["wing", "flap", "secondary", 0, "ori"], p=sec4_ctrls[0].last_node)
        transformslib.xform.match(pri2_ctrls[0].last_node, ori0, translate=True)

        name = self.format_name(["wing", "secondary", 1], node_type="nurbsSurface")
        sec1_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          axis="y",
                                                          width=utilslib.distance.get(start, end) * 0.2,
                                                          targets=[sec1_ctrls[0].last_node,
                                                                   sec2_ctrls[0].last_node,
                                                                   sec3_ctrls[0].last_node,
                                                                   sec4_ctrls[0].last_node,
                                                                   ori0])

        ori0 = self.create_node("transform", name=["wing", "flap", "secondary", 1, "ori"], p=sec4_ctrls[1].last_node)
        transformslib.xform.match(pri2_ctrls[1].last_node, ori0, translate=True)

        name = self.format_name(["wing", "secondary", 2], node_type="nurbsSurface")
        sec2_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          axis="y",
                                                          width=utilslib.distance.get(start, end) * 0.2,
                                                          targets=[sec1_ctrls[1].last_node,
                                                                   sec2_ctrls[1].last_node,
                                                                   sec3_ctrls[1].last_node,
                                                                   sec4_ctrls[1].last_node,
                                                                   ori0])

        ori0 = self.create_node("transform", name=["wing", "flap", "secondary", 2, "ori"], p=sec4_ctrls[2].last_node)
        transformslib.xform.match(pri2_ctrls[2].last_node, ori0, translate=True)

        name = self.format_name(["wing", "secondary", 3], node_type="nurbsSurface")
        sec3_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          axis="y",
                                                          width=utilslib.distance.get(start, end) * 0.2,
                                                          targets=[sec1_ctrls[2].last_node,
                                                                   sec2_ctrls[2].last_node,
                                                                   sec3_ctrls[2].last_node,
                                                                   sec4_ctrls[2].last_node,
                                                                   ori0])

        # primary ---------------
        ori0 = self.create_node("transform", name=["wing", "flap", "primary", 0, "ori"], p=pri1_ctrls[0].last_node)
        ori1 = self.create_node("transform", name=["wing", "flap", "primary", 1, "ori"], p=pri1_ctrls[0].last_node)
        ori2 = self.create_node("transform", name=["wing", "flap", "primary", 2, "ori"], p=pri2_ctrls[0].last_node)
        ori3 = self.create_node("transform", name=["wing", "flap", "primary", 3, "ori"], p=pri3_ctrls[0].last_node)
        ori4 = self.create_node("transform", name=["wing", "flap", "primary", 4, "ori"], p=pri4_ctrls[0].last_node)
        transformslib.xform.match(ori0, [ori1, ori2, ori3, ori4], translate=False, rotate=True)
        transformslib.xform.match(sec3_ctrls[0].last_node, ori0, translate=True)

        name = self.format_name(["wing", "primary", 1], node_type="nurbsSurface")
        pri1_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          axis="y",
                                                          width=utilslib.distance.get(start, end) * 0.2,
                                                          targets=[ori0,
                                                                   ori1,
                                                                   ori2,
                                                                   ori3,
                                                                   ori4])

        ori0 = self.create_node("transform", name=["wing", "flap", "primary", 1, "ori"], p=pri1_ctrls[1].last_node)
        transformslib.xform.match(sec3_ctrls[1].last_node, ori0, translate=True)

        name = self.format_name(["wing", "primary", 2], node_type="nurbsSurface")
        pri2_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          axis="y",
                                                          width=utilslib.distance.get(start, end) * 0.2,
                                                          targets=[ori0,
                                                                   pri1_ctrls[1].last_node,
                                                                   pri2_ctrls[1].last_node,
                                                                   pri3_ctrls[1].last_node,
                                                                   pri4_ctrls[1].last_node])

        ori0 = self.create_node("transform", name=["wing", "flap", "primary", 2, "ori"], p=pri1_ctrls[2].last_node)
        transformslib.xform.match(sec3_ctrls[2].last_node, ori0, translate=True)

        name = self.format_name(["wing", "primary", 3], node_type="nurbsSurface")
        pri3_surf = geometrylib.nurbs.create_surface_link(name=name,
                                                          parent=self.noxform_group,
                                                          axis="y",
                                                          width=utilslib.distance.get(start, end) * 0.2,
                                                          targets=[ori0,
                                                                   pri1_ctrls[2].last_node,
                                                                   pri2_ctrls[2].last_node,
                                                                   pri3_ctrls[2].last_node,
                                                                   pri4_ctrls[2].last_node])

        # Build feather joint rings ----------------------------------------------------
        pri_joint_chains, sec_joint_chains = self.parent_feather_joints(wing_jnts[0])

        for chain in pri_joint_chains:
            self.build_feather_rig(chain, pri1_surf, pri2_surf, pri3_surf, self.get_rig_group())

        for chain in sec_joint_chains:
            self.build_feather_rig(chain, sec1_surf, sec2_surf, sec3_surf, self.get_rig_group())

        # cleanup -------------------------------------------------------------------------
        cmds.parent(wing_ctrls[0].groups[-1], self.get_control_group())

        for ct in wing_ctrls:
            attributeslib.set_attributes(ct.all_controls, ["t", "s"], lock=True, keyable=False)

        for ct in [pri1_ctrls, pri2_ctrls, pri3_ctrls, pri4_ctrls]:
            attributeslib.set_attributes([ct[0].path, ct[1].path, ct[2].path], ["s"], lock=True, keyable=False)

        for ct in [sec1_ctrls, sec2_ctrls, sec3_ctrls, sec4_ctrls]:
            attributeslib.set_attributes([ct[0].path, ct[1].path, ct[2].path], ["s"], lock=True, keyable=False)

    def build_flap_ctrls(self, name, index, start, end):
        """

        :return:
        """
        ref_base_ctrl = self.format_name(["wing", "flap", "base"], node_type="animControl")
        ref_ctrl = self.format_name(["wing", "flap"], node_type="animControl")

        cname = self.format_name(["wing", name, index, "flap", "base"], node_type="animControl")
        ct1 = self.create_control_from_guide(cname, ref_ctrl=ref_base_ctrl)

        cname = self.format_name(["wing", name, index, "flap", 1], node_type="animControl")
        ct2 = self.create_control_from_guide(cname, ref_ctrl=ref_ctrl)

        cname = self.format_name(["wing", name, index, "flap", 2], node_type="animControl")
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

    def parent_blend_flap_ctrls(self, ctrl, parent, blend0, blend1, blend_value):
        """

        :param ctrl:
        :param parent:
        :param blend0:
        :param blend1:
        :param blend_value:
        :return:
        """
        cmds.parent(ctrl.groups[-1], parent)
        ori0_grp = cmds.duplicate(ctrl.groups[-1], po=True, n=ctrl.groups[-1] + "_ori0_offset_GRP")[0]
        ori1_grp = cmds.duplicate(ctrl.groups[-1], po=True, n=ctrl.groups[-1] + "_ori1_offset_GRP")[0]

        ori0 = cmds.duplicate(ctrl.groups[-1], po=True, n=ctrl.groups[-1] + "_ori0_GRP")[0]
        ori1 = cmds.duplicate(ctrl.groups[-1], po=True, n=ctrl.groups[-1] + "_ori1_GRP")[0]

        cmds.parent(ori0_grp, ori1_grp, w=1)
        cmds.parent(ori0, ori0_grp)
        cmds.parent(ori1, ori1_grp)
        cmds.parent(ori0_grp, blend0)
        cmds.parent(ori1_grp, blend1)

        oc = cmds.orientConstraint(ori0, ori1, ctrl.groups[-2], mo=True)[0]
        cmds.setAttr(oc + ".interpType", 2)

        cmds.addAttr(ctrl.path, ln="blendOrient", min=0, max=1, k=1, dv=blend_value)
        attributeslib.connection.reverse_connection(ctrl.path + ".blendOrient", oc + ".w0")
        cmds.connectAttr(ctrl.path + ".blendOrient", oc + ".w1")

    def parent_feather_joints(self, parent):
        """

        :param parent:
        :return:
        """
        sgrp = self.get_guide_node(self.format_name(["wing", "primary", "feathers", "joints"], node_type="transform"))
        pri_fjnts_grp = cmds.duplicate(sgrp)

        sgrp = self.get_guide_node(self.format_name(["wing", "secondary", "feathers", "joints"], node_type="transform"))
        sec_fjnts_grp = cmds.duplicate(sgrp)

        parent_gep = self.create_node("transform", name=["wing", "feather", "joints"], p=parent)
        cmds.parent(pri_fjnts_grp[0], sec_fjnts_grp[0], parent_gep)

        jnts = selectionlib.get_children(pri_fjnts_grp[0], all_descendents=False)
        pri_joint_chains = [selectionlib.get_children(j, all_descendents=True) + [j] for j in jnts]
        [lst.reverse() for lst in pri_joint_chains]

        jnts = selectionlib.get_children(sec_fjnts_grp[0], all_descendents=False)
        sec_joint_chains = [selectionlib.get_children(j, all_descendents=True) + [j] for j in jnts]
        [lst.reverse() for lst in sec_joint_chains]

        return pri_joint_chains, sec_joint_chains

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
