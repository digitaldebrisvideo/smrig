import logging
from functools import partial

import maya.cmds as cmds

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui

from smrig import dataio
from smrig import env
from smrig.gui.mayawin import maya_main_window
from smrig.gui.widget import header
from smrig.lib import constantlib
from smrig.lib import naminglib
from smrig.lib import selectionlib
from smrig.lib import utilslib

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"

log = logging.getLogger("smrig.gui.tool.dataexporter")

EXCLUDED_TYPES = ["keyableAttributes", "deformationOrder", "spaces"]
VALID_SHAPE_TYPES = ["mesh", "nurbsSurface", "nurbsCurve"]
DEFORMER_TYPES = ["skinCluster", "blendShape", "cluster", "deltaMush", "nonLinear", "ffd", "wire", "wrap", "sculpt"]

# Alias for QAction to ensure compatibility with PySide2 and PySide6
try:
	from PySide2.QtWidgets import QAction
except ImportError:
	from PySide6.QtGui import QAction as QAction


class DataExporter(QtWidgets.QDialog):
	filters = {}
	all_filter_items = []

	def __init__(self, parent=maya_main_window):
		super(DataExporter, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Guides")

		layout = QtWidgets.QVBoxLayout(self)

		# file menu ------------------------------------------------

		self.menu = QtWidgets.QMenuBar(self)
		self.menu.setStyleSheet("QMenuBar{background-color: rgb(58, 58, 58)}")

		action = QAction(self)
		action.setText("Import Deformers && Data Util")
		self.menu.addAction(action)

		# ------------------------------------------------------

		node_header = header.Header(self, large=False, light_grey=True, title="Nodes", info_button=False)
		deformer_header = header.Header(self, large=False, light_grey=True, title="Deformes & Data", info_button=False)

		filter_frame = QtWidgets.QFrame()
		filter_layout = QtWidgets.QVBoxLayout(filter_frame)
		filter_layout.setContentsMargins(0, 0, 0, 0)
		filter_layout.setSpacing(0)

		self.filter_btn = QtWidgets.QPushButton("Deformer && Data Type Filters")
		self.filter_btn.setCheckable(True)
		self.filter_btn.setMaximumHeight(18)
		self.filter_btn.toggled.connect(self.toggle_filter_frame)

		self.filter_table = QtWidgets.QTableWidget()
		self.filter_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		self.filter_table.setFocusPolicy(QtCore.Qt.NoFocus)
		self.filter_table.setStyleSheet("QTableView{background-color:rgb(55, 55, 55);}")
		self.filter_table.setMinimumHeight(192)

		filter_layout.addWidget(self.filter_btn)
		filter_layout.addWidget(self.filter_table)
		filter_layout.setStretch(0, 0)
		filter_layout.setStretch(0, 0)

		node_frame = QtWidgets.QFrame()
		node_layout = QtWidgets.QVBoxLayout(node_frame)
		node_layout.setContentsMargins(0, 0, 0, 0)
		node_layout.setSpacing(6)

		deformer_frame = QtWidgets.QFrame()
		deformer_layout = QtWidgets.QVBoxLayout(deformer_frame)
		deformer_layout.setContentsMargins(0, 0, 0, 0)
		deformer_layout.setSpacing(6)

		self.node_list = QtWidgets.QListWidget()
		self.node_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.node_list.setFocusPolicy(QtCore.Qt.NoFocus)

		self.deformer_list = QtWidgets.QListWidget()
		self.deformer_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.deformer_list.setFocusPolicy(QtCore.Qt.NoFocus)

		self.node_list.itemSelectionChanged.connect(self.list_deformers)

		list_btn = QtWidgets.QPushButton("List Selected Nodes")
		names_btn = QtWidgets.QPushButton("Fix Deformer Node Names")

		btn_layout = QtWidgets.QGridLayout()
		export_btn = QtWidgets.QPushButton("Export Deformers && Data")
		order_btn = QtWidgets.QPushButton("Export Deformation Order")
		val_btn = QtWidgets.QPushButton("Export Control Values")
		attrs_btn = QtWidgets.QPushButton("Export Keyable Attributes")

		btn_layout.addWidget(export_btn, 0, 0, 1, 3)
		btn_layout.addWidget(order_btn, 1, 0)
		btn_layout.addWidget(val_btn, 1, 1)
		btn_layout.addWidget(attrs_btn, 1, 2)

		node_layout.addWidget(node_header)
		node_layout.addWidget(self.node_list)
		node_layout.addWidget(list_btn)

		deformer_layout.addWidget(deformer_header)
		deformer_layout.addWidget(self.deformer_list)
		deformer_layout.addWidget(names_btn)

		self.splitter = QtWidgets.QSplitter(self)
		self.splitter.addWidget(node_frame)
		self.splitter.addWidget(deformer_frame)

		layout.addWidget(self.menu)
		layout.addWidget(filter_frame)
		layout.addWidget(self.splitter)
		layout.addWidget(QHLine())
		layout.addLayout(btn_layout)

		layout.setStretch(0, 0)
		layout.setStretch(1, 0)
		layout.setStretch(2, 1)
		layout.setStretch(3, 0)

		# actions & connections
		export_btn.released.connect(self.export_data)
		names_btn.released.connect(self.rename_nodes)
		attrs_btn.released.connect(self.export_control_attributes)
		val_btn.released.connect(self.export_control_values)

		list_btn.released.connect(self.list_selected_nodes)

		self.node_list.itemDoubleClicked.connect(self.node_list.selectAll)
		self.deformer_list.itemDoubleClicked.connect(self.deformer_list.selectAll)

		self.node_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		self.deformer_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		export_btn.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		list_btn.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		names_btn.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		order_btn.released.connect(self.export_deformation_order)

		action1 = QAction(self)
		action1.setText("List Model Hierahy")
		action1.triggered.connect(self.list_model_hierahy)
		list_btn.addAction(action1)

		div = QAction(self)
		div.setSeparator(True)
		list_btn.addAction(div)

		action1 = QAction(self)
		action1.setText("Add Selected Nodes to List")
		action1.triggered.connect(partial(self.list_selected_nodes, append=True))
		list_btn.addAction(action1)

		action1 = QAction(self)
		action1.setText("Fix All Deformer Node Names")
		action1.triggered.connect(partial(self.rename_nodes, rename_all=True))
		names_btn.addAction(action1)

		action1 = QAction(self)
		action1.setText("Select Nodes")
		action1.triggered.connect(partial(self.select_nodes, self.node_list))
		self.node_list.addAction(action1)

		action1 = QAction(self)
		action1.setText("Select Nodes")
		action1.triggered.connect(partial(self.select_nodes, self.deformer_list))
		self.deformer_list.addAction(action1)

		self.deformer_list.addAction(div)

		action1 = QAction(self)
		action1.setText("Add Highlighted Nodes To Nodes List")
		action1.triggered.connect(self.add_deformer_to_node_list)
		self.deformer_list.addAction(action1)

		action1 = QAction(self)
		action1.setText("Export All Deformers & Data")
		action1.triggered.connect(partial(self.export_data, export_all=True))
		export_btn.addAction(action1)

		self.populate_filters()
		self.filter_table.hide()

	@property
	def node_items(self):
		"""

		:return:
		"""
		return [self.node_list.item(i) for i in range(self.node_list.count())]

	@property
	def node_items_text(self):
		"""

		:return:
		"""
		return [i.text() for i in self.node_items]

	@property
	def deformer_items(self):
		"""

		:return:
		"""
		return [self.node_list.item(i) for i in range(self.node_list.count())]

	@property
	def deformer_items_text(self):
		"""

		:return:
		"""
		return [i.text() for i in self.deformer_items]

	def list_selected_nodes(self, append=False, nodes=None):
		"""

		:return:
		"""
		nodes = nodes if nodes else cmds.ls(sl=1)

		if append:
			nodes = [n for n in nodes if n not in self.node_items_text]

		if not nodes:
			return

		if not append:
			self.node_list.clear()

		self.node_list.addItems(nodes)

	def list_model_hierahy(self):
		"""

		:return:
		"""
		model_grp = constantlib.MODEL_GROUP
		if not cmds.objExists(model_grp):
			log.warning("{} doesnt exist in scene.".format(model_grp))
			return

		nodes = cmds.ls(selectionlib.get_children(model_grp,
		                                          full_path=True,
		                                          all_descendents=True))
		nodes.insert(0, model_grp)

		if not nodes:
			log.warning("No shapes under {}".format(model_grp))
			return

		self.list_selected_nodes(nodes=nodes)

	def select_nodes(self, list_widget):
		"""

		:param list_widget:
		:return:
		"""
		nodes = []
		for item in list_widget.selectedItems():
			node = item.text()
			if not node:
				continue

			node = node.split(":")[0] if ":" in node else node
			node = node.split("\n") if "\n" in node else node
			node = cmds.ls(node)
			nodes.extend(node)

		cmds.select(nodes)
		return nodes

	def add_deformer_to_node_list(self):
		"""

		:return:
		"""
		nodes = self.select_nodes(self.deformer_list)
		if nodes:
			self.list_selected_nodes(nodes=nodes, append=True)

	def populate_filters(self):
		"""

		:return:
		"""
		module_names = dataio.types.modules.keys()
		module_names = [n for n in module_names if n not in EXCLUDED_TYPES]
		# module_names.sort()
		sorted(module_names)

		module_names.insert(0, "All Data Types")

		module_chunks = utilslib.conversion.as_chunks(module_names, 6)
		self.filter_table.setColumnCount(len(module_chunks))
		self.filter_table.setRowCount(6)
		self.all_filter_items = []

		for ci, chunk in enumerate(module_chunks):
			for ri, module_name in enumerate(chunk):
				nice_name = naminglib.conversion.camel_case_to_nice_name(module_name)
				item = QtWidgets.QTableWidgetItem(nice_name)
				item.setCheckState(QtCore.Qt.CheckState.Checked)
				item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
				item.data_type = module_name

				self.all_filter_items.append(item)
				self.filter_table.setItem(ri, ci, item)

				if module_name != "All Data Types":
					self.filters[module_name] = True

		self.filter_table.itemChanged.connect(self.toggle_filter_state)

		self.filter_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
		self.filter_table.horizontalHeader().setVisible(False)
		self.filter_table.verticalHeader().setVisible(False)

	def toggle_filter_state(self, *args, **kwargs):
		"""

		:param item:
		:return:
		"""
		if args[0].data_type == "All Data Types":
			self.filter_table.blockSignals(True)
			check_state = args[0].checkState()

			for item in self.all_filter_items[1:]:
				item.setCheckState(check_state)
				self.filters[item.data_type] = bool(check_state)

			self.filter_table.blockSignals(False)

		else:
			for item in self.all_filter_items[1:]:
				self.filters[item.data_type] = bool(item.checkState())

		self.list_deformers()

	def toggle_filter_frame(self):
		"""

		:return:
		"""
		if self.filter_btn.isChecked():
			self.filter_table.show()
		else:
			self.filter_table.hide()

	def list_deformers(self):
		"""

		:return:
		"""
		nodes = cmds.ls([i.text() for i in self.node_list.selectedItems()])

		data_types = [k for k, v in self.filters.items() if v]
		node_data_types = [d for d in data_types if d not in ["poseInterpolators", "animShaders"]]
		data = {k: [] for k in data_types}

		for node in nodes:
			for data_type in node_data_types:
				deformers = dataio.utils.get_deformers(node, data_type, as_string=True)
				try:
					data[data_type].extend(list(set(deformers)))

				except:
					data[data_type].extend(deformers)

		if "animShaders" in data_types:
			data["animShaders"] = get_shaders()

		if "poseInterpolators" in data_types:
			data["poseInterpolators"] = get_pose_interpolators()

		ordered_list = data.keys()
		sorted(ordered_list)
		print(ordered_list)

		# if "animShaders" in ordered_list:
		#     ordered_list.remove("animShaders")
		#     ordered_list.append("animShaders")
		#
		# if "poseInterpolators" in ordered_list:
		#     ordered_list.remove("poseInterpolators")
		#     ordered_list.append("poseInterpolators")

		self.deformer_list.clear()

		for data_type in ordered_list:
			values = data.get(data_type)

			if not values:
				continue

			label_item = QtWidgets.QListWidgetItem(data_type)
			label_item.setForeground(QtCore.Qt.darkGray)
			label_item.setBackground(QtGui.QColor('#353535'))
			label_item.setFlags(label_item.flags() & ~QtCore.Qt.ItemIsSelectable)
			label_item.node = None
			label_item.data_type = None

			self.deformer_list.addItem(label_item)

			for value in values:
				item = QtWidgets.QListWidgetItem(value)
				item_node = value.split(":")[0]
				item.node = item_node
				item.data_type = data_type

				self.deformer_list.addItem(item)

			spacer_item = QtWidgets.QListWidgetItem("")
			spacer_item.setFlags(spacer_item.flags() & ~QtCore.Qt.ItemIsSelectable)
			spacer_item.node = None
			spacer_item.data_type = None

			self.deformer_list.addItem(spacer_item)

	def export_data(self, export_all=False):
		"""

		:param export_all:
		:return:
		"""
		items = self.deformer_list.selectedItems()
		items = [self.deformer_list.item(i) for i in range(self.deformer_list.count())] if export_all else items

		for item in items:
			if item.node and item.data_type:
				dataio.save_to_asset(item.data_type, node=item.node)

	def rename_nodes(self, rename_all=False):
		"""

		:param rename_all:
		:return:
		"""
		items = self.deformer_list.selectedItems()
		items = [self.deformer_list.item(i) for i in range(self.deformer_list.count())] if rename_all else items

		for item in items:
			node = item.node
			geo = None

			if not node or not cmds.objExists(node):
				continue

			if item.data_type == "constraint":
				geo = cmds.listConnections(node + ".constraintParentInverseMatrix")

			elif item.data_type == "matrixConstraint":
				geo = None

			elif item.data_type == "cluster":
				geo = [cmds.cluster(node, q=1, wn=1)]

			elif item.data_type in DEFORMER_TYPES:
				try:
					geo = cmds.deformer(node, q=True, g=True)
				except:
					geo = None

			if geo and cmds.objExists(geo[0]) and node and cmds.objExists(node):
				geo = selectionlib.get_transform(geo[0]).split("|")[-1]
				suffix = env.prefs.get_suffix(cmds.nodeType(node))

				if not suffix:
					continue

				name = "{}_{}".format(geo, suffix)
				if node != name:
					name = cmds.rename(node, "{}_{}".format(geo, suffix))
					item.node = name
					item.setText(name)

	def export_deformation_order(self):
		"""

		:return:
		"""
		nodes = [i.text() for i in self.node_list.selectedItems()]
		for node in nodes:
			dataio.save_to_asset("deformationOrder", node=node)

	def export_control_attributes(self):
		"""

		:return:
		"""
		dataio.save_to_asset("keyableAttributes")

	def export_control_values(self):
		"""

		:return:
		"""
		dataio.save_to_asset("attributeValues")


class QHLine(QtWidgets.QFrame):
	def __init__(self):
		super(QHLine, self).__init__()
		self.setFrameShape(QtWidgets.QFrame.HLine)
# self.setFrameShadow(QtWidgets.QFrame.Sunken)


def run():
	"""

	:return: Qt widget object
	"""
	ui = DataExporter()
	ui.show()
	return ui


def get_shaders():
	"""

	:return:
	"""
	excluded_nodes = ["initialParticleSE", "initialShadingGroup"]

	all_shading_engines = [s for s in cmds.ls(type="shadingEngine") if s not in excluded_nodes]
	materials = []

	for shader in all_shading_engines:
		material_connection = cmds.listConnections(shader + ".surfaceShader")

		if material_connection:
			materials.append(material_connection[0])
	if materials:
		return ["\n".join(materials)]


def get_pose_interpolators():
	"""

	:return:
	"""
	pose_nodes = [selectionlib.get_transform(p) for p in cmds.ls(type='poseInterpolator')]

	if pose_nodes:
		return ["\n".join(pose_nodes)]
