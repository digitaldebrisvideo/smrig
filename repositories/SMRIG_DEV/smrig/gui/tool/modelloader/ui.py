import logging
from functools import partial

import maya.cmds as cmds
try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.build import model
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.gui.widget import header
from smrig.lib import pathlib
from smrig.userprefs import *

try:
	import visional_pipeline_api1.element as velement
	import visional_pipeline_api1.asset as vasset

except:
	pass

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"
filters = "Maya Scenes (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);;OBJ (*.obj);;FBX (*.fbx);;All Files (*.*)"
log = logging.getLogger("smrig.gui.widget.modelloader")


class ModelLoader(QtWidgets.QDialog):

	def __init__(self, parent=maya_main_window):
		super(ModelLoader, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Rig Bot | Model Loader")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		asset = env.asset.get_asset()
		variant = env.asset.get_variant()
		self.g_header = header.Header(self, large=False, title="Asset: {} {}".format(asset, variant))

		self.tree = QtWidgets.QTreeWidget(self)
		self.tree.setColumnCount(6)
		self.tree.setIndentation(0)
		self.tree.setHeaderLabels(["Asset", "Name", "Version", "Unlock Normals", "Soften Normals", ""])
		self.tree.setFocusPolicy(QtCore.Qt.NoFocus);

		self.tree.header().setStretchLastSection(False)
		self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
		self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
		self.tree.header().resizeSection(5, 30)

		# --------------------------------------------------
		self.tree_file = QtWidgets.QTreeWidget(self)
		self.tree_file.setColumnCount(5)
		self.tree_file.setIndentation(0)
		self.tree_file.setHeaderLabels(["", "", "", "", ""])
		self.tree_file.setFocusPolicy(QtCore.Qt.NoFocus);

		self.tree_file.header().setStretchLastSection(False)
		self.tree_file.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		self.tree_file.header().resizeSection(4, 30)
		self.tree_file.header().resizeSection(1, 30)
		self.tree_file.hide()

		self.add_button = QtWidgets.QPushButton("Add Model")
		self.add_button.released.connect(self.add_item)
		self.add_button.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		action = QAction(self)
		action.setText("Add Model File Path")
		action.triggered.connect(self.add_file_item)
		self.add_button.addAction(action)

		self.save_button = QtWidgets.QPushButton("Save Model Settings")
		self.save_button.released.connect(self.save)

		self.load_button = QtWidgets.QPushButton("Import Models")
		self.load_button.released.connect(self.load)

		layout.addWidget(self.g_header, 0, 0, 1, 2)
		layout.addWidget(self.add_button, 1, 0, 1, 2)
		layout.addWidget(self.tree, 2, 0, 1, 2)
		layout.addWidget(self.tree_file, 3, 0, 1, 2)
		layout.addWidget(self.load_button, 4, 0)
		layout.addWidget(self.save_button, 4, 1)

		style = "QTreeView::item { padding: 1px 1px 1px 4px; background-color:rgb(55, 55, 55)}"
		style += "QComboBox{background-color:rgb(75,75,75)}"

		self.tree.setStyleSheet(style)
		self.set_from_asset_data()
		self.setMinimumWidth(750)
		self.setMaximumWidth(750)
		self.resize(750, 250)

	def list_assets(self, item):
		"""

		:return:
		"""
		item.asset_cmb.clear()
		item.asset_cmb.addItems(get_assets(env.get_job()))

	def list_names(self, item, *args, **kwargs):
		"""

		:return:
		"""

		item.name_cmb.clear()
		item.name_cmb.addItems(get_model_names(env.get_job(), item.asset_cmb.currentText()))

	def list_versions(self, item, *args, **kwargs):
		"""

		:return:
		"""
		asset = item.asset_cmb.currentText()
		name = item.name_cmb.currentText()

		item.version_cmb.clear()
		item.version_cmb.addItems(get_versions(env.get_job(), asset, name))

	def set_from_asset_data(self):
		"""

		:return:
		"""
		data = env.asset.get_models()
		self.tree.clear()

		if not data:
			return

		for item in data:
			if item.get("file_path"):
				self.add_file_item(file_path=item.get("file_path"))
			else:
				self.add_item(**item)

	def save(self):
		"""

		:return:
		"""
		if not env.asset.get_asset() or not env.asset.get_variant():
			log.warning("Job, asset or variant not set!")
			return

		env.asset.set_models(clear_all=True)
		for index in range(self.tree.topLevelItemCount()):
			item = self.tree.topLevelItem(index)
			asset = item.asset_cmb.currentText()
			name = item.name_cmb.currentText()
			version = item.version_cmb.currentText()
			version = None if version == "latest" else int(version[1:]) if version else None

			unlock = item.unlock_checkbox.isChecked()
			soften = item.soften_checkbox.isChecked()

			if asset:
				env.asset.set_models(asset=asset,
				                     description=name,
				                     version=version,
				                     unlock_normals=unlock,
				                     soft_normal=soften,
				                     append=True)

		for index in range(self.tree_file.topLevelItemCount()):
			item = self.tree_file.topLevelItem(index)
			file_path = item.line_edit.text()
			unlock = item.unlock_checkbox.isChecked()
			soften = item.soften_checkbox.isChecked()

			env.asset.set_models(file_path=file_path,
			                     unlock_normals=unlock,
			                     soft_normal=soften,
			                     append=True)
		self.deleteLater()

	def load(self, new_file=False, action="import"):
		"""

		:param load_offset_data:
		:param new_file:
		:param action:
		:return:
		"""

		for index in range(self.tree.topLevelItemCount()):
			item = self.tree.topLevelItem(index)
			asset = item.asset_cmb.currentText()
			name = item.name_cmb.currentText()
			version = item.version_cmb.currentText()
			version = None if version == "latest" else int(version[1:]) if version else None

			unlock = item.unlock_checkbox.isChecked()
			soften = item.soften_checkbox.isChecked()

			model.load_scene(asset=asset,
			                 description=name,
			                 version=version,
			                 new_file=new_file,
			                 action=action,
			                 unlock_normals=unlock,
			                 soft_normals=soften)

		for index in range(self.tree_file.topLevelItemCount()):
			item = self.tree_file.topLevelItem(index)
			file_path = item.line_edit.text()
			unlock = item.unlock_checkbox.isChecked()
			soften = item.soften_checkbox.isChecked()

			model.load_scene(file_path=file_path,
			                 new_file=new_file,
			                 action=action,
			                 unlock_normals=unlock,
			                 soft_normals=soften)

	def browse(self, item):
		"""

		:param item:
		:return:
		"""
		file_path = cmds.fileDialog2(fileFilter=filters, dialogStyle=2, okc="Select", fm=1)
		if file_path:
			item.line_edit.setText(file_path[0])

	def reload_ui(self):
		"""

		:return:
		"""
		self.list_assets()
		self.set_from_asset_data()

	def add_item(self, asset=None, description=None, version=None, unlock_normals=False, soft_normals=False, **kwargs):
		"""

		:param asset:
		:param variant:
		:param version:
		:param unlock_normals:
		:param soft_normals:
		:param kwargs:
		:return:
		"""
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

		item.asset_cmb.currentIndexChanged.connect(partial(self.list_names, item))
		item.name_cmb.currentIndexChanged.connect(partial(self.list_versions, item))

		item.name_cmb.setMaximumWidth(160)
		item.asset_cmb.setMaximumWidth(160)
		item.version_cmb.setMaximumWidth(160)

		self.list_assets(item)

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

	def add_file_item(self, file_path=None, unlock_normals=False, soft_normals=False, **kwargs):
		"""

		:param file_path:
		:return:
		"""
		item = QtWidgets.QTreeWidgetItem()

		item.line_edit = QtWidgets.QLineEdit(self)
		item.unlock_checkbox = QtWidgets.QCheckBox(self)
		item.soften_checkbox = QtWidgets.QCheckBox(self)
		item.button = QtWidgets.QPushButton()
		item.button.setIcon(QtGui.QIcon(get_icon_path("deleteActive.png")))
		item.button.released.connect(partial(self.remove_item, item))
		item.browse_button = QtWidgets.QPushButton()
		item.browse_button.setIcon(QtGui.QIcon(get_icon_path("browse.png")))
		item.browse_button.released.connect(partial(self.browse, item))
		item.setSizeHint(0, QtCore.QSize(26, 26))

		self.tree_file.addTopLevelItem(item)
		self.tree_file.setItemWidget(item, 0, item.line_edit)
		self.tree_file.setItemWidget(item, 1, item.browse_button)
		self.tree_file.setItemWidget(item, 2, item.unlock_checkbox)
		self.tree_file.setItemWidget(item, 3, item.soften_checkbox)
		self.tree_file.setItemWidget(item, 4, item.button)

		style = "QTreeView::item { padding: 1px 1px 1px 4px; background-color:rgb(55, 55, 55)} "
		style += "QComboBox{background-color:rgb(75,75,75)}"
		self.tree_file.setStyleSheet(style)

		if file_path:
			item.line_edit.setText(file_path)
		if unlock_normals:
			item.unlock_checkbox.setChecked(unlock_normals)
		if soft_normals:
			item.soften_checkbox.setChecked(soft_normals)

		self.tree_file.show()

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


def get_assets(job):
	"""

	:param job:
	:return:
	"""
	if not job:
		return []

	if USE_FACILITY_PIPELINE:
		return env.get_assets()

	base_directory = env.prefs.get_path_template().split("{asset}")[0].replace("{job}", job)
	if not os.path.isdir(base_directory):
		return []

	assets_list = [d for d in os.listdir(base_directory) if
	               not d.startswith(".") and os.path.isdir(os.path.join(base_directory, d))]

	return sorted(assets_list)


def get_model_names(job, asset):
	"""

	:param job:
	:param asset:
	:return:
	"""
	if not job or not asset:
		return []

	if USE_FACILITY_PIPELINE:
		jpath = PATH_TEMPLATE.split("{job}")[0] + env.get_job()
		paths = [p for p in vasset.get_assets(jpath) if asset in p]

		if not paths:
			return []

		elements = sorted([os.path.basename(p) for p in velement.get_elements(paths[0]) if "_model_" in p])
		return elements

	build_path = env.assets.get_rigbuild_path(asset)
	directory = pathlib.normpath(os.path.join(os.path.dirname(build_path), "model"))

	if not os.path.isdir(directory):
		return []

	names = [f.split("_")[2] for f in os.listdir(directory) if "model" in f and f.endswith(maya_file_extention)]

	return sorted(list(set(names)))


def get_versions(job, asset, name):
	"""

	:param job:
	:param asset:
	:param name:
	:return:
	"""
	if not job or not asset or not name:
		return []

	if USE_FACILITY_PIPELINE:
		path = PATH_TEMPLATE.split("{job}")[0] + env.get_job()
		paths = [p for p in vasset.get_assets(path) if asset in p]
		if not paths:
			return []

		e_paths = [p for p in velement.get_elements(paths[0]) if name == os.path.basename(p)]
		if not e_paths:
			return []

		versions = [p.split("_")[-1] for p in velement.get_element_versions(e_paths[0])]
		versions.reverse()
		versions.insert(0, "latest")
		return versions

	build_path = env.assets.get_rigbuild_path(asset)
	directory = pathlib.normpath(os.path.join(os.path.dirname(build_path), "model"))

	if not os.path.isdir(directory):
		return []

	file_name = "{}_model_{}".format(asset, name)
	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	versions = version_object.get_versions()
	versions.insert(0, "latest")

	return versions
