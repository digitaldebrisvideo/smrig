try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui

from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.gui.widget import partpicker


class PartsFilterListWidget(QtWidgets.QFrame):

	def __init__(self, parent=maya_main_window, guide_build_widget=None):
		super(PartsFilterListWidget, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)
		self.setFrameStyle(QtWidgets.QFrame.StyledPanel)

		layout = QtWidgets.QVBoxLayout(self)

		frame = QtWidgets.QFrame(self)
		frame.setStyleSheet("QFrame{background-color: rgb(55,55,55)}")
		f_layout = QtWidgets.QHBoxLayout(frame)
		label = QtWidgets.QLabel("Filter:\t")
		btn = QtWidgets.QPushButton(self)
		btn.released.connect(self.clear)
		btn.setIcon(QtGui.QIcon(get_icon_path("x.png")))
		btn.setFlat(True)

		self.field = QtWidgets.QLineEdit(self)

		self.list = PartListWidget(self, guide_build_widget)
		self.list.setFrameStyle(QtWidgets.QFrame.NoFrame)

		f_layout.addWidget(label)
		f_layout.addWidget(self.field)
		f_layout.addWidget(btn)
		f_layout.setContentsMargins(4, 2, 2, 2)
		f_layout.setSpacing(2)

		layout.addWidget(frame)
		layout.addWidget(self.list)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

	@property
	def items(self):
		"""

		:return:
		"""
		items = []
		for idx in range(self.list.count()):
			items.append(self.list.item(idx))
		return items

	def clear(self):
		"""

		:return:
		"""
		self.field.setText("")


class PartListWidget(QtWidgets.QListWidget):

	def __init__(self, parent=maya_main_window, guide_build_widget=None):
		super(PartListWidget, self).__init__(parent)

		self.part_picker = None
		self.guide_build_widget = guide_build_widget
		self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

	def keyPressEvent(self, event):
		QtWidgets.QListWidget.keyPressEvent(self, event)

	def event(self, event):
		if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
			self.part_picker = partpicker.run(self.parentWidget(), self.guide_build_widget)

			win_point = self.part_picker.parentWidget().window().frameGeometry().bottomLeft()
			wdg_point = QtCore.QPoint(self.part_picker.parentWidget().frameGeometry().width() * -0.5,
			                          self.part_picker.parentWidget().frameGeometry().height() * 0.8)
			self.part_picker.move(win_point - wdg_point)

		return QtWidgets.QListWidget.event(self, event)
