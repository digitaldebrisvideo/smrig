try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui

from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.gui.widget import header


class NewStep(QtWidgets.QDialog):
	do_it = False

	def __init__(self, parent=maya_main_window, label="", import_code="", command_code="", item_type=""):
		super(NewStep, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Add New Build Step")
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		self.label = label.strip()
		self.import_code = import_code
		self.command_code = command_code
		self.item_type = item_type

		layout = QtWidgets.QGridLayout(self)

		self.header = header.Header(self, large=False, title="New Build Step")
		layout.addWidget(self.header, 0, 0, 1, 2)

		label_wdg = QtWidgets.QLabel("Label: ")
		layout.addWidget(label_wdg, 1, 0)

		label_wdg = QtWidgets.QLabel("Import Code: ")
		layout.addWidget(label_wdg, 2, 0)

		label_wdg = QtWidgets.QLabel("Command Code: ")
		layout.addWidget(label_wdg, 3, 0)

		label_wdg = QtWidgets.QLabel("Type: ")
		layout.addWidget(label_wdg, 4, 0)

		self.label_line = QtWidgets.QLineEdit(self)
		self.label_line.setPlaceholderText("Step Label")
		self.label_line.setText(label.strip())
		layout.addWidget(self.label_line, 1, 1)

		self.import_line = QtWidgets.QLineEdit(self)
		self.import_line.setPlaceholderText("Import / source command")
		self.import_line.setText(import_code)
		layout.addWidget(self.import_line, 2, 1)

		self.command_line = QtWidgets.QLineEdit(self)
		self.command_line.setPlaceholderText("Command code to execute")
		self.command_line.setText(command_code)
		layout.addWidget(self.command_line, 3, 1)

		self.type_cmb = QtWidgets.QComboBox()
		self.type_cmb.addItems(["python", "MEL"])
		self.type_cmb.setCurrentText(item_type.upper() if item_type == "mel" else item_type)
		layout.addWidget(self.type_cmb, 4, 1)

		btn = QtWidgets.QPushButton("Save Step" if label else "Add New Step")
		btn.released.connect(self.add_step)
		layout.addWidget(btn, 5, 0, 1, 2)
		self.resize(400, 150)

		self.setMinimumHeight(190)
		self.setMaximumHeight(190)

		self.setMinimumWidth(400)
		self.setMaximumWidth(400)

	def add_step(self):
		"""

		:return:
		"""
		self.label = self.label_line.text().strip()
		self.import_code = self.import_line.text().strip()
		self.command_code = self.command_line.text().strip()
		self.item_type = self.type_cmb.currentText().lower()
		self.do_it = True

		self.deleteLater()
