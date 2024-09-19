from smrig.dataioo.types import anim_shaders
from smrig.dataioo.types import attribute_values
from smrig.dataioo.types import blendshape
from smrig.dataioo.types import cluster
from smrig.dataioo.types import connections
from smrig.dataioo.types import deformation_order
from smrig.dataioo.types import deltamush
from smrig.dataioo.types import keyable_attributes
from smrig.dataioo.types import lattice
from smrig.dataioo.types import matrixconstraint
from smrig.dataioo.types import mayaconstraint
from smrig.dataioo.types import non_linear
from smrig.dataioo.types import poseinterpolator
from smrig.dataioo.types import proximity_wrap
from smrig.dataioo.types import sculpt
from smrig.dataioo.types import set_driven_keyframe
from smrig.dataioo.types import skincluster
from smrig.dataioo.types import spaces
from smrig.dataioo.types import user_defined_attributes
from smrig.dataioo.types import wire
from smrig.dataioo.types import wrap

modules = {
	cluster.deformer_type: cluster,
	skincluster.deformer_type: skincluster,
	mayaconstraint.deformer_type: mayaconstraint,
	matrixconstraint.deformer_type: matrixconstraint,
	blendshape.deformer_type: blendshape,
	deltamush.deformer_type: deltamush,
	poseinterpolator.deformer_type: poseinterpolator,
	attribute_values.deformer_type: attribute_values,
	deformation_order.deformer_type: deformation_order,
	connections.deformer_type: connections,
	set_driven_keyframe.deformer_type: set_driven_keyframe,
	proximity_wrap.deformer_type: proximity_wrap,
	non_linear.deformer_type: non_linear,
	lattice.deformer_type: lattice,
	anim_shaders.deformer_type: anim_shaders,
	wire.deformer_type: wire,
	wrap.deformer_type: wrap,
	sculpt.deformer_type: sculpt,
	user_defined_attributes.deformer_type: user_defined_attributes,
	keyable_attributes.deformer_type: keyable_attributes,
	spaces.deformer_type: spaces
}
