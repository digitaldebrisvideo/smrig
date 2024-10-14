import logging
from functools import partial

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui
from maya import cmds

from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.lib import decoratorslib
from smrig.lib.deformlib import blendshape

log = logging.getLogger("smrig.splitshapes.ui")


class SplitShapes(QtWidgets.QDialog):
	split_obj = None

	def __init__(self, parent=maya_main_window):
		super(SplitShapes, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | SplitShapes UI")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		n_label = QtWidgets.QLabel("Name")
		g_label = QtWidgets.QLabel("Base Geo")
		t_label = QtWidgets.QLabel("Target Geos")
		p_label = QtWidgets.QLabel("Split Prefixes")

		self.n_line = QtWidgets.QLineEdit()
		self.g_line = QtWidgets.QLineEdit()
		self.t_line = QtWidgets.QLineEdit()
		self.p_line = QtWidgets.QLineEdit()

		g_btn = QtWidgets.QPushButton()
		t_btn = QtWidgets.QPushButton()
		c_btn = QtWidgets.QPushButton("Create Split Setup")
		u_btn = QtWidgets.QPushButton("Update Weights")
		e_btn = QtWidgets.QPushButton("Extract Shapes")
		d_btn = QtWidgets.QPushButton("Delete Setup")

		g_btn.setIcon(QtGui.QIcon(get_icon_path("select.png")))
		g_btn.setToolTip("Set Selected")
		g_btn.setMaximumWidth(50)

		t_btn.setIcon(QtGui.QIcon(get_icon_path("select.png")))
		t_btn.setToolTip("Set Selected")
		t_btn.setMaximumWidth(50)

		layout.addWidget(n_label, 0, 0)
		layout.addWidget(g_label, 1, 0)
		layout.addWidget(t_label, 2, 0)
		layout.addWidget(p_label, 3, 0)

		layout.addWidget(self.n_line, 0, 1)
		layout.addWidget(self.g_line, 1, 1)
		layout.addWidget(self.t_line, 2, 1)
		layout.addWidget(self.p_line, 3, 1, 1, 2)

		layout.addWidget(g_btn, 1, 2)
		layout.addWidget(t_btn, 2, 2)

		layout.addWidget(c_btn, 4, 0, 1, 3)
		layout.addWidget(u_btn, 5, 0, 1, 3)
		layout.addWidget(e_btn, 6, 0, 1, 3)
		layout.addWidget(d_btn, 7, 0, 1, 3)

		c_btn.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		action = QAction(self)
		action.setText("Get Split Group From Selection")
		action.triggered.connect(self.get_setup)
		c_btn.addAction(action)

		g_btn.released.connect(partial(self.get_selected, self.g_line))
		t_btn.released.connect(partial(self.get_selected, self.t_line, multiple=True))

		c_btn.released.connect(self.create)
		u_btn.released.connect(self.update)
		e_btn.released.connect(self.extract)
		d_btn.released.connect(self.delete_splits)

		self.resize(350, 269)

	def get_selected(self, line_edit, multiple=False):
		"""

		:param line_edit:
		:param multiple:
		:return:
		"""
		sel = cmds.ls(sl=1) if multiple else cmds.ls(sl=1)[0]
		line_edit.setText(str(sel))

	def get_setup(self):
		"""

		:return:
		"""
		self.split_obj = blendshape.SplitShapes(cmds.ls(sl=1)[0])
		name = self.split_obj.name
		self.n_line.setText(name[:-1])
		self.g_line.setText(self.split_obj.geo.replace(name, "").replace("_split", ""))
		self.t_line.setText(str(self.split_obj.targets))
		self.p_line.setText(", ".join(self.split_obj.prefixes))

	@decoratorslib.undoable
	def create(self):
		"""

		:return:
		"""
		name = self.n_line.text() if self.n_line.text() else None
		geo = self.g_line.text()
		target = eval(self.t_line.text())
		prefixes = [p for p in self.p_line.text().strip().replace(" ", ",").split(",") if p]
		self.split_obj = blendshape.SplitShapes.create(geo, target, prefixes, name=name)
		self.p_line.setText(", ".join(self.split_obj.prefixes))
		print("Done")

	@decoratorslib.undoable
	def update(self):
		"""

		:return:
		"""
		if self.split_obj:
			self.split_obj.update_weights()
			print("Done")

		else:
			log.warning("Split Group not initialized. ")

	@decoratorslib.undoable
	def extract(self):
		"""

		:return:
		"""
		if self.split_obj:
			self.split_obj.extract_shapes()
			print("Done")
		else:
			log.warning("Split Group not initialized. ")

	@decoratorslib.undoable
	def delete_splits(self):
		"""

		:return:
		"""
		if self.split_obj:
			self.split_obj.delete_split_setup()
			print("Done")
		else:
			log.warning("Split Group not initialized. ")


def run():
	"""

	:return:
	"""
	split_ui = SplitShapes()
	split_ui.show()
	return split_ui
