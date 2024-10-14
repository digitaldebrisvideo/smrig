import logging
import os

try:
    from PySide2 import QtCore, QtWidgets
except:
	from PySide6 import QtCore, QtWidgets

from smrig import partslib
from smrig.gui.mayawin import maya_main_window
from smrig.lib import pathlib

log = logging.getLogger("smrig.gui.widget.newpart")


class NewPart(QtWidgets.QDialog):

	def __init__(self, parent=maya_main_window):
		super(NewPart, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)
		self.setWindowTitle("smrig | Create New Part")

		layout = QtWidgets.QGridLayout(self)

		name_label = QtWidgets.QLabel("Part Name")
		cat_label = QtWidgets.QLabel("Category")

		self.name_line = QtWidgets.QLineEdit()
		self.cat_line = QtWidgets.QLineEdit()
		self.create_btn = QtWidgets.QPushButton("Create")
		self.cancel_btn = QtWidgets.QPushButton("Cancel")

		self.cancel_btn.released.connect(self.deleteLater)
		self.create_btn.released.connect(self.create)

		completer = QtWidgets.QCompleter(partslib.manager.categories, self)
		completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		completer.setWrapAround(False)
		self.cat_line.setCompleter(completer)

		layout.addWidget(name_label, 0, 0)
		layout.addWidget(cat_label, 1, 0)
		layout.addWidget(self.name_line, 0, 1)
		layout.addWidget(self.cat_line, 1, 1)

		row_layout = QtWidgets.QHBoxLayout()
		row_layout.addWidget(self.create_btn)
		row_layout.addWidget(self.cancel_btn)

		layout.addLayout(row_layout, 2, 0, 1, 2)
		self.setMinimumWidth(255)
		self.setMaximumWidth(255)
		self.setMinimumHeight(101)
		self.setMaximumHeight(101)

	def create(self):
		"""

		:return:
		"""
		name = self.name_line.text()
		cat = self.cat_line.text()

		if not name or not cat:
			log.warning("Specify name and category.")
			return

		file_path = partslib.manager.create_part(name, cat)

		if file_path and os.path.isfile(file_path):
			pathlib.open_in_text_editor(file_path)
			self.deleteLater()


def run(parent):
	"""

	:return:
	"""
	self = NewPart(parent)
	self.show()
