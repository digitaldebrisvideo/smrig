# -*- coding: utf-8 -*-

import operator
import os
from functools import partial

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui
from maya import cmds

from smrig.gui import mayawin
from smrig.gui.mel import prompts
from smrig.gui.widget import header
from smrig.lib import colorlib
from smrig.lib import controlslib
from smrig.lib import decoratorslib
from smrig.lib import selectionlib
from smrig.lib import utilslib

color_data = colorlib.COLOR_NAMES
color_data = sorted(color_data.items(), key=operator.itemgetter(1))

shapes_data = controlslib.library.get_control_shape_library()
icon_path = os.path.join(os.path.dirname(controlslib.__file__), "bin", "icons")

btn_size = 50
num_columns = 6

width = 326
height = 795
ctrl_ui = None


class Controls(QtWidgets.QDialog):

	def __init__(self, parent=mayawin.maya_main_window):
		super(Controls, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)
		self.setWindowTitle("sm Rig | Controls UI")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(mayawin.get_icon_path("logo.png")))

		layout = QtWidgets.QVBoxLayout(self)

		# --------------------------------------

		shapes_frame = QtWidgets.QFrame()
		shapes_layout = QtWidgets.QVBoxLayout()
		shapes_frame.setLayout(shapes_layout)
		shapes_layout.setContentsMargins(0, 0, 0, 0)

		s_header = header.Header(self, large=False, light_grey=True, title="Shapes", info_button=False)
		s_header.part_obj = None

		self.tree = QtWidgets.QTreeWidget()
		self.tree.value_items = []
		self.tree.setColumnCount(num_columns)
		self.tree.setIndentation(0)
		self.tree.header().setMinimumSectionSize(24)

		for i in range(num_columns):
			self.tree.header().resizeSection(i, btn_size)

		self.tree.header().setStretchLastSection(False)
		self.tree.setHeaderHidden(True)
		self.tree.setFocusPolicy(QtCore.Qt.NoFocus)

		style = "QTreeView{ background-color:rgb(55, 55, 55); }" \
		        "QTreeView::item{ padding:1px; } "

		self.tree.setStyleSheet(style)
		self.tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		shapes_layout.addWidget(s_header)

		btn_layout = QtWidgets.QHBoxLayout()
		bx = QtWidgets.QPushButton("Rotate X 45°")
		by = QtWidgets.QPushButton("Rotate Y 45°")
		bz = QtWidgets.QPushButton("Rotate Z 45°")

		bx.released.connect(partial(self.rotate_shape, [45, 0, 0]))
		by.released.connect(partial(self.rotate_shape, [0, 45, 0]))
		bz.released.connect(partial(self.rotate_shape, [0, 0, 45]))

		btn_layout.addWidget(bx)
		btn_layout.addWidget(by)
		btn_layout.addWidget(bz)
		shapes_layout.addLayout(btn_layout)

		shapes_layout.addWidget(self.tree)
		shapes_layout.setSpacing(11)

		# --------------------------------------

		color_frame = QtWidgets.QFrame()
		color_layout = QtWidgets.QVBoxLayout()
		color_frame.setLayout(color_layout)
		color_layout.setContentsMargins(0, 0, 0, 0)

		c_header = header.Header(self, large=False, light_grey=True, title="Colors", info_button=False)
		c_header.part_obj = None

		self.c_tree = QtWidgets.QTreeWidget()
		self.c_tree.value_items = []
		self.c_tree.setColumnCount(num_columns)
		self.c_tree.setIndentation(0)
		self.c_tree.header().setMinimumSectionSize(24)

		for i in range(num_columns):
			self.c_tree.header().resizeSection(i, btn_size)

		self.c_tree.header().setStretchLastSection(False)
		self.c_tree.setHeaderHidden(True)
		self.c_tree.setFocusPolicy(QtCore.Qt.NoFocus)

		style = "QTreeView{ background-color:rgb(55, 55, 55); }" \
		        "QTreeView::item{ padding:1px; } "

		self.c_tree.setStyleSheet(style)
		self.c_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		color_layout.addWidget(c_header)
		color_layout.addWidget(self.c_tree)
		color_layout.setSpacing(11)

		btn = QtWidgets.QPushButton("Save New Shape From Selection")
		btn.released.connect(self.save_shape)

		layout.addWidget(shapes_frame)
		layout.addWidget(btn)
		layout.addWidget(color_frame)

		self.populate_shapes()
		self.populate_colors()

		shapes_layout.setStretch(0, 0)
		shapes_layout.setStretch(1, 0)
		shapes_layout.setStretch(2, 1)

		layout.setStretch(0, 1)
		layout.setStretch(1, 0)
		layout.setStretch(2, 0)

		self.setMinimumWidth(width)
		self.setMaximumWidth(width)
		self.setMinimumHeight(height)

		self.c_tree.setMaximumHeight(310)
		self.c_tree.setMinimumHeight(310)

		self.settings = QtCore.QSettings("Saavedra_Studio", "Rig_Bot_controls")
		self.restoreGeometry(self.settings.value("geometry"))

	def save_shape(self):
		"""

		:return:
		"""
		name = prompts.prompt_dialog(title="Save Control Shape", message="Name", button=["Save", "Cancel"])
		controlslib.library.save_control_shape(name, cmds.ls(sl=1)[0], normalize=False)
		shapes_data = controlslib.library.get_control_shape_library()
		self.populate_shapes()

	def populate_shapes(self):
		"""

		:return:
		"""
		chunks = utilslib.conversion.as_chunks([[k, v] for k, v in shapes_data.items()], num_columns)
		self.tree.clear()

		for row, items in enumerate(chunks):
			item = QtWidgets.QTreeWidgetItem()
			item.setSizeHint(0, QtCore.QSize(btn_size, btn_size))
			self.tree.addTopLevelItem(item)

			for column, shape_item in enumerate(items):
				key, data = shape_item
				btn = QtWidgets.QPushButton(self)
				btn.setToolTip("{}:\n{}".format(key, data.get("note")))
				btn.setIcon(QtGui.QIcon(os.path.join(icon_path, data.get("icon"))))
				btn.setIconSize(QtCore.QSize(btn_size * .7, btn_size * .7))
				btn.released.connect(partial(self.set_shapes, key))
				self.tree.setItemWidget(item, column, btn)

	def populate_colors(self):
		"""

		:return:
		"""
		chunks = utilslib.conversion.as_chunks([[k, v] for k, v in color_data], num_columns)

		for row, items in enumerate(chunks):
			item = QtWidgets.QTreeWidgetItem()
			item.setSizeHint(0, QtCore.QSize(btn_size, btn_size))
			self.c_tree.addTopLevelItem(item)

			for column, shape_item in enumerate(items):
				key, idx = shape_item
				btn = QtWidgets.QPushButton(self)
				btn.setMinimumWidth(btn_size)
				btn.setMinimumWidth(btn_size)
				btn.setToolTip("{}:\ncolor index {}\n".format(key, idx))
				btn.released.connect(partial(self.set_colors, key))

				if key == "none":
					btn.setText("None")

				else:
					rgb = colorlib.get_color_rbg_from_index(idx, color_range=(0, 255))
					rgb = "{}, {}, {}".format(rgb[0], rgb[1], rgb[2])
					btn.setStyleSheet("QPushButton{ background-color:rgb(" + rgb + ")}")
				self.c_tree.setItemWidget(item, column, btn)

	@decoratorslib.undoable
	@decoratorslib.preserve_selection
	def set_shapes(self, shape):
		"""
		Set shape on selected ctrls.. filters out offset controls and pivot controls

		:param shape:
		:return:
		"""
		for ctrl in get_valid_selection():
			ct = controlslib.Control(ctrl)
			ct.set_shape(shape)

	@decoratorslib.undoable
	@decoratorslib.preserve_selection
	def set_colors(self, color):
		"""
		Set shape on selected ctrls.. filters out offset controls and pivot controls

		:param color:
		:return:
		"""
		for ctrl in get_valid_selection():
			ct = controlslib.Control(ctrl)
			ct.set_color(color)

	@decoratorslib.undoable
	@decoratorslib.preserve_selection
	def rotate_shape(self, axis):
		"""

		:return:
		"""
		shapes = cmds.ls(["{}.cv[*]".format(s) for s in selectionlib.get_shapes(get_valid_selection())])
		cmds.xform(shapes, r=1, ro=axis)

	def closeEvent(self, event, *args, **kwargs):
		"""

		:param event:
		:return:
		"""
		self.settings.setValue("geometry", self.saveGeometry())
		QtWidgets.QDialog.closeEvent(self, event)

	def reject(self, *args, **kwargs):
		"""

		:return:
		"""
		self.settings.setValue("geometry", self.saveGeometry())
		QtWidgets.QDialog.reject(self)


def list_ud(c):
	"""

	:param c:
	:return:
	"""
	return cmds.listAttr(c, ud=True) or []


def get_valid_selection():
	"""

	:return:
	"""
	ctrls = cmds.ls(sl=1)
	ctrls = [c for c in ctrls if controlslib.TAG_PIVOT_CONTROL not in list_ud(c)]
	ctrls = [c for c in ctrls if "smrigGuideControlPivot" not in list_ud(c)]
	ctrls = [c for c in ctrls if "smrigGuidePlacer" not in list_ud(c)]
	return ctrls


def run(reset=False):
	"""

	:return: Qt widget object
	"""
	global ctrl_ui

	if ctrl_ui and not reset:
		ctrl_ui.show()

	else:
		ctrl_ui = Controls()
		ctrl_ui.show()

	return ctrl_ui
