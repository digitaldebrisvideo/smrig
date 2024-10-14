try:
    from PySide2 import QtWidgets
except:
    from PySide6 import QtWidgets, QtGui

from smrig.gui.mayawin import maya_main_window, get_icon_path


class SearchTree(QtWidgets.QFrame):

	def __init__(self, parent=maya_main_window):
		super(SearchTree, self).__init__(parent)

		# Parent widget under Maya mainbuild window
		self.setParent(parent)
		self.setFrameStyle(QtWidgets.QFrame.StyledPanel)

		layout = QtWidgets.QVBoxLayout(self)

		frame = QtWidgets.QFrame(self)
		frame.setStyleSheet("QFrame{background-color: rgb(55,55,55)}")
		f_layout = QtWidgets.QHBoxLayout(frame)
		label = QtWidgets.QLabel("Filter:\t")
		btn = QtWidgets.QPushButton(self)
		btn.setIcon(QtGui.QIcon(get_icon_path("x.png")))
		btn.setFlat(True)

		self.tree = QtWidgets.QTreeWidget(self)
		self.tree.setFrameStyle(QtWidgets.QFrame.NoFrame)

		self.field = QtWidgets.QLineEdit(self)
		btn.released.connect(self.clear)

		f_layout.addWidget(label)
		f_layout.addWidget(self.field)
		f_layout.addWidget(btn)
		f_layout.setContentsMargins(4, 2, 2, 2)
		f_layout.setSpacing(2)

		layout.addWidget(frame)
		layout.addWidget(self.tree)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

	def clear(self):
		"""

		:return:
		"""
		self.field.setText("")
