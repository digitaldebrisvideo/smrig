import inspect
import logging
import os
from functools import partial

import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets, QtGui

from smrig import build
from smrig import env
from smrig.gui import mayawin
from smrig.gui.mel import prompts
from smrig.gui.tool import guideloader
from smrig.gui.tool import modelloader
from smrig.gui.tool import newstep
from smrig.gui.widget import header
from smrig.lib import decoratorslib
from smrig.lib import pathlib

log = logging.getLogger("smrig.gui.tool.guidebuild")

exec("""
try:
    from importlib import reload
except:
    pass
""")


class ArtistMain(QtWidgets.QWidget):
	stored_build_list = []
	style = "QTreeView::item { padding: 1px; } QTreeView{background-color: rgb(50,50,50)}"

	def __init__(self, parent=mayawin.maya_main_window):
		super(ArtistMain, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Artist Rig Build")

		self.build = build

		layout = QtWidgets.QGridLayout(self)

		self.header = header.Header(self, large=False, light_grey=True, title="Artist Rig Build Steps",
		                            info_icon="edit.png")
		self.header.help_button.setCheckable(True)
		self.header.help_button.toggled.connect(self.toggle_build_list_edit)

		# Model Button

		self.model_btn = QtWidgets.QPushButton("Set Model File to Start")
		self.model_btn.released.connect(self.launch_model_loader)
		self.model_btn.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		# item.line_edit = QtWidgets.QLineEdit(self)
		# item.unlock_checkbox = QtWidgets.QCheckBox(self)
		# item.soften_checkbox = QtWidgets.QCheckBox(self)
		# item.button = QtWidgets.QPushButton()
		# item.button.setIcon(QtGui.QIcon(get_icon_path("deleteActive.png")))
		# item.button.released.connect(partial(self.remove_item, item))
		# item.browse_button = QtWidgets.QPushButton()
		# item.browse_button.setIcon(QtGui.QIcon(get_icon_path("browse.png")))
		# item.browse_button.released.connect(partial(self.browse, item))
		# item.setSizeHint(0, QtCore.QSize(26, 26))

		# path_wdg = QtWidgets.QFrame(self)
		# path_layout = QtWidgets.QHBoxLayout(path_wdg)
		# path_label = QtWidgets.QLabel("Build List: ")
		# self.path_line = QtWidgets.QLineEdit(self)
		# self.path_line.setFocusPolicy(QtCore.Qt.NoFocus)
		# self.path_line.setReadOnly(True)

		# Build List

		path_wdg = QtWidgets.QFrame(self)
		path_layout = QtWidgets.QHBoxLayout(path_wdg)
		path_label = QtWidgets.QLabel("Build List: ")
		self.path_line = QtWidgets.QLineEdit(self)
		self.path_line.setFocusPolicy(QtCore.Qt.NoFocus)
		self.path_line.setReadOnly(True)

		# path_layout.addWidget(self.menu)
		path_layout.addWidget(path_label)
		path_layout.addWidget(self.path_line)
		path_layout.setContentsMargins(0, 0, 0, 0)
		path_wdg.setStyleSheet("QFrame{background-color: rgb(58, 58, 58)}")
		path_wdg.setFrameStyle(QtWidgets.QFrame.NoFrame)

		# model Loader

		# # file menu ------------------------------------------------
		# self.menu.setStyleSheet("QMenuBar{background-color: rgb(58, 58, 58)}")
		# self.file_menu = QtWidgets.QMenu("Settings")
		# self.menu.addMenu(self.file_menu)

		# action = QtWidgets.QAction(self)
		# action.setText("Set Guides To Load")
		# action.triggered.connect(self.launch_guide_loader)
		# self.file_menu.addAction(action)

		# build tree ----------------------------------------------

		self.tree = TreeWidget(self)
		self.tree.step_items = []
		self.tree.setColumnCount(4)

		self.tree.header().setMinimumSectionSize(20)
		self.tree.header().resizeSection(0, 20)
		self.tree.header().resizeSection(1, 25)
		self.tree.header().resizeSection(2, 100)
		self.tree.header().resizeSection(3, 80)

		style = "QHeaderView::section{background-color:#4d4d4d; color:#999; border: 0px solid #555}"
		self.tree.header().setStyleSheet(style)

		self.tree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode(2))
		self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode(1))
		self.tree.header().setSectionsMovable(False)
		self.tree.header().setMaximumHeight(14)
		self.tree.header().setStretchLastSection(False)
		self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
		self.tree.setHeaderLabels(["", "", "", "Status"])

		self.tree.setFocusPolicy(QtCore.Qt.NoFocus)
		self.tree.setFocusPolicy(QtCore.Qt.NoFocus)
		self.tree.setMinimumWidth(120)
		self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		self.tree.itemExpanded.connect(self.write_expanded_states)
		self.tree.itemCollapsed.connect(self.write_expanded_states)

		self.action1 = QtWidgets.QAction(self)
		self.action1.setText("Build Selected")
		self.action1.triggered.connect(self.build_selected)
		self.tree.addAction(self.action1)

		action = QtWidgets.QAction(self)
		action.setSeparator(True)
		self.tree.addAction(action)

		self.action2 = QtWidgets.QAction(self)
		self.action2.setText("Build Up To Selected Step")
		self.action2.triggered.connect(self.build_up_to_selected)
		self.tree.addAction(self.action2)

		self.action8 = QtWidgets.QAction(self)
		self.action8.setText("Restart && Build Up To Selected Step")
		self.action8.triggered.connect(partial(self.build_up_to_selected, restart=True))
		self.tree.addAction(self.action8)

		self.action5 = QtWidgets.QAction(self)
		self.action5.setText("Edit Selected Step")
		self.action5.triggered.connect(self.edit_build_step)
		self.tree.addAction(self.action5)

		action = QtWidgets.QAction(self)
		action.setSeparator(True)
		self.tree.addAction(action)

		self.action3 = QtWidgets.QAction(self)
		self.action3.setText("Add New Label")
		self.action3.triggered.connect(self.add_new_label)
		self.tree.addAction(self.action3)

		self.action4 = QtWidgets.QAction(self)
		self.action4.setText("Add New Build Step")
		self.action4.triggered.connect(self.add_new_build_step)
		self.tree.addAction(self.action4)

		action = QtWidgets.QAction(self)
		action.setSeparator(True)
		self.tree.addAction(action)

		self.action7 = QtWidgets.QAction(self)
		self.action7.setText("Remove Build Step")
		self.action7.triggered.connect(self.delete_step)
		self.tree.addAction(self.action7)

		action = QtWidgets.QAction(self)
		action.setSeparator(True)
		self.tree.addAction(action)

		self.action6 = QtWidgets.QAction(self)
		self.action6.setText("Revert Build List")
		self.action6.triggered.connect(self.revert_build_list_edits)
		self.tree.addAction(self.action6)

		self.build_next_btn = QtWidgets.QPushButton("Build Next Step")
		self.build_next_btn.released.connect(self.build_next)
		self.build_next_btn.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		self.build_all_btn = QtWidgets.QPushButton("Build All Steps")
		self.build_all_btn.released.connect(self.build_all)
		self.build_all_btn.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		action = QtWidgets.QAction(self)
		action.setText("Restart Build")
		action.triggered.connect(partial(self.build_next, restart=True))
		self.build_next_btn.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Rebuild All Steps")
		action.triggered.connect(partial(self.build_all, restart=True))
		self.build_all_btn.addAction(action)

		action = QtWidgets.QAction(self)
		action.setSeparator(True)
		self.tree.addAction(action)

		action3 = QtWidgets.QAction(self)
		action3.setText("Open File In Editor")
		action3.triggered.connect(self.edit_file)
		self.tree.addAction(action3)

		action = QtWidgets.QAction(self)
		action.setSeparator(True)
		self.tree.addAction(action)

		action3 = QtWidgets.QAction(self)
		action3.setText("Reload Build List")
		action3.triggered.connect(self.reload_ui)
		self.tree.addAction(action3)

		layout.addWidget(path_wdg, 0, 0, 1, 2)
		layout.addWidget(self.model_btn, 1, 0, 1, 2)
		layout.addWidget(self.header, 2, 0, 1, 2)
		layout.addWidget(self.tree, 3, 0, 1, 2)
		layout.addWidget(self.build_next_btn, 4, 0)
		layout.addWidget(self.build_all_btn, 4, 1)

		self.setLayout(layout)

		self.reload_ui()

	def launch_guide_loader(self, *args, **kwargs):
		"""

		:return:
		"""
		self.guide_wdg = guideloader.GuideLoader(self)
		self.guide_wdg.show()

	def launch_model_loader(self, *args, **kwargs):
		"""

		:return:
		"""
		self.model_wdg = modelloader.ModelLoader(self)
		self.model_wdg.show()

	def reload_ui(self):
		"""

		:return:
		"""
		build.manager.reload_manager()
		self.populate_path()
		self.populate_list()

		self.disable_build_list_edit()

		self.update_status()
		self.update_colors()

	def populate_path(self):
		"""

		:return:
		"""
		build_file = build.manager.build_file if build.manager.build_file else ""
		asset = env.asset.get_asset()
		if not asset:
			return

		if not build_file:
			text = "Build file does not exist."
			style = "QLineEdit{color: " + mayawin.red_color + "}"

		elif asset in build_file:
			text = build_file
			style = ""

		else:
			text = "Inheriting: {}".format(build_file)
			style = "QLineEdit{color: " + mayawin.yellow_color + "}"

		self.path_line.setText(text)
		self.path_line.setStyleSheet(style)

	def populate_list(self):
		"""

		:return:
		"""
		self.tree.blockSignals(True)

		self.tree.clear()
		self.tree.step_items = []

		parent_item = None
		for i, data in enumerate(build.manager.build_list):
			parent_item = self.add_step(i, parent_item=parent_item, **data)

		for i, item in enumerate(self.tree.step_items):
			item.setExpanded(bool(item.item_data.get("expanded")))

		self.tree.blockSignals(False)

	def browse(self, item):
		"""

		:param item:
		:return:
		"""
		file_path = cmds.fileDialog2(fileFilter=filters, dialogStyle=2, okc="Select", fm=1)
		if file_path:
			item.line_edit.setText(file_path[0])

	def add_step(self,
	             index,
	             enabled=None,
	             label=None,
	             item_type=None,
	             expanded=True,
	             status=None,
	             parent_item=None,
	             item_data=None,
	             *args,
	             **kwargs):
		"""

		:param index:
		:param enabled:
		:param label:
		:param item_type:
		:param expanded:
		:param status:
		:param parent_item:
		:param item_data:
		:param args:
		:param kwargs:
		:return:
		"""
		item = QtWidgets.QTreeWidgetItem()

		item.item_data = item_data if item_data else build.manager.build_list[index]
		item.item_name = ("build_step_{}".format(index))
		item.item_index = index
		item.parent_item = None
		item.children = []

		item.check_box = QtWidgets.QCheckBox(self)
		item.check_box.setChecked(enabled)

		if item_type == "label":
			item.setText(2, label)
			item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
			item.setExpanded(expanded)

			item.check_box.stateChanged.connect(partial(self.toggle_children_checks, item))
			item.check_box.stateChanged.connect(partial(self.write_check_states))

			bg_color = QtGui.QColor(60, 60, 60)
			item.setBackground(0, bg_color)
			item.setBackground(1, bg_color)
			item.setBackground(2, bg_color)
			item.setBackground(3, bg_color)

			self.tree.addTopLevelItem(item)
			parent_item = item

		else:
			item.setText(2, "   {}".format(label))
			item.setToolTip(2, "{}\n{}\n{}".format(item.item_data.get("import_code"),
			                                       item.item_data.get("command_code"),
			                                       item.item_data.get("file_path")))

			status = "" if status == "success" else status
			item.setText(3, status if status else "")
			item.setFlags(item.flags() & ~QtCore.Qt.ItemIsDropEnabled)

			item.check_box.stateChanged.connect(partial(self.write_check_states))

			if parent_item:
				item.parent_item = parent_item
				parent_item.addChild(item)
				parent_item.children.append(item)

			else:
				self.tree.addTopLevelItem(item)

		self.tree.setItemWidget(item, 1, item.check_box)
		self.tree.setStyleSheet(self.style)
		self.tree.step_items.append(item)

		return parent_item

	def set_wip_color(self, item):
		"""

		:param item:
		:return:
		"""
		color = QtGui.QColor('orange')
		item.setForeground(2, color)
		item.setForeground(3, color)

		if item.parent_item:
			item.parent_item.setForeground(2, color)
			item.parent_item.setForeground(3, color)

		QtCore.QCoreApplication.processEvents()

	def update_colors(self, clear=False, *args, **kwargs):
		"""

		:param clear:
		:param args:
		:param kwargs:
		:return:
		"""

		if not len(self.tree.step_items) == len(build.manager.build_list) == len(build.manager.status):
			return

		last_succeeded_index = None
		red_labels = []

		for index, status in enumerate(build.manager.status):
			color = mayawin.white_color
			self.tree.step_items[index].setForeground(2, QtGui.QColor(color))
			self.tree.step_items[index].setForeground(3, QtGui.QColor(color))

			if clear:
				if build.manager.build_list[index].get("item_type") == "label":
					color = "#999"
					self.tree.step_items[index].setForeground(2, QtGui.QColor(color))
					self.tree.step_items[index].setForeground(3, QtGui.QColor(color))

				continue

			elif status and build.manager.build_list[index].get("item_type") != "label" and status == "success":
				color = mayawin.dark_green_color
				last_succeeded_index = index

			elif build.manager.build_list[index].get("item_type") == "label" \
					and self.tree.step_items[index].text(3) == "Finished":
				color = mayawin.dark_green_color

			elif status and "Error" in status:
				color = mayawin.red_color

				if self.tree.step_items[index].parent_item:
					red_labels.append(self.tree.step_items[index].parent_item)

			elif status and "Exception" in status:
				color = mayawin.red_color

				if self.tree.step_items[index].parent_item:
					red_labels.append(self.tree.step_items[index].parent_item)

			elif build.manager.build_list[index].get("item_type") == "label":
				color = "#999"

			elif env.asset.get_asset() in build.manager.build_list[index].get("file_path", ""):
				color = mayawin.blue_color

			elif env.asset.get_inheritance():
				for iasset, ibuild in env.asset.get_inheritance():
					if ibuild and iasset in build.manager.build_list[index].get("file_path", ""):
						color = mayawin.yellow_color

			self.tree.step_items[index].setForeground(2, QtGui.QColor(color))
			self.tree.step_items[index].setForeground(3, QtGui.QColor(color))

		if last_succeeded_index:
			self.tree.step_items[last_succeeded_index].setForeground(2, QtGui.QColor(mayawin.green_color))
			self.tree.step_items[last_succeeded_index].setForeground(3, QtGui.QColor(mayawin.green_color))

		for label_item in red_labels:
			label_item.setForeground(2, QtGui.QColor(mayawin.red_color))
			label_item.setForeground(3, QtGui.QColor(mayawin.red_color))

	def update_status(self, clear=False, *args, **kwargs):
		"""

		:param clear:
		:param args:
		:param kwargs:
		:return:
		"""
		if not len(self.tree.step_items) == len(build.manager.build_list) == len(build.manager.status):
			return

		for index, status in enumerate(build.manager.status):
			status = "Finished" if status == "success" else status
			status = "" if clear else status

			self.tree.step_items[index].setText(3, status if status else "")
			if status and status != "Finished" and self.tree.step_items[index].parent_item:
				self.tree.step_items[index].parent_item.setText(3, status if status else "")
				self.update_label_status()
				return

		self.update_label_status()

	def update_label_status(self):
		"""

		:return:
		"""
		for parent in self.tree.step_items:
			if parent.item_data.get("item_type") == "label":
				status = []
				for child in parent.children:
					status.append(child.text(3))

				error_status = [s for s in reversed(status) if s not in ["", "Finished"]]
				label_status = error_status[0] if error_status else status[-1] if status else ""
				parent.setText(3, label_status)

	@decoratorslib.undoable
	def build_next(self, index=None, restart=False):
		"""

		:return:
		"""
		if restart:
			self.restart_build()
			self.populate_list()
			self.update_colors()
			self.update_status()

		if index:
			build.manager.current_step_index = index

		if build.manager.current_step_index > len(self.tree.step_items[:-1]):
			log.warning("Build is complete!")
			return

		if index is None:
			if self.tree.step_items[build.manager.current_step_index].item_data.get("item_type") == "label":
				build.manager.current_step_index += 1

		self.set_wip_color(self.tree.step_items[build.manager.current_step_index])

		try:
			build.manager.build_next_step()

		except Exception:
			self.update_status()
			self.update_colors()
			return

		self.update_status()
		self.update_colors()

		return True

	@decoratorslib.undoable
	@decoratorslib.refresh_viewport
	def build_all(self, restart=False):
		"""

		:return:
		"""
		if restart:
			self.restart_build()
			self.populate_list()
			self.update_colors()
			self.update_status()

		if build.manager.current_step_index > len(self.tree.step_items[:-1]):
			log.warning("Build is complete!")
			return

		for i in range(build.manager.current_step_index, len(self.tree.step_items), 1):
			if not self.build_next():
				QtCore.QCoreApplication.processEvents()
				return

			QtCore.QCoreApplication.processEvents()
			cmds.refresh()

	@decoratorslib.undoable
	@decoratorslib.refresh_viewport
	def build_selected(self):
		"""

		:return:
		"""
		if not self.tree.selectedItems():
			log.warning("No steps selected")
			return

		all_item_names = [i.item_name for i in self.tree.step_items]
		selected_item_indexes = [all_item_names.index(i.item_name) for i in self.tree.selectedItems()]
		selected_item_indexes.sort()

		for index in selected_item_indexes:
			if not self.build_next(index=index):
				QtCore.QCoreApplication.processEvents()
				return

			QtCore.QCoreApplication.processEvents()
			cmds.refresh()

	@decoratorslib.undoable
	@decoratorslib.refresh_viewport
	def build_up_to_selected(self, restart=False):
		"""

		:param restart:
		:return:
		"""
		if not self.tree.selectedItems():
			log.warning("No steps selected")
			return

		all_item_names = [i.item_name for i in self.tree.step_items]
		selected_item_indexes = [all_item_names.index(i.item_name) + 1 for i in self.tree.selectedItems()]
		selected_item_indexes.sort()

		if restart:
			self.restart_build()

		for index in range(build.manager.current_step_index, selected_item_indexes[-1]):
			if not self.build_next(index=index):
				QtCore.QCoreApplication.processEvents()
				return

			QtCore.QCoreApplication.processEvents()
			cmds.refresh()

	def restart_build(self):
		"""

		:return:
		"""
		if cmds.objExists(build.manager.status_node):
			cmds.delete(build.manager.status_node)

		self.reload_ui()

	def toggle_children_checks(self, item, *args, **kwargs):
		"""

		:return:
		"""
		children = item.children
		check_state = item.check_box.isChecked()
		for child in children:
			child.check_box.setChecked(check_state)

	def write_check_states(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		for idx, item in enumerate(self.tree.step_items):
			enabled = item.check_box.isChecked()
			build.manager.build_list[idx]["enabled"] = enabled

		build.manager.write_build_list()

	def write_expanded_states(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		for idx, item in enumerate(self.tree.step_items):
			expanded = item.isExpanded()
			build.manager.build_list[idx]["expanded"] = expanded

		build.manager.write_build_list()

	def save_build_list_edits(self):
		"""

		:return:
		"""
		self.tree.get_step_items()
		build.manager.build_list = []

		for idx, item in enumerate(self.tree.step_items):
			item_data = dict(item.item_data)
			item_data["label"] = item.text(2).strip()
			item_data["annotation"] = item.text(2).strip()
			item_data["enabled"] = item.check_box.isChecked()
			item_data["expanded"] = item.isExpanded()
			build.manager.build_list.append(item_data)

		build.manager.write_build_list()
		build.manager.reload_manager()

		self.restart_build()
		self.update_colors()
		self.update_status()

		log.debug("Wrote build list edits to disk")

	def toggle_build_list_edit(self):
		"""

		:return:
		"""
		if self.header.help_button.isChecked():
			self.stored_build_list = list(build.manager.build_list)
			self.enable_build_list_edit()

		else:
			self.disable_build_list_edit()
			self.save_build_list_edits()

	def enable_build_list_edit(self):
		"""

		:return:
		"""
		self.tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
		self.tree.setStyleSheet("QTreeView::item { padding: 1px; } QTreeView{background-color: rgb(80,40,60)}")
		# self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

		self.header.label.setText("Rig Build Steps: EDIT MODE")
		self.header.label.setStyleSheet("color:" + mayawin.red_color)

		self.action1.setVisible(False)
		self.action2.setVisible(False)
		self.action8.setVisible(False)
		self.action3.setVisible(True)
		self.action4.setVisible(True)
		self.action5.setVisible(True)
		self.action6.setVisible(True)
		self.action7.setVisible(True)

		self.build_next_btn.setEnabled(False)
		self.build_all_btn.setEnabled(False)

		for item in self.tree.step_items:
			item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

		self.update_colors(clear=True)
		self.update_status(clear=True)

		self.header.help_button.blockSignals(True)
		self.header.help_button.setChecked(True)
		self.header.help_button.blockSignals(False)
		self.header.help_button.setIcon(QtGui.QIcon(mayawin.get_icon_path("save.png")))

	def disable_build_list_edit(self, write=True, *args, **kwargs):
		"""

		:return:
		"""
		self.tree.get_step_items()
		self.tree.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
		self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.tree.setStyleSheet(self.style)

		self.header.label.setText("Rig Build Steps")
		self.header.label.setStyleSheet("")

		self.action1.setVisible(True)
		self.action2.setVisible(True)
		self.action8.setVisible(True)
		self.action3.setVisible(False)
		self.action4.setVisible(False)
		self.action5.setVisible(False)
		self.action6.setVisible(False)
		self.action7.setVisible(False)

		self.build_next_btn.setEnabled(True)
		self.build_all_btn.setEnabled(True)

		for item in self.tree.step_items:
			item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)

		self.update_colors(clear=True)
		self.update_status(clear=True)

		self.header.help_button.blockSignals(True)
		self.header.help_button.setChecked(False)
		self.header.help_button.blockSignals(False)
		self.header.help_button.setIcon(QtGui.QIcon(mayawin.get_icon_path("edit.png")))

	def add_new_label(self):
		"""

		:return:
		"""
		item_data = {
			"annotation": "New Rig label",
			"cache": False,
			"command_code": "",
			"enabled": True,
			"expanded": True,
			"import_code": "",
			"item_type": "label",
			"label": "New Rig Label"
		}
		self.tree.get_step_items()
		self.add_step(len(self.tree.step_items), item_data=item_data, **item_data)
		self.save_build_list_edits()
		self.enable_build_list_edit()

	def add_new_build_step(self):
		"""

		:param label:
		:return:
		"""
		result = newstep.NewStep()
		result.exec_()

		if not result.do_it:
			return

		item_data = {
			"annotation": result.label,
			"cache": False,
			"command_code": result.command_code,
			"enabled": True,
			"expanded": True,
			"import_code": result.import_code,
			"item_type": result.item_type,
			"label": result.label
		}
		self.tree.get_step_items()
		self.add_step(len(self.tree.step_items), item_data=item_data, **item_data)
		self.save_build_list_edits()
		self.enable_build_list_edit()

	def edit_build_step(self):
		"""

		:param label:
		:return:
		"""
		self.tree.get_step_items()
		item = self.tree.selectedItems()
		if not item:
			log.warning("No step selected.")
			return

		if item[0].item_data.get("item_type") == "label":
			log.warning("Double click on label text to edit.")
			return

		result = newstep.NewStep(label=item[0].text(2),
		                         import_code=item[0].item_data.get("import_code"),
		                         command_code=item[0].item_data.get("command_code"),
		                         item_type=item[0].item_data.get("item_type"))
		result.exec_()

		if not result.do_it:
			return

		item_data = {
			"annotation": result.label,
			"command_code": result.command_code,
			"import_code": result.import_code,
			"item_type": result.item_type,
			"label": result.label
		}

		item[0].item_data.update(item_data)
		item[0].setText(2, result.label)
		self.save_build_list_edits()
		self.enable_build_list_edit()

	def delete_step(self):
		"""

		:return:
		"""

		self.tree.get_step_items()
		item = self.tree.selectedItems()[0]
		if not item:
			log.warning("No step selected.")
			return

		if item.parent_item:
			item.parent_item.takeChild(item.parent_item.indexOfChild(item))
		else:
			if item.childCount():
				message = "This label has items under it,\nthey will be deleted as well."
				if prompts.confirm_dialog(title="smrig | Delete Step", message=message):
					self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
			else:
				self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))

	def revert_build_list_edits(self):
		"""

		:return:
		"""
		build.manager.build_list = list(self.stored_build_list)
		build.manager.write_build_list()
		self.reload_ui()

	def edit_file(self):
		"""

		:return:
		"""
		item = self.tree.selectedItems()
		if not item:
			log.warning("No step selected.")
			return

		if item[0].item_data.get("item_type") == "label":
			return

		import_code = item[0].item_data.get("import_code")
		command_code = item[0].item_data.get("command_code")
		item_type = item[0].item_data.get("item_type")

		try:
			if item_type.lower() == "python":
				exec("{}".format(import_code))
				exec("reload({})".format(import_code.split(" ")[-1]))

				try:
					module = eval(command_code.split("(")[0])
				except:
					module = eval(".".join(command_code.split(".")[:-1]))

				module = inspect.getmodule(module)
				file_path = inspect.getfile(module).replace(".pyc", ".py")

				if os.path.isfile(file_path):
					pathlib.open_in_text_editor(file_path)

			elif item_type.lower() == "mel":
				log.warning("MEL files not currently supported by edit_file function.")

		except:
			log.error("Cannot find file path!")


class TreeWidget(QtWidgets.QTreeWidget):

	def __init__(self, parent=None):
		super(TreeWidget, self).__init__(parent)
		self.step_items = []

	def dropEvent(self, event):
		"""

		:param event:
		:return:
		"""
		super(TreeWidget, self).dropEvent(event)
		self.get_step_items()
		self.update_checks()

	def get_step_items(self):
		"""

		:return:
		"""
		self.step_items = []
		for i in range(self.topLevelItemCount()):
			item = self.topLevelItem(i)
			item.children = []
			item.setText(2, item.text(2).strip())

			self.step_items.append(item)
			for ci in range(item.childCount()):
				c_item = item.child(ci)
				c_item.setText(2, "    " + c_item.text(2).strip())
				c_item.parent_item = item
				item.children.append(c_item)
				self.step_items.append(c_item)

		for i, item in enumerate(self.step_items):
			item.item_index = i

	def update_checks(self):
		"""

		:return:
		"""
		for i, item in enumerate(self.step_items):
			item.check_box = QtWidgets.QCheckBox(self)
			item.check_box.setChecked(item.item_data.get("enabled"))
			self.setItemWidget(item, 1, item.check_box)

		self.setStyleSheet(self.styleSheet())


def run():
	"""

	:return: Qt widget object
	"""
	ui = ArtistMain()
	ui.show()
	return ui
