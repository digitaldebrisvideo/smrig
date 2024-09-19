import os
from functools import partial

import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path, red_color
from smrig.gui.mel import prompts
from smrig.gui.tool import inheritsettings
from smrig.lib import pathlib
from smrig.userprefs import USE_FACILITY_PIPELINE


class AssetEnv(QtWidgets.QFrame):
	post_function = None

	def __init__(self, parent=maya_main_window):
		super(AssetEnv, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)

		layout = QtWidgets.QGridLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)

		self.job_cmb = QtWidgets.QComboBox(self)
		self.asset_cmb = QtWidgets.QComboBox(self)
		self.variant_cmb = QtWidgets.QComboBox(self)

		self.build_path_line = QtWidgets.QLineEdit(self)
		self.build_path_line.setReadOnly(True)

		self.data_path_line = QtWidgets.QLineEdit(self)
		self.data_path_line.setReadOnly(True)

		self.build_path_btn = QtWidgets.QPushButton(self)
		self.build_path_btn.setIcon(QtGui.QIcon(get_icon_path("browse.png")))
		self.build_path_btn.setMaximumWidth(32)

		self.data_path_btn = QtWidgets.QPushButton(self)
		self.data_path_btn.setIcon(QtGui.QIcon(get_icon_path("browse.png")))
		self.data_path_btn.setMaximumWidth(32)

		self.inheritance_btn = QtWidgets.QPushButton(self)
		self.inheritance_btn.setIcon(QtGui.QIcon(get_icon_path("inherit.png")))
		self.inheritance_btn.setMaximumWidth(32)
		self.inheritance_btn.released.connect(self.inhertance_ui)

		job_label = QtWidgets.QLabel("Job:")
		asset_label = QtWidgets.QLabel("Asset:")
		variant_label = QtWidgets.QLabel("Variant:")
		build_path_label = QtWidgets.QLabel("Path:")
		data_path_label = QtWidgets.QLabel("Data Path:")

		layout.addWidget(job_label, 0, 0)
		layout.addWidget(self.job_cmb, 0, 1)
		layout.addWidget(asset_label, 0, 2)
		layout.addWidget(self.asset_cmb, 0, 3)
		layout.addWidget(variant_label, 0, 4)
		layout.addWidget(self.variant_cmb, 0, 5)
		layout.addWidget(self.inheritance_btn, 0, 6)
		layout.addWidget(build_path_label, 1, 0)
		layout.addWidget(self.build_path_line, 1, 1, 1, 5)
		layout.addWidget(self.build_path_btn, 1, 6)
		layout.addWidget(data_path_label, 2, 0)
		layout.addWidget(self.data_path_line, 2, 1, 1, 5)
		layout.addWidget(self.data_path_btn, 2, 6)

		layout.setColumnStretch(0, 0)
		layout.setColumnStretch(1, 1)
		layout.setColumnStretch(2, 0)
		layout.setColumnStretch(3, 1)
		layout.setColumnStretch(4, 0)
		layout.setColumnStretch(5, 1)
		layout.setColumnStretch(6, 0)

		current_job = env.get_job()
		current_asset = env.asset.get_asset()
		current_variant = env.asset.get_variant()

		# connections -----------------------------------------------------
		self.build_path_btn.released.connect(partial(self.browse_path, self.build_path_line))
		self.data_path_btn.released.connect(partial(self.browse_path, self.data_path_line))

		self.job_cmb.currentIndexChanged.connect(self.set_job)
		self.asset_cmb.currentIndexChanged.connect(self.set_asset)
		self.variant_cmb.currentIndexChanged.connect(self.set_variant)

		self.job_cmb.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		self.asset_cmb.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		self.variant_cmb.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		if not USE_FACILITY_PIPELINE:
			item = QtWidgets.QAction(self)
			item.setText('Create New Job')
			item.triggered.connect(self.create_job)
			self.job_cmb.addAction(item)

			item = QtWidgets.QAction(self)
			item.setText('Create New Asset')
			item.triggered.connect(self.create_asset)
			self.asset_cmb.addAction(item)

			div = QtWidgets.QAction(self)
			div.setSeparator(True)
			self.asset_cmb.addAction(div)

			item = QtWidgets.QAction(self)
			item.setText('Recreate Asset Files')
			item.triggered.connect(self.create_asset_files)
			self.asset_cmb.addAction(item)

		else:
			item = QtWidgets.QAction(self)
			item.setText('Create Asset Files')
			item.triggered.connect(self.create_asset_files)
			self.asset_cmb.addAction(item)

		item = QtWidgets.QAction(self)
		item.setText('Create New Variant')
		item.triggered.connect(self.create_variant)
		self.variant_cmb.addAction(item)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.variant_cmb.addAction(div)

		item = QtWidgets.QAction(self)
		item.setText('Delete Variant')
		item.triggered.connect(self.delete_variant)
		self.variant_cmb.addAction(item)

		# setup --------------------------------------------------------
		self.list_jobs()
		self.list_assets()
		self.list_variants()

		self.job_cmb.setCurrentText(current_job)
		self.asset_cmb.setCurrentText(current_asset)
		self.variant_cmb.setCurrentText(current_variant)

		self.data_path_line.hide()
		self.data_path_btn.hide()
		data_path_label.hide()

	def list_jobs(self):
		"""
		List jobs in gui

		:return:
		"""
		self.job_cmb.clear()
		self.job_cmb.addItems(env.get_jobs() or [])

	def list_assets(self):
		"""
		List assets

		:return:
		"""
		env.reload_assets()
		self.asset_cmb.clear()
		self.asset_cmb.addItems(env.get_assets() or [])

	def list_variants(self):
		"""

		:return:
		"""
		self.variant_cmb.clear()
		self.variant_cmb.addItems(env.asset.get_variants() or [])

	def set_job(self):
		"""

		:return:
		"""

		job = self.job_cmb.currentText() if self.job_cmb.currentText() else None

		env.set_job(job)

		self.list_assets()
		self.list_variants()

	def set_asset(self):
		"""

		:return:
		"""
		asset = self.asset_cmb.currentText() if self.asset_cmb.currentText() else None
		env.asset.set_asset(asset)

		self.list_variants()

	def set_variant(self):
		"""

		:return:
		"""
		variant = self.variant_cmb.currentText() if self.variant_cmb.currentText() else None
		env.asset.set_variant(variant)

		self.set_paths()

	def set_paths(self):
		"""

		:return:
		"""
		self.build_path_line.setText(env.asset.get_rigbuild_path())
		self.data_path_line.setText(env.asset.get_data_path())
		self.set_path_colors()

	def set_path_colors(self):
		"""

		:return:
		"""
		path = env.asset.get_rigbuild_path()
		if os.path.isdir(path):
			self.build_path_line.setStyleSheet("")
		else:
			self.build_path_line.setStyleSheet("color: {}".format(red_color))

		path = env.asset.get_data_path()
		if os.path.isdir(path):
			self.data_path_line.setStyleSheet("")
		else:
			self.data_path_line.setStyleSheet("color: {}".format(red_color))

	def create_job(self):
		"""

		:return:
		"""
		result = cmds.promptDialog(
			title="Create New Job",
			message="Job Name:",
			button=["Create", "Cancel"],
			defaultButton="Create",
			cancelButton="Cancel",
			dismissString="Cancel")

		if result == "Create":
			name = cmds.promptDialog(query=True, text=True)
			env.create_job(name)

			self.list_jobs()
			self.job_cmb.setCurrentText(name)

	def create_asset(self):
		"""

		:return:
		"""
		result = cmds.promptDialog(
			title="Create New Asset",
			message="Asset Name:",
			button=["Create", "Cancel"],
			defaultButton="Create",
			cancelButton="Cancel",
			dismissString="Cancel")

		if result == "Create":
			name = cmds.promptDialog(query=True, text=True)
			env.create_asset(name)

			self.list_assets()
			self.asset_cmb.setCurrentText(name)

	def create_variant(self):
		"""

		:return:
		"""
		result = cmds.promptDialog(
			title="Create New Variant",
			message="Variant Name:",
			button=["Create", "Cancel"],
			defaultButton="Create",
			cancelButton="Cancel",
			dismissString="Cancel")

		if result == "Create":
			name = cmds.promptDialog(query=True, text=True)
			env.asset.add_variant(name)

			self.list_variants()
			self.variant_cmb.setCurrentText(name)

	def create_asset_files(self):
		"""

		:return:
		"""
		env.asset.create_rig_files()
		self.set_paths()

	def delete_variant(self):
		"""

		:return:
		"""
		variant = self.variant_cmb.currentText()
		if variant == env.assets.DEFAULT_VARIANT:
			cmds.warning("Cannot remove {} variant".format(env.assets.DEFAULT_VARIANT))
			return

		if prompts.confirm_dialog(title="Delete Variant",
		                          icon="warning",
		                          message="Delete variant: {}\n\nAre you sure?".format(variant)):
			env.asset.remove_variant(variant)
			self.list_variants()

	def inhertance_ui(self):
		"""

		:return:
		"""
		self.inherit_wdg = inheritsettings.InheritSettings(self)
		self.inherit_wdg.post_function = self.post_function
		self.inherit_wdg.show()

	def browse_path(self, line_edit):
		"""

		:param line_edit:
		:return:
		"""
		self.set_path_colors()

		path = line_edit.text()
		if os.path.isdir(path):
			pathlib.open_in_browser(path)
