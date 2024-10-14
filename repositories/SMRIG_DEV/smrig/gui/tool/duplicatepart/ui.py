import logging

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.gui.widget import header

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"

log = logging.getLogger("smrig.gui.widget.guideloader")


class DuplicateGuide(QtWidgets.QDialog):
	do_it = False
	side = None
	name = None

	def __init__(self, parent=maya_main_window):
		super(DuplicateGuide, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Mirror Options")
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		self.header = header.Header(self, large=False, title="Duplicate Part")
		layout.addWidget(self.header, 0, 0, 1, 2)

		label = QtWidgets.QLabel("New Side: ")
		layout.addWidget(label, 1, 0)

		label = QtWidgets.QLabel("New Name: ")
		layout.addWidget(label, 2, 0)

		self.side_line = QtWidgets.QLineEdit(self)
		self.side_line.setText("")
		layout.addWidget(self.side_line, 1, 1)

		self.name_line = QtWidgets.QLineEdit(self)
		self.name_line.setText("")
		layout.addWidget(self.name_line, 2, 1)

		btn = QtWidgets.QPushButton("Duplicate Selected Parts")
		btn.released.connect(self.duplicate)
		layout.addWidget(btn, 5, 0, 1, 2)
		self.resize(400, 150)

		self.setMinimumHeight(136)
		self.setMaximumHeight(136)

		self.setMinimumWidth(400)
		self.setMaximumWidth(400)

	def duplicate(self):
		"""

		:return:
		"""
		self.side = self.side_line.text()
		self.name = self.name_line.text()
		self.do_it = True

		self.deleteLater()
