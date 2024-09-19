import logging

from PySide2 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.gui.widget import header

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"

log = logging.getLogger("smrig.gui.widget.guideloader")


class MirrorPart(QtWidgets.QDialog):
	side = None
	mirror_mode = None
	set_shapes = None
	set_colors = None
	do_it = False

	def __init__(self, parent=maya_main_window):
		super(MirrorPart, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Mirror Options")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		self.header = header.Header(self, large=False, title="Mirror Part Options")
		layout.addWidget(self.header, 0, 0, 1, 2)

		label = QtWidgets.QLabel("Mirror Axis: ")
		layout.addWidget(label, 2, 0)

		label = QtWidgets.QLabel("Mirror Control Shapes: ")
		layout.addWidget(label, 3, 0)

		label = QtWidgets.QLabel("Mirror Control Colors: ")
		layout.addWidget(label, 4, 0)

		self.axis_cmb = QtWidgets.QComboBox(self)
		self.axis_cmb.addItems(["X", "Y", "Z"])
		layout.addWidget(self.axis_cmb, 2, 1)

		self.shapes_chx = QtWidgets.QCheckBox(self)
		self.shapes_chx.setChecked(True)
		layout.addWidget(self.shapes_chx, 3, 1)

		self.colors_chx = QtWidgets.QCheckBox(self)
		self.colors_chx.setChecked(False)
		layout.addWidget(self.colors_chx, 4, 1)

		btn = QtWidgets.QPushButton("Mirror Selected Parts")
		btn.released.connect(self.mirror)
		layout.addWidget(btn, 5, 0, 1, 2)
		self.resize(400, 150)

		self.setMinimumHeight(180)
		self.setMaximumHeight(180)

		self.setMinimumWidth(400)
		self.setMaximumWidth(400)

	def mirror(self):
		"""

		:return:
		"""
		self.mirror_mode = self.axis_cmb.currentText()
		self.set_shapes = self.shapes_chx.isChecked()
		self.set_colors = self.colors_chx.isChecked()
		self.do_it = True

		self.deleteLater()
