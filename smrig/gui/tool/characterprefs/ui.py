import logging
from functools import partial

from smrig.gui import mayawin

log = logging.getLogger("smrig.gui.tool.guidebuild")

from PySide2 import QtCore, QtWidgets, QtGui
from smrig import env
from smrig.gui.mayawin import get_icon_path
from smrig.gui.widget import header

try:
	import visional_pipeline_api1.element as velement
	import visional_pipeline_api1.asset as vasset

except:
	pass

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"
filters = "Maya Scenes (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);;OBJ (*.obj);;FBX (*.fbx);;All Files (*.*)"
log = logging.getLogger("smrig.gui.widget.modelloader")


class CharacterPrefs(QtWidgets.QWidget):
	stored_build_list = []
	style = "QTreeView::item { padding: 1px; } QTreeView{background-color: rgb(50,50,50)}"

	def __init__(self, parent=mayawin.maya_main_window):
		super(CharacterPrefs, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Character Preferences")

		layout = QtWidgets.QVBoxLayout(self)
		layout.setStretch(0, 1)

		self.header = header.Header(self, large=False, light_grey=True, title="Rigging CharacterPrefs")
		self.header.help_button.setCheckable(True)
		layout.addWidget(self.header)

		# settings util --------------------------------

		# btn = QtWidgets.QPushButton("Settings and tools UI")
		# btn.released.connect(model.run)
		# layout.addWidget(btn)

		# controls util --------------------------------

		item = QtWidgets.QTreeWidgetItem()
		item.asset_cmb = QtWidgets.QComboBox(self)
		item.name_cmb = QtWidgets.QComboBox(self)
		item.version_cmb = QtWidgets.QComboBox(self)
		item.unlock_checkbox = QtWidgets.QCheckBox(self)
		item.soften_checkbox = QtWidgets.QCheckBox(self)
		item.button = QtWidgets.QPushButton()

		item.button.released.connect(partial(self.remove_item, item))

		item.button.setIcon(QtGui.QIcon(get_icon_path("deleteActive.png")))
		item.setSizeHint(0, QtCore.QSize(26, 26))

		self.tree.addTopLevelItem(item)
		self.tree.setItemWidget(item, 0, item.asset_cmb)
		self.tree.setItemWidget(item, 1, item.name_cmb)
		self.tree.setItemWidget(item, 2, item.version_cmb)
		self.tree.setItemWidget(item, 3, item.unlock_checkbox)
		self.tree.setItemWidget(item, 4, item.soften_checkbox)
		self.tree.setItemWidget(item, 5, item.button)

		style = "QTreeView::item { padding: 1px 1px 1px 4px; background-color:rgb(55, 55, 55)} "
		style += "QComboBox{background-color:rgb(75,75,75)}"
		self.tree.setStyleSheet(style)

		# item.asset_cmb.currentIndexChanged.connect(partial(self.list_names, item))
		# item.name_cmb.currentIndexChanged.connect(partial(self.list_versions, item))

		item.name_cmb.setMaximumWidth(160)
		item.asset_cmb.setMaximumWidth(160)
		item.version_cmb.setMaximumWidth(160)

		# self.list_assets(item)

		if asset:
			item.asset_cmb.setCurrentText(asset)
		if description:
			item.name_cmb.setCurrentText(description)
		if version:
			item.version_cmb.setCurrentText(str(version))
		if unlock_normals:
			item.unlock_checkbox.setChecked(unlock_normals)
		if soft_normals:
			item.soften_checkbox.setChecked(soft_normals)

	def remove_item(self, item):
		"""

		:param item:
		:return:
		"""
		self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
		self.tree.setCurrentItem(None)

		self.tree_file.takeTopLevelItem(self.tree_file.indexOfTopLevelItem(item))
		self.tree_file.setCurrentItem(None)

		if not self.tree_file.topLevelItemCount():
			self.tree_file.hide()


def run():
	"""

	:return: Qt widget object
	"""
	ui = CharacterPrefs()
	ui.show()
	return ui
