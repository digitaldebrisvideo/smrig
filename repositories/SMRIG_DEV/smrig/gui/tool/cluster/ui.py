import logging
from functools import partial

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui
from maya import cmds

from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.lib import deformlib

log = logging.getLogger("smrig")


class Cluster(QtWidgets.QDialog):
	geo = None

	def __init__(self, parent=maya_main_window):
		super(Cluster, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Cluster UI")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		wn_label = QtWidgets.QLabel("Weighted Node")
		pb_label = QtWidgets.QLabel("Prebind Node")

		self.wn_line = QtWidgets.QLineEdit()
		self.pb_line = QtWidgets.QLineEdit()

		wn_btn = QtWidgets.QPushButton()
		pb_btn = QtWidgets.QPushButton()

		create_btn = QtWidgets.QPushButton("Create Cluster")
		soft_btn = QtWidgets.QPushButton("Create Cluster With Soft Weighted")

		create_btn.released.connect(self.create_cls)
		soft_btn.released.connect(self.create_soft_cls)

		wn_btn.setIcon(QtGui.QIcon(get_icon_path("select.png")))
		wn_btn.setToolTip("Set Selected")
		wn_btn.setMaximumWidth(50)

		pb_btn.setIcon(QtGui.QIcon(get_icon_path("select.png")))
		pb_btn.setToolTip("Set Selected")
		pb_btn.setMaximumWidth(50)

		wn_btn.released.connect(partial(self.get_selected, self.wn_line))
		pb_btn.released.connect(partial(self.get_selected, self.pb_line))

		layout.addWidget(wn_label, 0, 0)
		layout.addWidget(pb_label, 1, 0)

		layout.addWidget(self.wn_line, 0, 1)
		layout.addWidget(self.pb_line, 1, 1)

		layout.addWidget(wn_btn, 0, 2)
		layout.addWidget(pb_btn, 1, 2)

		layout.addWidget(create_btn, 2, 0, 1, 3)
		layout.addWidget(soft_btn, 3, 0, 1, 3)

	def get_selected(self, line_edit):
		"""

		:return:
		"""
		sel = cmds.ls(sl=1)
		line_edit.setText(sel[0])

	def create_cls(self):
		"""

		:return:
		"""
		sel = cmds.ls(sl=1, fl=1)
		wn = self.wn_line.text() or None
		pb = self.pb_line.text() or None
		cls = deformlib.cluster.create_cluster(sel, weighted_node=wn, prebind_node=pb)
		print("Created cluster: {}".format(cls))

		return cls

	def create_soft_cls(self):
		"""

		:return:
		"""
		sel = cmds.ls(sl=1)
		cls = self.create_cls()[0]
		loc = cmds.ls(sl=1)

		cmds.select(sel)
		deformlib.cluster.set_soft_weights(cls)
		cmds.select(loc)


def run():
	"""

	:return:
	"""
	cluster_ui = Cluster()
	cluster_ui.show()
	return cluster_ui
