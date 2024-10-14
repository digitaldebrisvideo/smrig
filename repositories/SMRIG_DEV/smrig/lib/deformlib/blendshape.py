import maya.cmds as cmds
import maya.mel as mel
from smrig.dataio.types import skin_cluster
from smrig.lib import attributeslib
from smrig.lib import naminglib
from smrig.lib.deformlib import wrap

suffix = naminglib.get_suffix("blendShape")


def get_shape_targets(blendshape):
	"""

	:param blendshape:
	:return:
	"""
	targets = []
	for i in range(len(cmds.blendShape(blendshape, q=1, w=1))):
		trg = cmds.listAttr("{}.weight[{}]".format(blendshape, i), sn=True)[0]
		if cmds.objExists("{}.{}".format(blendshape, trg)):
			targets.append(trg)

	return targets

def get_selected_targets():
	"""
	query selected target shapes selected from shape editor
	:return:
	"""
	targets = mel.eval ("getShapeEditorTreeviewSelection(4)")
	selected_targets = []
	for target in targets:
		split = target.split (".")
		selected_targets.append (split[0] + "." + (cmds.aliasAttr (target, split[0] + ".w[" + split[1] + "]", q=1)))
	return (selected_targets)

def get_target_index(blendshape, name):
	"""

	:param blendshape:
	:param name:
	:return:
	"""
	count = cmds.blendShape(blendshape, q=True, wc=True) * 3
	for idx in range(count):
		if cmds.aliasAttr("{}.w[{}]".format(blendshape, idx), q=True) == name:
			return idx


def zero_targets(blendshape):
	"""

	:param blendshape:
	:return:
	"""
	for trg in get_shape_targets(blendshape):
		cmds.setAttr("{}.{}".format(blendshape, trg), 0)


def extract_targets(source_geo, blendshape):
	"""

	:param source_geo:
	:param blendshape:
	:return:
	"""
	targets = get_shape_targets(blendshape)
	zero_targets(blendshape)

	cmds.setAttr("{}.envelope".format(blendshape), 1)

	for trg in targets:
		cmds.setAttr("{}.{}".format(blendshape, trg), 1)
		new_trg = cmds.duplicate(source_geo, n=trg)[0]
		cmds.parent(new_trg, w=1)
		cmds.setAttr("{}.{}".format(blendshape, trg), 0)


def copy_blendshape(source_geo, target_geo, blendshape, create_blendshape=True, connect_to_source=True,
                    keep_targets=False):
	"""

	:param source_geo:
	:param target_geo:
	:param blendshape:
	:return:
	"""
	targets = get_shape_targets(blendshape)
	zero_targets(blendshape)

	cmds.setAttr("{}.envelope".format(blendshape), 1)

	tmp = cmds.duplicate(target_geo)[0]
	tmp_wrap = wrap.create(source_geo, tmp)
	new_trgs = []

	grp = cmds.createNode("transform", n="shapes_GRP")
	for trg in targets:
		cmds.setAttr("{}.{}".format(blendshape, trg), 1)
		new_trg = cmds.duplicate(tmp, n=trg)[0]
		cmds.setAttr("{}.{}".format(blendshape, trg), 0)

		attributeslib.set_attributes(new_trg, ["t", "r", "s"], lock=False, keyable=True)
		cmds.parent(new_trg, grp)
		new_trgs.append(new_trg)

	new_bs = None
	cmds.delete(tmp, tmp_wrap)
	if create_blendshape:
		new_bs = cmds.blendShape(new_trgs, target_geo, n="{}_{}".format(target_geo, suffix), automatic=True)[0]
		for trg in targets:
			cmds.setAttr("{}.{}".format(new_bs, trg), 1)

		cmds.refresh()
		cmds.dgdirty(a=True)

		for trg in targets:
			cmds.setAttr("{}.{}".format(new_bs, trg), 0)

			if connect_to_source:
				cmds.connectAttr("{}.{}".format(blendshape, trg), "{}.{}".format(new_bs, trg))

		if not keep_targets:
			cmds.delete(grp)

	return new_bs, targets


def get_dag_name(name):
	"""

	:param name:
	:return:
	"""
	sel_list = MSelectionList()
	MGlobal.getSelectionListByName(name, sel_list)

	if sel_list.length() > 0:
		obj = MDagPath()
		sel_list.getDagPath(0, obj)

		return obj


def copy_target_weights(src_mesh, dest_mesh, src_deformer, dest_deformer, src_target, dest_target, mirror=False):
	"""

	:param src_mesh: source mesh
	:param dest_mesh: destination mesh
	:param src_deformer: source blendshape node
	:param dest_deformer: destination blendshape node
	:param src_target: source target name
	:param dest_target: destinaton target name
	:param mirror:
	:return:
	"""
	sidx = get_target_index(src_deformer, src_target)
	src_attr = "it[0].itg[{}].tw".format(sidx)

	didx = get_target_index(src_deformer, dest_target)
	dest_attr = "it[0].itg[{}].tw".format(didx)

	if src_deformer == dest_deformer and src_mesh == dest_mesh and not mirror:  # do nothing when copy to itself
		return

	print("{} from '{}.{}' to '{}.{}'".format("Mirror" if mirror else "Copy", src_deformer, src_attr, dest_deformer,
	                                          dest_attr))

	dest_points = MPointArray()
	dest_mesh_fn = MFnMesh(get_dag_name(dest_mesh))
	dest_mesh_fn.getPoints(dest_points, MSpace.kWorld)

	src_mesh_fn = MFnMesh(get_dag_name(src_mesh))
	mesh_intersector = MMeshIntersector()

	src_mesh_path = get_dag_name(src_mesh)
	src_mesh_path.extendToShape()

	mesh_intersector.create(src_mesh_path.node(), src_mesh_path.inclusiveMatrix())

	src_attr_py = core.PyNode("{}.{}".format(src_deformer, src_attr))
	src_attr_values = [0] * src_mesh_fn.numVertices()
	for i, k in zip(src_attr_py.getArrayIndices(), src_attr_py.get()):
		src_attr_values[i] = k

	script_util = MScriptUtil()

	weights = [0] * dest_points.length()
	for i in range(dest_points.length()):
		mirror_point = MPoint(dest_points[i])

		if mirror:
			if dest_points[i].x > 0:
				continue

			mirror_point.x *= -1

		pm = MPointOnMesh()
		mesh_intersector.getClosestPoint(mirror_point, pm)

		script_util.createFromInt(0, 0, 0, 0)
		vertices3 = script_util.asIntPtr()

		src_mesh_fn.getPolygonTriangleVertices(pm.faceIndex(), pm.triangleIndex(), vertices3)

		u = floatPtr()
		v = floatPtr()
		pm.getBarycentricCoords(u, v)
		u = u.value()
		v = v.value()

		w = 1 - u - v
		# -----------
		v1 = script_util.getIntArrayItem(vertices3, 0)
		v2 = script_util.getIntArrayItem(vertices3, 1)
		v3 = script_util.getIntArrayItem(vertices3, 2)

		weights[i] = src_attr_values[v1] * u + src_attr_values[v2] * v + src_attr_values[v3] * w

	for i in range(dest_points.length()):
		if mirror and src_deformer == dest_deformer and dest_points[i].x > 0:
			continue

		cmds.setAttr("{}.{}[{}]".format(dest_deformer, dest_attr, i), weights[i])


class SplitShapes(object):
	def __init__(self, grp=None):
		"""
		Geo must have a bs node attatched ot it to initialize.

		:param split_node:
		"""
		self.grp = grp if grp else cmds.ls(sl=1)[0]
		if not cmds.objExists(self.grp + "."):
			raise IOError("Selection is not a split shapes group")

		self.name = cmds.getAttr(self.grp + ".name")
		self.geo = cmds.getAttr(self.grp + ".geo")
		self.targets = eval(cmds.getAttr(self.grp + ".target"))
		self.prefixes = eval(cmds.getAttr(self.grp + ".prefixes"))
		self.splits = len(self.prefixes)

		self.bs = "{}_BSH".format(self.geo)
		self.scls = "{}_SKN".format(self.geo)
		self.s_jnts = ["{}_{}_JNT".format(p, self.geo) for p in self.prefixes]

	@classmethod
	def create(cls, geo, targets, prefixes, name=None):
		"""

		:param str geo:
		:param list targets:
		:param list prefixes:
		:param str/none name:
		:return:
		"""
		cls.name = name + "_" if name else ""
		cls.geo = cmds.duplicate(geo, n="{}{}_split".format(cls.name, geo))[0]

		cls.targets = targets
		cls.prefixes = prefixes
		cls.splits = len(cls.prefixes)
		cls.grp = cmds.createNode("transform", n="{}{}_split_GRP".format(cls.name, geo))

		cmds.parent(cls.geo, cls.grp)

		s_targets = []
		cls.s_jnts = []

		# create jnts -------------------------------------------

		for i, prefix in enumerate(cls.prefixes):
			jnt = cmds.createNode("joint", p=cls.grp, n="{}_{}_JNT".format(prefix, cls.geo))
			cls.s_jnts.append(jnt)

			for target in cls.targets:
				dup = cmds.duplicate(target, n="{}{}_{}".format(cls.name, prefix, target))
				s_targets.append(dup[0])

		cmds.parent(s_targets, cls.grp)
		cmds.hide(cls.s_jnts, s_targets)

		bs_name = "{}_BSH".format(cls.geo)
		if cmds.objExists(bs_name):
			cmds.delete(bs_name)

		cls.bs = cmds.blendShape(s_targets, cls.geo, n=bs_name)
		cls.scls = cmds.skinCluster(cls.geo, cls.s_jnts, n="{}_SKN".format(cls.geo), tsb=1)
		cmds.setAttr(cls.scls[0] + ".envelope", 0)

		cmds.addAttr(cls.grp, at="message", ln="splitBS")
		cmds.addAttr(cls.grp, ln="geo", dt="string")
		cmds.addAttr(cls.grp, ln="target", dt="string")
		cmds.addAttr(cls.grp, ln="prefixes", dt="string")
		cmds.addAttr(cls.grp, ln="name", dt="string")

		cmds.setAttr(cls.grp + ".geo", cls.geo, type="string")
		cmds.setAttr(cls.grp + ".target", str(cls.targets), type="string")
		cmds.setAttr(cls.grp + ".prefixes", str(cls.prefixes), type="string")
		cmds.setAttr(cls.grp + ".name", cls.name, type="string")

		[cmds.rename(t, t + "_TRG") for t in s_targets]
		attributeslib.set_attributes(cls.geo, ["t", "r", "s"], lock=False)
		cmds.select(cls.grp)

		return SplitShapes(cls.grp)

	def update_weights(self):
		"""

		:return:
		"""
		skn_obj = skin_cluster.SkinCluster(self.scls)
		skn_obj.get_weights()
		weights_data = skn_obj.weights

		idx = 0
		for jnt in self.s_jnts:
			wgt = weights_data.get(jnt)

			for target in self.targets:
				cmds.setAttr('{}.it[0].itg[{}].tw[0:{}]'.format(self.bs, idx, len(wgt) - 1), *wgt)
				idx += 1

			print("updated shape weights for: {} {}".format(target, jnt))

	def extract_shapes(self):
		"""

		:return:
		"""
		targets = get_shape_targets(self.bs)
		zero_targets(self.bs)

		for trg in targets:
			cmds.setAttr("{}.{}".format(self.bs, trg), 1)
			new_trg = cmds.duplicate(self.geo, n=trg.replace(self.name, ""))[0]
			cmds.setAttr("{}.{}".format(self.bs, trg), 0)
			try:
				cmds.parent(new_trg, w=1)
			except:
				pass
			print("extracted shape for: " + new_trg)

	def delete_split_setup(self):
		"""
		Delete when done

		:return:
		"""
		cmds.delete(cmds.ls(self.scls, self.bs, self.grp))
