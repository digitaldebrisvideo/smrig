import logging
import os
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.gui.widget import header
from smrig.lib import pathlib

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"

log = logging.getLogger("smrig.gui.widget.guideloader")


class InheritSettings(QtWidgets.QDialog):
	post_function = None

	def __init__(self, parent=maya_main_window):
		super(InheritSettings, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Sys.path Inheritance")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QGridLayout(self)

		asset = env.asset.get_asset()
		variant = env.asset.get_variant()
		self.g_header = header.Header(self, large=False, title="Asset: {} {}".format(asset, variant))

		self.tree = QtWidgets.QTreeWidget(self)
		self.tree.setColumnCount(3)
		self.tree.setIndentation(0)
		self.tree.header().resizeSection(1, 110)
		self.tree.header().resizeSection(2, 30)
		self.tree.setHeaderLabels(["Asset", "Use Build List", ""])
		self.tree.header().setStretchLastSection(False)
		self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		self.tree.setFocusPolicy(QtCore.Qt.NoFocus);

		self.add_button = QtWidgets.QPushButton("Add sys.path Inheritance")
		self.add_button.released.connect(self.add_item)

		self.save_button = QtWidgets.QPushButton("Save Inheritance Settings")
		self.save_button.released.connect(self.save)

		layout.addWidget(self.g_header, 0, 0)
		layout.addWidget(self.add_button, 1, 0)
		layout.addWidget(self.tree, 2, 0)
		layout.addWidget(self.save_button, 3, 0)

		self.setMinimumWidth(350)
		self.set_from_asset_data()

	def add_item(self, asset=None, inherit_build_list=False):
		"""

		:param asset:
		:param inherit_build_list:
		:return:
		"""
		item = QtWidgets.QTreeWidgetItem()
		item.asset_cmb = QtWidgets.QComboBox(self)
		item.checkbox = QtWidgets.QCheckBox(self)
		item.button = QtWidgets.QPushButton()

		item.button.released.connect(partial(self.remove_item, item))
		item.checkbox.setChecked(inherit_build_list)
		item.button.setIcon(QtGui.QIcon(get_icon_path("deleteActive.png")))
		item.setSizeHint(0, QtCore.QSize(26, 26))

		self.tree.addTopLevelItem(item)
		self.tree.setItemWidget(item, 0, item.asset_cmb)
		self.tree.setItemWidget(item, 1, item.checkbox)
		self.tree.setItemWidget(item, 2, item.button)

		style = "QTreeView::item { padding: 1px 1px 1px 4px; background-color:rgb(55, 55, 55)} "
		style += "QComboBox{background-color:rgb(75,75,75)}"
		self.tree.setStyleSheet(style)

		self.list_assets(item.asset_cmb)
		if asset:
			item.asset_cmb.setCurrentText(asset)

	def remove_item(self, item):
		"""

		:param item:
		:return:
		"""
		self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
		self.tree.setCurrentItem(None)

	def list_assets(self, asset_cmb, *args):
		"""

		:param widget:
		:return:
		"""
		asset_cmb.clear()
		asset_cmb.addItems(get_assets(env.get_job()))

	def set_from_asset_data(self):
		"""

		:return:
		"""
		data = env.asset.get_inheritance()
		self.tree.clear()

		if not data:
			return

		for item in data:
			self.add_item(*item)

	def save(self):
		"""

		:return:
		"""
		if not env.asset.get_asset() or not env.asset.get_variant():
			log.warning("Job, asset or variant not set!")
			return

		env.asset._inheritance = []
		for index in range(self.tree.topLevelItemCount()):
			item = self.tree.topLevelItem(index)
			asset = item.asset_cmb.currentText()
			inhert_build_list = item.checkbox.isChecked()
			env.asset.add_inheritance(asset, inhert_build_list)

		if self.post_function:
			self.post_function()

		self.deleteLater()


def get_assets(job):
	"""

	:param job:
	:return:
	"""
	if not job:
		return []

	base_directory = env.prefs.get_path_template().split("{asset}")[0].replace("{job}", job)
	if not os.path.isdir(base_directory):
		return []

	assets_list = [d for d in os.listdir(base_directory) if
	               not d.startswith(".") and os.path.isdir(os.path.join(base_directory, d))]

	return sorted(assets_list)


def get_guide_names(job, asset):
	"""

	:param job:
	:param asset:
	:return:
	"""
	if not job or not asset:
		return []

	build_path = env.assets.get_rigbuild_path(asset)
	directory = pathlib.normpath(os.path.join(os.path.dirname(build_path), "guides"))

	if not os.path.isdir(directory):
		return []

	names = [f.split("_")[2] for f in os.listdir(directory) if "guides" in f and f.endswith(maya_file_extention)]

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

	build_path = env.assets.get_rigbuild_path(asset)
	directory = pathlib.normpath(os.path.join(os.path.dirname(build_path), "guides"))

	if not os.path.isdir(directory):
		return []

	file_name = "{}_guides_{}".format(asset, name)
	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	versions = version_object.get_versions()
	versions.insert(0, "latest")
	return versions
