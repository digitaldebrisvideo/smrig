from smrig.dataio.types import anim_shaders
from smrig.dataio.types import attribute_values
from smrig.dataio.types import blend_shape
from smrig.dataio.types import cluster
from smrig.dataio.types import connections
from smrig.dataio.types import constraints
from smrig.dataio.types import deformation_order
from smrig.dataio.types import delta_mush
from smrig.dataio.types import keyable_attributes
from smrig.dataio.types import matrix_constraints
from smrig.dataio.types import non_linear
from smrig.dataio.types import pose_interpolators
from smrig.dataio.types import set_driven_keyframe
from smrig.dataio.types import skin_cluster
from smrig.dataio.types import spaces
from smrig.dataio.types import user_defined_attributes
from smrig.dataio.types import wire
from smrig.dataio.types import wrap

modules = {
	user_defined_attributes.deformer_type: user_defined_attributes,
	pose_interpolators.deformer_type: pose_interpolators,
	non_linear.deformer_type: non_linear,
	blend_shape.deformer_type: blend_shape,
	skin_cluster.deformer_type: skin_cluster,
	cluster.deformer_type: cluster,
	delta_mush.deformer_type: delta_mush,
	deformation_order.deformer_type: deformation_order,
	constraints.deformer_type: constraints,
	connections.deformer_type: connections,
	set_driven_keyframe.deformer_type: set_driven_keyframe,
	anim_shaders.deformer_type: anim_shaders,
	keyable_attributes.deformer_type: keyable_attributes,
	spaces.deformer_type: spaces,
	attribute_values.deformer_type: attribute_values,
	matrix_constraints.deformer_type: matrix_constraints,
	wire.deformer_type: wire,
	wrap.deformer_type: wrap
}
