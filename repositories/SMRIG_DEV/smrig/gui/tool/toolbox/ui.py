import logging
import maya.cmds as cmds
try:
	from PySide2 import QtCore, QtWidgets
except:
	from PySide6 import QtCore, QtWidgets

from smrig.build import model
from smrig.gui import mayawin
from smrig.gui.tool import cluster
from smrig.gui.tool import controls
from smrig.gui.tool import handpose
from smrig.gui.tool import proprig
from smrig.gui.widget import header
from smrig.gui.tool import assetbrowser


log = logging.getLogger("smrig.gui.tool.guidebuild")


class ToolBox(QtWidgets.QWidget):
	stored_build_list = []
	style = "QTreeView::item { padding: 1px; } QTreeView{background-color: rgb(50,50,50)}"

	def __init__(self, parent=mayawin.maya_main_window):
		super(ToolBox, self).__init__(parent)

		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Rigbuild")

		layout = QtWidgets.QVBoxLayout(self)
		layout.setStretch(0, 1)

		self.header = header.Header(self, large=False, light_grey=True, title="Rigging Toolbox")
		self.header.help_button.setCheckable(True)
		layout.addWidget(self.header)

		# library exporter  --------------------------------

		btn = QtWidgets.QPushButton("Library Manager")
		btn.released.connect(assetbrowser.show)
		layout.addWidget(btn)

		# content browswer util --------------------------------

		btn = QtWidgets.QPushButton("Content Library")
		btn.released.connect(self.load_content_browser)
		layout.addWidget(btn)

		# controls util --------------------------------

		btn = QtWidgets.QPushButton("Controls UI")
		btn.released.connect(controls.run)
		layout.addWidget(btn)

		# hand pose util --------------------------------

		btn = QtWidgets.QPushButton("Hand Pose Util")
		btn.released.connect(handpose.run)
		layout.addWidget(btn)

		# cluster util --------------------------------

		btn = QtWidgets.QPushButton("Cluster UI")
		btn.released.connect(cluster.run)
		layout.addWidget(btn)

		# prop rig util --------------------------------

		btn = QtWidgets.QPushButton("Prog Rig Util")
		btn.released.connect(proprig.run)
		layout.addWidget(btn)

		# end spacer ------------------------------------

		spc = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
		layout.addSpacerItem(spc)

	def load_content_browser(self):
		"""
		load Maya's content browser
		:return:
		"""
		cmds.OpenContentBrowser ()

def run():
	"""

	:return: Qt widget object
	"""
	ui = ToolBox()
	ui.show()
	return ui
