import logging

from PySide2 import QtCore, QtWidgets, QtGui

from smrig import partslib
from smrig.gui.mayawin import maya_main_window, get_icon_path

log = logging.getLogger("smrig")


class NewTemplate(QtWidgets.QDialog):

	def __init__(self, parent=maya_main_window):
		super(NewTemplate, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Mirror Options")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		label_wdg = QtWidgets.QLabel("Name: ")
		layout.addWidget(label_wdg, 1, 0)

		label_wdg = QtWidgets.QLabel("Category: ")
		layout.addWidget(label_wdg, 2, 0)

		self.name_line = QtWidgets.QLineEdit(self)
		layout.addWidget(self.name_line, 1, 1)

		self.cat_line = QtWidgets.QLineEdit(self)
		layout.addWidget(self.cat_line, 2, 1)

		btn = QtWidgets.QPushButton("Save Guide Template")
		btn.released.connect(self.save)
		layout.addWidget(btn, 3, 0, 1, 2)
		self.resize(200, 101)

		self.setMaximumWidth(200)
		self.setMinimumWidth(200)
		self.setMaximumHeight(101)
		self.setMinimumHeight(101)

		cmp = QtWidgets.QCompleter(partslib.manager.categories)
		self.cat_line.setCompleter(cmp)

	def save(self):
		"""

		:return:
		"""
		if not self.name_line.text() or not self.cat_line.text():
			log.warning("Enter name and category.")
			return

		partslib.manager.create_template(self.name_line.text(), self.cat_line.text())
		self.deleteLater()
