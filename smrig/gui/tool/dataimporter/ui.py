import logging
import os

from PySide2 import QtCore, QtWidgets
from maya import cmds

from smrig import dataioo
from smrig import env
from smrig.dataioo.utils import remap_file
from smrig.gui.mayawin import maya_main_window
from smrig.gui.widget import header
from smrig.lib import iolib

log = logging.getLogger("smrig.gui.tool.dataloader")


class DataImporter(QtWidgets.QDialog):
	file_path = None
	node_items = []

	def __init__(self, parent=maya_main_window):
		super(DataImporter, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Data Load Utility")

		layout = QtWidgets.QGridLayout(self)

		self.menu = QtWidgets.QMenuBar(self)
		self.menu.setStyleSheet("QMenuBar{background-color: rgb(58, 58, 58)}")

		action = QtWidgets.QAction(self)
		action.setText("Load Data File")
		action.triggered.connect(self.load_file)
		self.menu.addAction(action)

		self.header = header.Header(self, large=False, light_grey=True, title="", info_button=False)

		label0 = QtWidgets.QLabel("Remap Required Nodes")
		label0.setStyleSheet("QLabel{background-color: rgb(58, 58, 58); padding: 3px}")

		layout1 = QtWidgets.QGridLayout(self)
		l0 = QtWidgets.QLabel("Seah: ")
		l1 = QtWidgets.QLabel("Replace: ")

		self.seah = QtWidgets.QLineEdit()
		self.replace = QtWidgets.QLineEdit()

		layout1.addWidget(l0, 0, 0)
		layout1.addWidget(l1, 1, 0)
		layout1.addWidget(self.seah, 0, 1)
		layout1.addWidget(self.replace, 1, 1)

		layout2 = QtWidgets.QHBoxLayout()

		sbtn = QtWidgets.QPushButton("Seah && Replace Names")
		abtn = QtWidgets.QPushButton("Assign Selected Node")

		sbtn.released.connect(self.seah_replace)
		abtn.released.connect(self.assign_selected)

		layout2.addWidget(sbtn)
		layout2.addWidget(abtn)
		layout1.addLayout(layout2, 2, 0, 1, 2)

		self.tree = QtWidgets.QTreeWidget(self)
		self.tree.setColumnCount(2)
		self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
		self.tree.setAlternatingRowColors(True)
		self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.tree.setHeaderLabels(["Required Nodes", "Remapped Nodes"])

		label = QtWidgets.QLabel("Bind Method: ")
		# label.setStyleSheet("QLabel{background-color: rgb(58, 58, 58); padding: 3px}")

		self.rdo0 = QtWidgets.QRadioButton("Vertex ID")
		self.rdo1 = QtWidgets.QRadioButton("Closest Point")
		self.rdo2 = QtWidgets.QRadioButton("UV Space")
		self.rdo0.setChecked(True)

		layout3 = QtWidgets.QHBoxLayout()

		lbtn = QtWidgets.QPushButton("Load Data")
		ssbtn = QtWidgets.QPushButton("Save Asset Remap File")

		lbtn.released.connect(self.load_data)
		ssbtn.released.connect(self.save_file)

		self.chx = QtWidgets.QCheckBox("Show only unmapped nodes")
		self.chx.toggled.connect(self.toggle_unmaped)

		layout3.addWidget(ssbtn)
		layout3.addWidget(lbtn)

		layout.addWidget(self.menu, 0, 0, 1, 4)
		layout.addWidget(self.header, 1, 0, 1, 4)
		# layout.addWidget(label0, 2, 0, 1, 3)
		layout.addLayout(layout1, 3, 0, 1, 4)
		layout.addWidget(self.chx, 4, 0, 1, 4)
		layout.addWidget(self.tree, 5, 0, 1, 4)

		# layout.addWidget(label,6, 0, 1, 4)
		layout.addWidget(label, 7, 0)
		layout.addWidget(self.rdo0, 7, 1)
		layout.addWidget(self.rdo1, 7, 2)
		layout.addWidget(self.rdo2, 7, 3)

		layout.addLayout(layout3, 8, 0, 1, 4)

		self.setMinimumWidth(475)
		self.resize(475, 650)

		self.chx.setChecked(True)

	def load_file(self):
		"""

		:return:
		"""
		file_path = dataioo.utils.browser(extension="*", dir=env.asset.get_data_path())

		if not file_path:
			return

		self.file_path = file_path
		required_nodes = dataioo.get_required_nodes(self.file_path)
		required_nodes.sort()

		name = os.path.splitext(os.path.basename(file_path))[0]
		self.populate_ui(name, required_nodes=required_nodes)

	def reset_ui(self):
		"""

		:return:
		"""
		self.populate_ui("", [])

	def populate_ui(self, name, required_nodes):
		"""
		This populates the UI

		:return:
		"""

		self.header.label.setText(name)
		self.tree.clear()
		self.node_items = []

		remap_data = {}
		if os.path.isfile(remap_file):
			remap_data = iolib.json.read(remap_file)

		for node in required_nodes:
			rnode = remap_data.get(node) or node
			existing = cmds.ls(rnode)
			existing = existing[0] if existing else ""

			item = QtWidgets.QTreeWidgetItem()
			item.setText(0, node)
			item.setText(1, existing)

			self.node_items.append(item)
			self.tree.addTopLevelItem(item)

		self.toggle_unmaped()

	def toggle_unmaped(self):
		"""

		:return:
		"""
		if self.chx.isChecked():
			for item in self.node_items:
				if item.text(1):
					item.setHidden(True)

		else:
			for item in self.node_items:
				item.setHidden(False)

	def seah_replace(self):
		"""

		:return:
		"""
		items = self.tree.selectedItems()
		seah = self.seah.text().strip()
		replace = self.replace.text().strip()

		for item in items:
			new_node = cmds.ls(item.text(0).replace(search, replace, 1))
			if new_node:
				item.setText(1, new_node[0])

	def assign_selected(self):
		"""

		:return:
		"""
		items = self.tree.selectedItems()
		sel = cmds.ls(sl=1)
		if not sel:
			log.warning("Select a node in scene to remap to.")
			return

		for item in items:
			item.setText(1, sel[0])

	def get_remap_data(self):
		"""

		:return:
		"""
		remap_data = {}

		for item in self.node_items:
			remap_data[item.text(0)] = item.text(1)

		return remap_data

	def clear_remap_file(self):
		"""

		:return:
		"""
		if os.path.isfile(remap_file):
			os.remove(remap_file)

	def save_file(self, overwrite=False):
		"""

		:return:
		"""
		if os.path.isfile(remap_file) and not overwrite:
			data = iolib.json.read(remap_file)
			data.update(self.get_remap_data())

		else:
			data = self.get_remap_data()

		iolib.json.write(remap_file, data)
		log.info("Saved remap file to '{}'.".format(remap_file))

	def load_data(self):
		"""

		:return:
		"""
		remap_data = self.get_remap_data()
		remap = [[k, v] for k, v in remap_data.items()]

		if self.rdo1.isChecked():
			method = "closestPoint"

		elif self.rdo2.isChecked():
			method = "uvSpace"

		else:
			method = "vertexID"

		dataioo.load(self.file_path, method=method, remap=remap)


def run():
	"""

	:return:
	"""

	ui = DataImporter()
	ui.show()
	return ui
