import logging
import random
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig import partslib
from smrig.build import guide
from smrig.build import model
from smrig.build import rig
from smrig.build import skeleton
from smrig.env import prefs
from smrig.gui import mayawin
from smrig.gui.mayawin import maya_main_window, get_icon_path, white_color
from smrig.gui.tool import cleanmodel
from smrig.gui.tool import guideloader, mirrorpart, duplicatepart, modelloader, newtemplate
from smrig.gui.widget import header, partsfilterlist, partpicker
from smrig.gui.widget import newpart
from smrig.lib import decoratorslib
from smrig.lib import spaceslib
from smrig.lib import utilslib

log = logging.getLogger("smrig.gui.tool.guidebuild")


class GuideBuild(QtWidgets.QWidget):

	def __init__(self, parent=maya_main_window):
		super(GuideBuild, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Guides")

		layout = QtWidgets.QVBoxLayout(self)

		list_frame = QtWidgets.QFrame(self)
		list_layout = QtWidgets.QVBoxLayout(self)
		list_frame.setLayout(list_layout)
		list_layout.setContentsMargins(0, 0, 0, 0)

		options_frame = QtWidgets.QFrame(self)
		options_layout = QtWidgets.QGridLayout(self)
		options_frame.setLayout(options_layout)
		options_layout.setContentsMargins(0, 0, 0, 0)

		self.splitter = QtWidgets.QSplitter(self)
		self.splitter.addWidget(list_frame)
		self.splitter.addWidget(options_frame)
		self.splitter.setSizes([100, 300])

		g_header = header.Header(self, large=False, light_grey=True, title="Parts In Scene", info_button=False)
		self.o_header = header.Header(self, large=False, light_grey=True, title="Build Options", info_button=True)
		self.o_header.help_button.setIcon(QtGui.QIcon(mayawin.get_icon_path("edit.png")))
		self.o_header.part_obj = None

		self.filter_list = partsfilterlist.PartsFilterListWidget(self, self)
		self.filter_list.list.itemSelectionChanged.connect(self.populate_options_from_selected)
		self.filter_list.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.filter_list.list.itemDoubleClicked.connect(self.select_guides)

		reload_btn = QtWidgets.QPushButton("Refresh Parts List")
		reload_btn.released.connect(self.list_parts)

		# file menu ------------------------------------------------
		self.menu = QtWidgets.QMenuBar(self)
		self.menu.setStyleSheet("QMenuBar{background-color: rgb(58, 58, 58)}")

		self.file_menu = QtWidgets.QMenu("File")
		self.file_menu.setObjectName("smrigFileMenu{}".format(random.randint(0, 999999)))
		self.menu.addMenu(self.file_menu)

		cmds.menuItem(label="Load Guides", parent=self.file_menu.objectName(), command=self.load_guides)
		cmds.menuItem(optionBox=True, parent=self.file_menu.objectName(), command=self.launch_guide_loader)

		cmds.menuItem(label="Load Models", parent=self.file_menu.objectName(), command=self.load_models)
		cmds.menuItem(optionBox=True, parent=self.file_menu.objectName(), command=self.launch_model_loader)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.file_menu.addAction(div)

		cmds.menuItem(label="Save Guides", parent=self.file_menu.objectName(), command=self.save_guides)
		cmds.menuItem(optionBox=True, parent=self.file_menu.objectName(), command=self.save_guide_options)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.file_menu.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Save As Template")
		action.triggered.connect(self.save_template)
		self.file_menu.addAction(action)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.file_menu.addAction(div)

		cmds.menuItem(label="Clean Model", parent=self.file_menu.objectName(), command=model.clean)
		cmds.menuItem(optionBox=True, parent=self.file_menu.objectName(), command=self.clean_model_options)

		cmds.menuItem(label="Save Model", parent=self.file_menu.objectName(), command=model.save_scene)
		cmds.menuItem(optionBox=True, parent=self.file_menu.objectName(), command=self.save_model_options)

		# modify menu ------------------------------------------------
		self.picker_menu = partpicker.PartPicker(self, self).menu
		self.picker_menu.setTitle("Create")
		self.menu.addMenu(self.picker_menu)

		# modify menu ------------------------------------------------
		self.modify_menu = QtWidgets.QMenu("Modify")
		self.modify_menu.setObjectName("smrigModifyMenu{}".format(random.randint(0, 999999)))
		self.menu.addMenu(self.modify_menu)

		cmds.menuItem(label="Mirror Parts", parent=self.modify_menu.objectName(), command=self.mirror_part)
		cmds.menuItem(optionBox=True, parent=self.modify_menu.objectName(), command=self.mirror_part_options)

		action = QtWidgets.QAction(self)
		action.setText("Mirror Parts")
		action.triggered.connect(self.mirror_part)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Duplicate Parts")
		action.triggered.connect(self.duplicate_options)
		self.modify_menu.addAction(action)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Rebuild Parts")
		action.triggered.connect(partial(self.modify_parts, "rebuild"))
		self.modify_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.modify_menu.addAction(div)
		self.filter_list.list.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Delete Parts")
		action.triggered.connect(partial(self.modify_parts, "delete"))
		self.modify_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setText("Components Visibility")
		div.setSeparator(True)
		self.filter_list.list.addAction(div)

		# view menu ------------------------------------------------
		self.view_menu = QtWidgets.QMenu("View")
		self.menu.addMenu(self.view_menu)

		action = QtWidgets.QAction(self)
		action.setText("Joints Visibility")
		action.triggered.connect(partial(self.toggle, "jointsVisibility", selected=True, unselected=False))
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Controls Visibility")
		action.triggered.connect(partial(self.toggle, "controlsVisibility", selected=True, unselected=False))
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Joints Display Local Axis")
		action.triggered.connect(partial(self.toggle, "jointDisplayLocalAxis", selected=True, unselected=False))
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Controls Display Local Axis")
		action.triggered.connect(partial(self.toggle, "controlDisplayLocalAxis", selected=True, unselected=False))
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setText("Parts Visibility")
		div.setSeparator(True)
		self.view_menu.addAction(div)
		self.filter_list.list.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Visibility Selected Parts")
		action.triggered.connect(partial(self.toggle, "visibility", selected=True, unselected=False))
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Visibility Unselected Parts")
		action.triggered.connect(partial(self.toggle, "visibility", selected=False, unselected=True))
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.view_menu.addAction(div)
		self.filter_list.list.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Unhide All Parts")
		action.triggered.connect(partial(self.toggle, "visibility", selected=False, unselected=False, value=1))
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setText("UI")
		div.setSeparator(True)
		self.view_menu.addAction(div)
		self.filter_list.list.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Refresh Parts List")
		action.triggered.connect(self.list_parts)
		self.view_menu.addAction(action)
		self.filter_list.list.addAction(action)

		# view menu ------------------------------------------------
		self.dev_menu = QtWidgets.QMenu("Develop")
		self.menu.addMenu(self.dev_menu)

		action = QtWidgets.QAction(self)
		action.setText("Quick Build")
		action.triggered.connect(self.quick_build)
		self.dev_menu.addAction(action)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Quick Finish")
		action.triggered.connect(self.quick_finish_build)
		self.dev_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.dev_menu.addAction(div)
		self.filter_list.list.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Build Skeleton")
		action.triggered.connect(skeleton.build)
		self.dev_menu.addAction(action)
		self.filter_list.list.addAction(action)

		action = QtWidgets.QAction(self)
		action.setText("Build Rigs")
		action.triggered.connect(partslib.build_rigs)
		self.dev_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.dev_menu.addAction(div)
		self.filter_list.list.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Create New Part Module")
		action.triggered.connect(self.create_new_part)
		self.dev_menu.addAction(action)
		self.filter_list.list.addAction(action)

		div = QtWidgets.QAction(self)
		div.setSeparator(True)
		self.dev_menu.addAction(div)
		self.filter_list.list.addAction(div)

		action = QtWidgets.QAction(self)
		action.setText("Reload Parts Library")
		action.triggered.connect(partial(utilslib.py.reload_hierarchy, partslib))
		self.dev_menu.addAction(action)
		self.filter_list.list.addAction(action)

		# buttons -----------------------------------------------------------
		self.update_btn = QtWidgets.QPushButton("Update Build Options")
		self.update_btn.released.connect(self.update_options)
		self.update_btn.setEnabled(False)

		self.build_btn = QtWidgets.QPushButton("Build New Part")
		self.build_btn.setEnabled(False)
		self.build_btn.released.connect(self.build_guide_part)

		self.tree = QtWidgets.QTreeWidget(self)
		self.tree.value_items = []
		self.tree.setColumnCount(4)
		self.tree.setIndentation(0)
		self.tree.header().resizeSection(0, 60)
		self.tree.header().setMinimumSectionSize(10)
		self.tree.header().resizeSection(1, 10)
		self.tree.header().resizeSection(2, 110)
		self.tree.header().resizeSection(3, 40)
		self.tree.header().setStretchLastSection(False)
		self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
		self.tree.setHeaderHidden(True)
		self.tree.setFocusPolicy(QtCore.Qt.NoFocus)
		self.tree.setMinimumWidth(120)

		style = "QTreeView{background-color:rgb(55, 55, 55);} "
		self.tree.setStyleSheet(style)
		self.tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

		list_layout.addWidget(g_header)
		list_layout.addWidget(self.filter_list)
		list_layout.addWidget(reload_btn)

		options_layout.addWidget(self.o_header, 0, 0, 1, 2)
		options_layout.addWidget(self.tree, 1, 0, 1, 2)
		options_layout.addWidget(self.update_btn, 2, 1)
		options_layout.addWidget(self.build_btn, 2, 0)
		options_layout.setVerticalSpacing(11)

		layout.addWidget(self.menu)
		layout.addWidget(self.splitter)

		layout.setStretch(0, 0)
		layout.setStretch(1, 1)

		self.setLayout(layout)
		self.filter_list.field.textChanged.connect(self.list_parts)
		self.list_parts()

		self.setTabOrder(self.filter_list.list, self.tree)
		self.setTabOrder(self.tree, self.build_btn)

	def create_part(self):
		"""

		:return:
		"""

		self.part_picker = partpicker.run(self.filter_list.list, self)

		win_point = self.part_picker.parentWidget().window().frameGeometry().topLeft()
		wdg_point = QtCore.QPoint(50, 250)
		self.part_picker.move(win_point + wdg_point)

		self.populate_new_part(self.part_picker.part, self.part_picker.template)

	def select_guides(self):
		"""

		:return:
		"""
		guide_grps = cmds.ls([i.text() for i in self.filter_list.list.selectedItems()])
		if guide_grps:
			cmds.select(guide_grps)

	def highlight_selected_guides(self):
		"""

		:return:
		"""
		nodes = [partslib.utils.find_guide_group_from_selection(n) for n in cmds.ls(sl=1)]
		for idx in range(self.filter_list.list.count()):
			item = self.filter_list.list.item(idx)
			value = True if item.text() in nodes else False
			self.filter_list.list.setItemSelected(item, value)

	def list_parts(self):
		"""

		:return:
		"""
		filter = self.filter_list.field.text().lower().strip()
		guides = [g for g in partslib.utils.get_guides_in_scene() if filter in g.lower()]

		self.filter_list.list.clear()
		self.tree.clear()
		self.filter_list.list.addItems(guides)
		self.color_items()
		self.highlight_selected_guides()
		self.filter_list.list.setStyleSheet("QListView:item { padding: 1px; }")

	def color_items(self):
		"""

		:return:
		"""
		all_items = [self.filter_list.list.item(i) for i in range(self.filter_list.list.count())]
		values = [cmds.getAttr("{}.visibility".format(i.text())) for i in all_items]

		for item, value in zip(all_items, values):
			if value:
				item.setForeground(QtGui.QColor(white_color))
			else:
				item.setForeground(QtGui.QColor("grey"))

	def populate_options_from_selected(self):
		"""

		:return:
		"""
		item = self.filter_list.list.selectedItems()
		self.clear_tree()

		if not item or len(item) > 1:
			return

		guide_grp = item[0].text()
		part_obj = partslib.part(guide_grp)

		if not part_obj or not guide_grp:
			return

		self.o_header.label.setText("Build Options: " + part_obj.part_type)
		self.o_header.part_obj = part_obj
		self.o_header.set_link(part_obj.path)

		option_names = part_obj.sorted_option_names
		options = part_obj.options

		for name in option_names:
			self.add_option_item(name, **options[name])

	def populate_new_part(self, name, template):
		"""

		:return:
		"""
		if template:
			partslib.build_template(name, build=True)

		else:
			self.clear_tree()
			part_obj = partslib.part(name)
			if not part_obj:
				return

			self.o_header.label.setText("Build Options: New " + part_obj.part_type)
			self.o_header.part_obj = part_obj
			self.o_header.set_link(part_obj.path)

			option_names = part_obj.sorted_option_names
			options = part_obj.options

			for name in option_names:
				self.add_option_item(name, **options[name])

			self.build_btn.setEnabled(True)
			self.build_btn.setDefault(True)

	def clear_tree(self):
		"""

		:return:
		"""
		self.tree.clear()
		self.o_header.label.setText("Build Options")
		self.o_header.part_obj = None
		self.o_header.set_link(None)
		self.build_btn.setEnabled(False)
		self.update_btn.setEnabled(False)
		self.tree.value_items = []

		self.update_btn.setDefault(False)
		self.build_btn.setDefault(False)

	def add_option_item(self, name, **kwargs):
		"""

		:param name:
		:param kwargs:
		:return:
		"""
		if not kwargs.get("editable"):
			return

		item = QtWidgets.QTreeWidgetItem()
		item.setToolTip(0, kwargs.get("tool_tip"))
		item.setToolTip(1, kwargs.get("tool_tip"))
		item.setToolTip(2, kwargs.get("tool_tip"))
		item.setSizeHint(0, QtCore.QSize(26, 26))
		item.option_name = name
		item.value_field = None
		item.button = None

		self.tree.addTopLevelItem(item)

		# set label -----------------------------------
		item.label = QtWidgets.QLabel(name + "\t")
		self.tree.setItemWidget(item, 0, item.label)

		if kwargs.get("value_required"):
			item.setText(1, "*")
			item.setForeground(1, QtGui.QColor("#ff6a45"))

		# create widget -------------------------------
		data_type = kwargs.get("data_type")
		s_data_types = ["string", "single_selection", "selection", "parent_driver", "attribute_driver", "rig_part"]
		b_data_types = ["single_selection", "selection", "parent_driver", "attribute_driver", "rig_part"]

		if data_type == "bool":
			item.value_field = QtWidgets.QCheckBox(self)
			item.value_field.setChecked(kwargs.get("value"))
			self.tree.setItemWidget(item, 2, item.value_field)

			item.value_field.stateChanged.connect(self.enable_update_btn)

		elif data_type == "int":
			item.value_field = QtWidgets.QSpinBox(self)
			item.value_field.setMinimum(kwargs.get("min") or 0)
			item.value_field.setMaximum(kwargs.get("max") or 99999)
			item.value_field.setValue(kwargs.get("value"))
			self.tree.setItemWidget(item, 2, item.value_field)

			item.value_field.valueChanged.connect(self.enable_update_btn)

		elif data_type == "float":
			item.value_field = QtWidgets.QDoubleSpinBox(self)
			item.value_field.setMinimum(kwargs.get("min") or 0.0)
			item.value_field.setMaximum(kwargs.get("max") or 99999.0)
			item.value_field.setValue(kwargs.get("value"))
			self.tree.setItemWidget(item, 2, item.value_field)

			item.value_field.valueChanged.connect(self.enable_update_btn)

		elif data_type == "enum":
			item.value_field = QtWidgets.QComboBox(self)
			item.value_field.addItems(kwargs.get("enum").split(":") or [])
			item.value_field.setCurrentText(kwargs.get("value"))
			self.tree.setItemWidget(item, 2, item.value_field)

			item.value_field.currentIndexChanged.connect(self.enable_update_btn)

		elif data_type in s_data_types:
			item.value_field = QtWidgets.QLineEdit(self)
			item.value_field.setText(str(kwargs.get("value")) or "")
			self.tree.setItemWidget(item, 2, item.value_field)
			item.value_field.textChanged.connect(self.enable_update_btn)

		if data_type in b_data_types:
			single_selection = False if kwargs.get("data_type") == "selection" else True

			rig_part = True if data_type == "rig_part" else False
			item.button = QtWidgets.QPushButton()
			item.button.setMaximumWidth(50)
			item.button.released.connect(partial(self.set_field_selection,
			                                     item.value_field,
			                                     single_selection,
			                                     rig_part))

			item.button.setIcon(QtGui.QIcon(get_icon_path("select.png")))
			item.setToolTip(3, "Set Selected")
			self.tree.setItemWidget(item, 3, item.button)

		item.value_field.option_name = name
		self.tree.value_items.append(item.value_field)

		style = "QTreeView::item { padding: 1px 4px 1px 4px; background-color:rgb(55, 55, 55)}"
		style += "QComboBox{background-color:rgb(75,75,75)}"
		style += "QTreeView{background-color:rgb(55, 55, 55);}"

		self.tree.setStyleSheet(style)
		self.tree.resizeColumnToContents(0)
		self.tree.header().resizeSection(3, 40)

	def enable_update_btn(self):
		"""

		:return:
		"""
		self.update_btn.setEnabled(False)
		self.update_btn.setDefault(False)

		if "New" in self.o_header.label.text():
			return

		item = self.filter_list.list.selectedItems()
		if not item or len(item) > 1:
			return

		part_obj, options = self.get_options_data()
		if not part_obj or not options:
			return

		self.update_btn.setEnabled(True)
		self.update_btn.setDefault(True)

	def get_options_data(self):
		"""

		:return:
		"""
		part_obj = self.o_header.part_obj
		if not part_obj:
			return None, None

		items = self.tree.value_items
		options = part_obj.options
		result = {}

		for item in items:
			name = item.option_name
			data_type = options.get(name).get("data_type")

			if data_type == "bool":
				value = item.isChecked()

			elif data_type in ["int", "float"]:
				value = item.value()

			elif data_type == "enum":
				value = item.currentText()

			elif data_type == "selection":
				try:
					value = eval(item.text())
				except:
					value = []

			elif data_type == "rig_part":
				value = item.text()
				if cmds.objExists(value):
					value = partslib.utils.find_guide_group_from_selection(value)

			elif data_type in ["string", "single_selection", "parent_driver", "attribute_driver"]:
				value = str(item.text() or "")

			else:
				value = None

			result[name] = value

		return part_obj, result

	@decoratorslib.undoable
	def build_guide_part(self):
		"""

		:return:
		"""

		part_obj, options = self.get_options_data()
		if not part_obj:
			return

		partslib.build_guide(part_obj.part_type, **options)
		self.list_parts()

	@decoratorslib.undoable
	def update_options(self):
		"""

		:return:
		"""

		part_obj, options = self.get_options_data()
		if not part_obj or not options:
			return

		part_obj, options = self.get_options_data()
		current_options = {k: v.get("value") for k, v in part_obj.options.items()}

		# find changed options
		changed_options = {}
		for name in options.keys():
			if options.get(name) != current_options.get(name):
				if name == "side":
					part_obj = partslib.update_options(part_obj, side=options.get(name))

				elif name == "name":
					part_obj = partslib.update_options(part_obj, name=options.get(name))

				else:
					changed_options[name] = options.get(name)

		if changed_options:
			part_obj = partslib.update_options(part_obj, **changed_options)

		cmds.select(part_obj.guide_group)

		self.list_parts()

	def set_field_selection(self, line_edit, single_selection=True, rig_part=False):
		"""

		:param line_edit:
		:param single_selection:
		:param rig_part:
		:return:
		"""
		plc_suffix = prefs.get_suffix("jointPlacer")
		jnt_suffix = prefs.get_suffix("joint")

		sel = cmds.ls(sl=1)
		sel = [s.replace(plc_suffix, jnt_suffix)
		       if s.endswith(plc_suffix) and cmds.objExists(s.replace(plc_suffix, jnt_suffix)) else s for s in sel]

		value = ""
		if sel and single_selection:
			value = sel[0]

		elif sel:
			value = sel

		value = partslib.utils.find_guide_group_from_selection(value) if rig_part else value
		line_edit.setText(str(value))

	def save_guides(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		guide.save_from_build_options()

	def load_guides(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		guide.load_from_build_options()
		self.list_parts()

	def launch_guide_loader(self, *args, **kwargs):
		"""

		:return:
		"""
		self.guide_wdg = guideloader.GuideLoader(self)
		self.guide_wdg.show()

	def load_models(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		model.load_from_build_options()

	def launch_model_loader(self, *args, **kwargs):
		"""

		:return:
		"""
		self.model_wdg = modelloader.ModelLoader(self)
		self.model_wdg.show()

	def save_guide_options(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		result = cmds.promptDialog(
			title='Save Guides File.',
			message='Guide Description Token:',
			button=['Save Scene', 'Cancel'],
			defaultButton='Save Scene',
			cancelButton='Cancel',
			dismissString='Cancel')

		if result == 'Save Scene':
			description = cmds.promptDialog(query=True, text=True)
			guide.save_scene(description=description)
			env.asset.set_guides(description=description)

	def clean_model_options(self, *args, **kwargs):
		"""

		:return:
		"""
		clean_model_wdg = cleanmodel.CleanModel()
		clean_model_wdg.show()

	def save_model_options(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		result = cmds.promptDialog(
			title='Save Model File.',
			message='Model Description Token:',
			button=['Save Scene', 'Cancel'],
			defaultButton='Save Scene',
			cancelButton='Cancel',
			dismissString='Cancel')

		if result == 'Save Scene':
			description = cmds.promptDialog(query=True, text=True)
			model.save_scene(description=description)

	def save_template(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		ui = newtemplate.NewTemplate()
		ui.exec_()

	@decoratorslib.undoable
	def modify_parts(self, action, side=None):
		"""

		:param action:
		:param side:
		:param name:
		:param mirror_mode:
		:param set_shapes:
		:param set_colors:
		:return:
		"""
		if not self.filter_list.list.selectedItems():
			log.warning("No parts selected in list.")
			return

		guide_grps = [i.text() for i in self.filter_list.list.selectedItems()]
		for guide_grp in guide_grps:
			if action == "mirror":
				partslib.mirror_guide(guide_grp)

			elif action == "duplicate":
				partslib.duplicate_guide(guide_grp)

			elif action == "rebuild":
				partslib.rebuild_guide(guide_grp)

			elif action == "delete":
				partslib.delete_guide(guide_grp)

		self.list_parts()

	def mirror_part(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		self.modify_parts("mirror")

	def mirror_part_options(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""
		if not self.filter_list.list.selectedItems():
			log.warning("No parts selected in list.")
			return

		mirror_option_wdg = mirrorpart.MirrorPart(self)
		mirror_option_wdg.header.label.setText("Mirror Part ")
		mirror_option_wdg.exec_()

		if mirror_option_wdg.do_it:
			guide_grps = [i.text() for i in self.filter_list.list.selectedItems()]

			for guide_grp in guide_grps:
				partslib.mirror_guide(guide_grp,
				                      mirror_mode=mirror_option_wdg.mirror_mode,
				                      set_shapes=mirror_option_wdg.set_shapes,
				                      set_colors=mirror_option_wdg.set_colors)
			else:
				self.list_parts()
				return

		self.list_parts()

	def create_new_part(self):
		"""

		:return:
		"""
		newpart.run(self)

	def duplicate_options(self):
		"""

		:return:
		"""
		if not self.filter_list.list.selectedItems():
			log.warning("No parts selected in list.")
			return

		guide_grps = [i.text() for i in self.filter_list.list.selectedItems()]
		for guide_grp in guide_grps:
			options = eval(cmds.getAttr(guide_grp + ".options"))

			duplicate_option_wdg = duplicatepart.DuplicateGuide(self)
			duplicate_option_wdg.header.label.setText("Duplicate Part: " + guide_grp)
			duplicate_option_wdg.side_line.setText(options.get("side").get("value"))
			duplicate_option_wdg.name_line.setText(options.get("name").get("value"))
			duplicate_option_wdg.exec_()

			if duplicate_option_wdg.do_it:
				partslib.duplicate_guide(guide_grp,
				                         side=str(duplicate_option_wdg.side),
				                         name=str(duplicate_option_wdg.name))
			else:
				self.list_parts()
				return

		self.list_parts()

	@decoratorslib.undoable
	@decoratorslib.preserve_selection
	def toggle(self, attribute, selected=True, unselected=False, value=None):
		"""

		:param attribute: "visibility" "jointsVisibility", "controlsVisibility", "jointDisplayLocalAxis", "controlDisplayLocalAxis"
		:param selected:
		:param unselected:
		:return:
		"""
		all_items = [self.filter_list.list.item(i).text() for i in range(self.filter_list.list.count())]
		selected_items = [i.text() for i in self.filter_list.list.selectedItems()]
		unselected_items = [i for i in all_items if i not in selected_items]
		items = selected_items if selected else unselected_items if unselected else all_items

		if not items:
			return

		if value is None:
			value = cmds.getAttr("{}.{}".format(items[0], attribute))
			value = 0 if value else 1

		for item in items:
			cmds.setAttr("{}.{}".format(item, attribute), value)

		self.color_items()
		cmds.select(items)

	@decoratorslib.undoable
	def quick_build(self):
		"""

		:return:
		"""
		skeleton.build()
		partslib.build_rigs()
		rig.connect_parent_drivers()
		rig.connect_attribute_drivers()
		spaceslib.build_all_spaces()

	@decoratorslib.undoable
	def quick_finish_build(self):
		"""

		:return:
		"""
		rig.lock_control_group_hierarchy()
		rig.parent_constraint_noxform()


def run():
	"""

	:return: Qt widget object
	"""
	ui = GuideBuild()
	ui.show()
	return ui
