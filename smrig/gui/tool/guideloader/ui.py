# -*- coding: utf-8 -*-

import logging
import os
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.build import guide
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.gui.widget import header
from smrig.lib import pathlib

maya_file_extention = env.prefs_.DEFAULT_FILE_TYPE
maya_file_type = "mayaBinary" if maya_file_extention == "mb" else "mayaAscii"

log = logging.getLogger("smrig.gui.widget.guideloader")


class GuideLoader(QtWidgets.QDialog):

	def __init__(self, parent=maya_main_window):
		super(GuideLoader, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Guide Loader")
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
		self.tree.setHeaderLabels(["Asset", "Name", "Version"])

		self.tree.header().setStretchLastSection(False)
		self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
		self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

		self.save_button = QtWidgets.QPushButton("Save Guide Settings")
		self.load_button = QtWidgets.QPushButton("Load Guides")
		self.load_button.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		action = QtWidgets.QAction(self)
		action.setText("Load Guides Without Inherit Offsets")
		action.triggered.connect(partial(self.load, load_offset_data=False))
		self.load_button.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Import Guides")
		action.triggered.connect(partial(self.load, new_file=False))
		self.load_button.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Open Guides")
		action.triggered.connect(partial(self.load, action="open"))
		self.load_button.addAction(action)

		layout.addWidget(self.g_header, 0, 0, 1, 2)
		layout.addWidget(self.tree, 1, 0, 1, 2)
		layout.addWidget(self.load_button, 2, 0)
		layout.addWidget(self.save_button, 2, 1)

		self.asset_cmb = QtWidgets.QComboBox(self)
		self.name_cmb = QtWidgets.QComboBox(self)
		self.version_cmb = QtWidgets.QComboBox(self)

		self.item = QtWidgets.QTreeWidgetItem()
		self.item.setSizeHint(0, QtCore.QSize(26, 26))

		self.tree.addTopLevelItem(self.item)
		self.tree.setItemWidget(self.item, 0, self.asset_cmb)
		self.tree.setItemWidget(self.item, 1, self.name_cmb)
		self.tree.setItemWidget(self.item, 2, self.version_cmb)
		self.tree.setFocusPolicy(QtCore.Qt.NoFocus);

		self.list_assets()
		self.asset_cmb.currentIndexChanged.connect(self.list_names)
		self.name_cmb.currentIndexChanged.connect(self.list_versions)
		self.save_button.released.connect(self.save)
		self.load_button.released.connect(self.load)

		style = "QTreeView::item { padding: 1px 1px 1px 4px; background-color:rgb(55, 55, 55)}"
		style += "QComboBox{background-color:rgb(75,75,75)}"

		self.tree.setStyleSheet(style)
		self.set_from_asset_data()

		self.resize(400, 150)

	def list_assets(self):
		"""

		:return:
		"""
		self.asset_cmb.clear()
		self.asset_cmb.addItems(get_assets(env.get_job()))

	def list_names(self):
		"""

		:return:
		"""
		self.name_cmb.clear()
		self.name_cmb.addItems(get_guide_names(env.get_job(), self.asset_cmb.currentText()))

	def list_versions(self):
		"""

		:return:
		"""
		asset = self.asset_cmb.currentText()
		name = self.name_cmb.currentText()

		self.version_cmb.clear()
		self.version_cmb.addItems(get_versions(env.get_job(), asset, name))

	def set_from_asset_data(self):
		"""

		:return:
		"""
		data = env.asset.get_guides()
		if not data:
			return

		self.list_assets()
		self.asset_cmb.setCurrentText(data[0].get("asset") or env.asset.get_asset())
		self.name_cmb.setCurrentText(data[0].get("description") or env.assets.DEFAULT_VARIANT)

		version = data[0].get("version")
		version = "v{}".format(str(version).zfill(3)) if version else "latest"
		self.version_cmb.setCurrentText(version)

	def save(self):
		"""

		:return:
		"""
		if not env.asset.get_asset() or not env.asset.get_variant():
			log.warning("Job, asset or variant not set!")
			return

		asset = self.asset_cmb.currentText()
		name = self.name_cmb.currentText() if self.name_cmb.currentText() else env.assets.DEFAULT_VARIANT
		version = self.version_cmb.currentText()
		version = None if version == "latest" else int(version[1:]) if version else None
		inherited = False if asset == env.asset.get_asset() else True

		env.asset.set_guides(asset=asset, description=name, version=version, inherited=inherited)
		self.deleteLater()

	def load(self, load_offset_data=True, new_file=True, action="import"):
		"""

		:param load_offset_data:
		:param new_file:
		:param action:
		:return:
		"""
		asset = self.asset_cmb.currentText()
		name = self.name_cmb.currentText()
		version = self.version_cmb.currentText()
		version = None if version == "latest" else int(version[1:]) if version else None
		inherited = False if asset == env.asset.get_asset() else True

		guide.load_scene(asset=asset, description=name, version=version, new_file=new_file, action=action)
		if load_offset_data and inherited:
			guide.load_data(asset=env.asset.get_asset(), description="inherited", build=False)

	def reload_ui(self):
		"""

		:return:
		"""
		self.list_assets()
		self.set_from_asset_data()


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
	directory = pathlib.normpath(os.path.join(build_path, "guides"))

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
	directory = pathlib.normpath(os.path.join(build_path, "guides"))

	if not os.path.isdir(directory):
		return []

	file_name = "{}_guides_{}".format(asset, name)
	version_object = pathlib.Version(directory, file_name, maya_file_extention)
	versions = version_object.get_versions()
	versions.insert(0, "latest")
	return versions
