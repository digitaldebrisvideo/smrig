import logging

import maya.cmds as cmds
try:
	from PySide2 import QtCore, QtWidgets
except:
	from PySide6 import QtCore, QtWidgets

from smrig.build import rig
from smrig.gui import mayawin
from smrig.gui.widget import header

log = logging.getLogger("smrig.gui.tool.guidebuild")


class EndTools(QtWidgets.QWidget):
	stored_build_list = []
	style = "QTreeView::item { padding: 1px; } QTreeView{background-color: rgb(50,50,50)}"

	def __init__(self, parent=mayawin.maya_main_window):
		super(EndTools, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Rigbuild")

		layout = QtWidgets.QVBoxLayout(self)
		layout.setStretch(0, 1)

		self.header = header.Header(self, large=False, light_grey=True, title="Rigging EndTools")
		self.header.help_button.setCheckable(True)
		layout.addWidget(self.header)

		# settings util --------------------------------

		btn = QtWidgets.QPushButton("Set up current scene with cache and render references")
		layout.addWidget(btn)
		btn.released.connect(self.setup_current_scene)

		self.ref_configuration = QtWidgets.QComboBox(self)

		# # controls util --------------------------------
		#
		# btn = QtWidgets.QPushButton("Controls UI")
		# btn.released.connect(controls.run)
		# layout.addWidget(btn)
		#
		# # hand pose util --------------------------------
		#
		# btn = QtWidgets.QPushButton("Hand Pose Util")
		# btn.released.connect(handpose.run)
		# layout.addWidget(btn)
		#
		# # cluster util --------------------------------
		#
		# btn = QtWidgets.QPushButton("Cluster UI")
		# btn.released.connect(cluster.run)
		# layout.addWidget(btn)

		# prop rig util --------------------------------

		# btn = QtWidgets.QPushButton("Prog Rig Util")
		# btn.released.connect(proprig.run)
		# layout.addWidget(btn)

		# end spacer ------------------------------------

		spc = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
		layout.addSpacerItem(spc)

	def setup_current_scene(self):
		"""

		"""
		# check current scene for references
		if cmds.namespace(":CACHE", exists=True, query=True):
			if cmds.namespace(":RENDER", exists=True, query=True):
				cmds.confirmDialog(title='Confirm', message='CACHE & RENDER references already exists in scene',
				                   button=['OK', 'Cancel'], defaultButton='OK',
				                   cancelButton='Cancel', dismissString='Cancel')
				return ("current file appears to be setup.  See Briana if problem persists")
			else:
				return (
					"It looks like one of the references appear to exists but not the other one.  Delete CACHE reference and try again")

		rig.reference_connect_cache_render_scenes()
		cmds.confirmDialog(title='Reminder',
		                   message='Scene is now set up for cache export and rendering\nIn DEV: For now, Use ReferenceEditor to load and unload\nRemember to save this scene to keep update',
		                   button=['OK', 'Cancel'], defaultButton='OK',
		                   cancelButton='Cancel', dismissString='Cancel')

	def set_stage_configuration(self):
		"""

		"""
		pass


def run():
	"""

	:return: Qt widget object
	"""
	ui = EndTools()
	ui.show()
	return ui
