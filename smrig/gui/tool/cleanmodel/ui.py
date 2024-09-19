import logging

from PySide2 import QtCore, QtWidgets, QtGui

from smrig.build import model
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.lib import naminglib

log = logging.getLogger("smrig")

options = [("freeze_transforms", True),
           ("zero_pivots", True),
           ("unlock_normals", False),
           ("soften_normals", False),
           ("rename_shape_nodes", True),
           ("delete_intermediate_objects", True),
           ("delete_layers", True),
           ("delete_namespaces", True),
           ("delete_history", True),
           ("fix_clashing_node_names", True),
           ("remove_unknown_plugins", True),
           ("unlock_transforms", True), ]


class CleanModel(QtWidgets.QDialog):

	def __init__(self, parent=maya_main_window):
		super(CleanModel, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Clean Model")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		self.checks = []
		for i in range(len(options)):
			arg = options[i][0]
			dv = options[i][1]

			label = QtWidgets.QLabel(naminglib.conversion.snake_case_to_nice_name(arg))
			chx = QtWidgets.QCheckBox()
			chx.setChecked(dv)
			chx.arg = arg

			layout.addWidget(label, i, 0)
			layout.addWidget(chx, i, 1)
			self.checks.append(chx)

		btn = QtWidgets.QPushButton("Clean Model")
		btn.released.connect(self.clean_model)
		layout.addWidget(btn, i + 1, 0, 1, 2)

		self.setMaximumWidth(194)
		self.setMinimumWidth(194)
		self.setMaximumHeight(265)
		self.setMinimumHeight(265)

	def clean_model(self):
		"""

		:return:
		"""
		args = {}
		for chx in self.checks:
			args[chx.arg] = chx.isChecked()

		model.clean(**args)
		self.deleteLater()

		log.info("Finished cleaning model!")
