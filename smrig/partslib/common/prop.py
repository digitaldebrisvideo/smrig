import logging

from maya import cmds
from smrig import dataio
from smrig import env
from smrig import partslib
from smrig.build import guide
from smrig.build import rig
from smrig.build import skeleton
from smrig.lib import constraintslib
from smrig.lib import selectionlib
from smrig.lib import spaceslib
from smrig.lib import transformslib
from smrig.lib import utilslib
from smrig.lib.constantlib import VISIBILITY_CONTROL, MODEL_GROUP, CACHE_SET, GUIDE_GRP

log = logging.getLogger("smrig.prop")


def build_guide(geo=None, fit_controls=True):
	"""
	Create simple prop guide

	:param geo:
	:param fit_controls:
	:return:
	"""
	cog = partslib.build_guide("cog")

	geo = cmds.ls(utilslib.conversion.as_list(geo))
	if geo:
		tmp = transformslib.xform.match_locator(geo)
		transformslib.xform.match(tmp, cog.guide_group)
		cmds.delete(tmp)

		if fit_controls:
			suffix = env.prefs.get_suffix("animControl")
			bb = cmds.exactWorldBoundingBox(geo, ii=1)
			scale = round(utilslib.distance.get(bb[:3], bb[3:]), 3) / 3.464

			cmds.xform(VISIBILITY_CONTROL, s=[scale * 0.3] * 3)
			cmds.xform(VISIBILITY_CONTROL, t=[0, bb[4] + scale, 0])

			cmds.xform("C_world_" + suffix, "C_cog_" + suffix, s=[scale * 0.8] * 3)


def build_rig(geo, asset_name=None, bind_method="Matrix Constraint"):
	"""
	Build simple prop rig and bind

	:param geo:
	:param asset_name:
	:param bind_method:
	:return:
	"""
	save_to_asset = True if asset_name else False

	geo = cmds.ls(utilslib.conversion.as_list(geo))
	suffix = env.prefs.get_suffix("joint")

	if save_to_asset:
		env.assets.create_asset(asset_name)
		env.asset.set_asset(asset_name)
		guide.save_from_build_options()

	skeleton.build()
	partslib.build_rigs()
	rig.connect_parent_drivers()
	rig.connect_attribute_drivers()
	spaceslib.build_all_spaces()

	cmds.parent(geo, MODEL_GROUP)
	rig.populate_sets()

	rig.lock_control_group_hierarchy()
	rig.parent_constraint_noxform()
	rig.set_historical_interest()
	rig.set_visibility_defaults()
	cmds.delete(GUIDE_GRP)

	shapes = selectionlib.get_children(geo, all_descendents=True)
	shapes = [s for s in shapes if selectionlib.get_shapes(s)]

	cmds.sets(shapes, add=CACHE_SET)

	if bind_method == "Matrix Constraint":
		for g in geo:
			con = constraintslib.matrix_constraint("C_cog_" + suffix, g)
			if save_to_asset:
				dataio.save_to_asset("matrixConstraint", node=con)
	else:
		for g in shapes:
			scls = cmds.skinCluster("C_cog_" + suffix, g, tsb=True, n=g + "_" + env.prefs.get_suffix("skinCluster"))

			if save_to_asset:
				dataio.save_to_asset("skinCluster", node=scls[0])

	if save_to_asset:
		log.info("Saved build to asset: " + asset_name)
