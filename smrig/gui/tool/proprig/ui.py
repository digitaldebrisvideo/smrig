import logging

from PySide2 import QtCore, QtWidgets, QtGui
from maya import cmds

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.partslib.common import prop

log = logging.getLogger("smrig")


class PropRig(QtWidgets.QDialog):
	geo = None

	def __init__(self, parent=maya_main_window):
		super(PropRig, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Prop Rig")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		asset_label = QtWidgets.QLabel("Save To Asset")
		bind_label = QtWidgets.QLabel("Bind Method")
		self.asset_name = QtWidgets.QLineEdit()
		self.bind_cmb = QtWidgets.QComboBox(self)
		self.bind_cmb.addItems(["Matrix Constraint", "Skin Cluster"])

		self.completer = QtWidgets.QCompleter(env.get_assets(), self)
		self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
		self.completer.setWrapAround(False)
		self.asset_name.setCompleter(self.completer)

		btn = QtWidgets.QPushButton("Build Guides")
		btn0 = QtWidgets.QPushButton("Build Rig")

		btn.released.connect(self.build_guide)
		btn0.released.connect(self.build_rig)

		layout.addWidget(asset_label, 0, 0)
		layout.addWidget(self.asset_name, 0, 1)
		layout.addWidget(bind_label, 1, 0)
		layout.addWidget(self.bind_cmb, 1, 1, 1, 1)

		layout.addWidget(btn, 2, 0, 1, 2)
		layout.addWidget(btn0, 3, 0, 1, 2)

		self.setMaximumWidth(240)
		self.setMinimumWidth(240)
		self.setMaximumHeight(133)
		self.setMinimumHeight(133)

	def build_guide(self):
		"""

		:return:
		"""
		self.geo = cmds.ls(sl=1)
		prop.build_guide(self.geo)

	def build_rig(self):
		"""

		:return:
		"""
		asset_name = self.asset_name.text()
		bind_method = self.bind_cmb.currentText()
		prop.build_rig(self.geo, asset_name=asset_name, bind_method=bind_method)


def run():
	"""

	:return:
	"""
	prop_rig_ui = PropRig()
	prop_rig_ui.show()
	return prop_rig_ui
