from PySide2 import QtCore, QtWidgets, QtGui

from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.lib import pathlib


class Header(QtWidgets.QFrame):
	_link = ""

	def __init__(self,
	             parent=maya_main_window,
	             title="Path Settings",
	             large=False,
	             bold=True,
	             italic=False,
	             light_grey=True,
	             logo=False,
	             info_button=True,
	             info_icon="info_24x24.png"):

		super(Header, self).__init__(parent)

		font_size = 20 if large else 12
		logo = logo if large else False
		height = 40 if large else 28

		# Parent widget under Maya main window
		self.setParent(parent)

		layout = QtWidgets.QHBoxLayout(self)
		layout.setSpacing(font_size)

		self.label = QtWidgets.QLabel(title)
		font = QtGui.QFont()
		font.setPointSize(font_size)
		font.setItalic(italic)
		font.setBold(bold)
		self.label.setFont(font)

		self.setMinimumSize(QtCore.QSize(0, height))
		self.setMaximumSize(QtCore.QSize(16777215, height))

		if light_grey:
			self.setStyleSheet("QWidget{background-color: rgb(50, 50, 50)}")
		else:
			self.setStyleSheet("QWidget{background-color: rgb(0, 0, 0)}")

		if logo:
			self.icon = QtWidgets.QLabel()
			self.pix = QtGui.QPixmap(get_icon_path("logo.png"))
			self.icon.setPixmap(self.pix)

			self.icon.setScaledContents(True)
			self.icon.setMinimumHeight(height)
			self.icon.setMaximumHeight(height)
			self.icon.setMinimumWidth(height)
			self.icon.setMaximumWidth(height)

			layout.setContentsMargins(0, 0, 6, 0)
			layout.addWidget(self.icon)
			layout.addWidget(self.label)

			layout.setStretch(0, 0)
			layout.setStretch(1, 1)
			layout.setStretch(2, 0)

		else:
			layout.setContentsMargins(6, 0, 6, 0)
			layout.addWidget(self.label)
			layout.setStretch(0, 1)
			layout.setStretch(1, 0)

		if info_button:
			self.help_button = QtWidgets.QPushButton()
			self.help_button.setIcon(QtGui.QIcon(get_icon_path(info_icon)))
			self.help_button.setFlat(True)
			layout.addWidget(self.help_button)

			self.help_button.released.connect(self.open_link)

	@property
	def link(self):
		"""

		:return:
		"""
		return self._link

	def set_link(self, path):
		"""

		:param path:
		:return:
		"""
		self._link = path

	def open_link(self):
		"""

		:return:
		"""
		if self.link:
			pathlib.open_in_text_editor(self._link)
