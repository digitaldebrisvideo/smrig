import logging
import sys
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui

from smrig import partslib
from smrig.gui.mayawin import maya_main_window
from smrig.userprefs import USE_FACILITY_PIPELINE

log = logging.getLogger("smrig.partpicker")


class PartPicker(QtWidgets.QDialog):
	part = None
	template = None

	def __init__(self, parent=maya_main_window, guide_build_wdg=None):
		super(PartPicker, self).__init__(parent)
		self.setWindowTitle("sm Rig | Add Part")

		"""
		if not USE_FACILITY_PIPELINE:
			self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
			self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		"""

		if not USE_FACILITY_PIPELINE:
			self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
			self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

		# Parent widget under Maya main window
		# self.setParent(parent)
		self.guide_build_widget = guide_build_wdg

		layout = QtWidgets.QHBoxLayout(self)
		layout.setContentsMargins(10, 10, 10, 10)

		widget = QtWidgets.QFrame(self)
		w_layout = QtWidgets.QHBoxLayout(self)
		w_layout.setContentsMargins(6, 0, 0, 0)
		w_layout.setSpacing(2)

		widget.setLayout(w_layout)
		layout.addWidget(widget)
		widget.setStyleSheet("QFrame{background-color: rgb(85,85,85)} QMenuBar{background-color: rgb(85,85,85)}")
		label = QtWidgets.QLabel("Add Part or Template:  ")

		self.line = PartsLine(self)
		self.line.setMinimumWidth(200)
		self.menu_bar = QtWidgets.QMenuBar(self)

		self.menu = QtWidgets.QMenu(">>")
		self.menu_bar.addMenu(self.menu)

		w_layout.addWidget(label)
		w_layout.addWidget(self.line)
		w_layout.addWidget(self.menu_bar)

		effect = QtWidgets.QGraphicsDropShadowEffect(widget)
		effect.setColor(QtGui.QColor("black"))
		effect.setBlurRadius(5)
		effect.setOffset(2, 2)
		widget.setGraphicsEffect(effect)

		self.reload_lib()

		if str(sys.version).startswith("2"):
			self.setModal(True)

	def reload_lib(self):

		partslib.manager.reload_lib()
		words = ["{}.template".format(t) for t in partslib.manager.templates] + partslib.manager.parts
		self.line.completer.model().setStringList(words)
		self.line.words = words

		part_cat_menus = {}
		template_cat_menus = {}

		self.menu.clear()
		self.line.setText("")

		tmp_action = QtWidgets.QWidgetAction(self.menu)
		label = QtWidgets.QLabel("")
		label.setMaximumHeight(0)
		tmp_action.setDefaultWidget(label)
		self.menu.addAction(tmp_action)
		self.menu.addSection("Templates")

		for category in partslib.manager.template_categories:
			menu = QtWidgets.QMenu(category)
			template_cat_menus[category] = menu
			self.menu.addMenu(menu)

		self.menu.addSection("Parts")
		for category in partslib.manager.part_categories:
			menu = QtWidgets.QMenu(category)
			part_cat_menus[category] = menu
			self.menu.addMenu(menu)

		for part, data in partslib.manager.data.items():
			if part in partslib.manager.parts + partslib.manager.templates:
				item = QtWidgets.QAction(self.menu)
				item.setText(part)
				item.triggered.connect(partial(self.set_values, part, data.get("type")))

				if data.get("type") == "part":
					part_cat_menus.get(data.get("category")).addAction(item)
				else:
					template_cat_menus.get(data.get("category")).addAction(item)

	def set_values(self, part, ptype):
		"""

		:param part:
		:param ptype:
		:return:
		"""
		self.part = part
		self.template = False if ptype == "part" else True
		self.set_guides_wdg()

	def set_guides_wdg(self):
		"""

		:return:
		"""
		try:
			self.deleteLater()
		except:
			pass

		if self.guide_build_widget:
			if self.part:
				self.guide_build_widget.populate_new_part(self.part, self.template)
			else:
				self.guide_build_widget.clear_tree()


class PartsLine(QtWidgets.QLineEdit):

	def __init__(self, parent=None, words=[]):
		super(PartsLine, self).__init__(parent)

		self.parent_widget = parent
		self.setPlaceholderText("Start typing...")

		self.completer = QtWidgets.QCompleter(words, self)
		self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
		self.completer.setWrapAround(False)
		self.setCompleter(self.completer)
		self.words = words

		self.setFocus()

	def next_completion(self):

		index = self.completer.currentIndex()
		self.completer.popup().setCurrentIndex(index)

		start = self.completer.currentRow()
		if not self.completer.setCurrentRow(start + 1):
			self.completer.setCurrentRow(0)

	def keyPressEvent(self, event):
		QtWidgets.QLineEdit.keyPressEvent(self, event)

	def event(self, event):
		if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Enter:
			self.parent_widget.part = self.text().split(".")[0]
			self.parent_widget.template = True if ".template" in self.text() else False
			self.parent_widget.set_guides_wdg()

			if self.text() in self.words:
				self.parent_widget.deleteLater()
			else:
				log.warning("{} not a valid part or template.".format(self.text()))

		elif event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Return:
			self.parent_widget.part = self.text().split(".")[0]
			self.parent_widget.template = True if ".template" in self.text() else False
			self.parent_widget.set_guides_wdg()

			if self.text() in self.words:
				self.parent_widget.deleteLater()
			else:
				log.warning("{} not a valid part or template.".format(self.text()))

		elif event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Escape:
			self.parent_widget.part = None
			self.parent_widget.template = False
			self.parent_widget.set_guides_wdg()
			self.parent_widget.deleteLater()

		elif event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
			self.next_completion()
			self.parent_widget.part = self.text().split(".")[0]
			self.parent_widget.template = True if ".template" in self.text() else False
			self.parent_widget.set_guides_wdg()
			return True

		return QtWidgets.QLineEdit.event(self, event)


def run(parent=maya_main_window, guide_build_wdg=None):
	"""

	:param parent:
	:param guide_build_wdg:
	:return:
	"""
	picker_ui = PartPicker(parent=parent, guide_build_wdg=guide_build_wdg)
	picker_ui.show()
	return picker_ui
