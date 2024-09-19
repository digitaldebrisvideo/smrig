from PySide2 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path, create_ui_script_jobs, kill_ui_script_jobs
from smrig.gui.tool import modelsettings
from smrig.gui.tool import rigbuild
from smrig.gui.widget import charenv
from smrig.gui.widget import header

global char_ui
char_ui = None


class CharMain(QtWidgets.QDialog):

	def __init__(self, parent=maya_main_window):
		super(CharMain, self).__init__(parent)

		# Parent widget under Maya CharMain window
		self.setParent(parent)
		self.setWindowTitle("Character Rigging Suites")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo3.png")))

		h_layout = QtWidgets.QVBoxLayout(self)
		h_layout.setContentsMargins(0, 0, 0, 0)

		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)

		self.m_header = header.Header(self, large=True, logo=True, title="SMRIG Character Rigging Suite")

		# asset Env ------------------------------------------
		self.e_frame = QtWidgets.QFrame(self)
		self.e_frame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
		self.env_widget = charenv.CharEnv(self)
		self.env_widget.variant_cmb.currentIndexChanged.connect(self.save_ui_state)

		e_layout = QtWidgets.QVBoxLayout(self)
		e_layout.addWidget(self.env_widget)
		self.e_frame.setLayout(e_layout)
		# self.e_frame.hide()

		# tabs ------------------------------------------------
		self.tabs = QtWidgets.QTabWidget(self)

		# #settings tab -----------------------------------------
		self.setting_wdg = modelsettings.ModelSettings(self)
		self.tabs.addTab(self.setting_wdg, "START HERE")

		# # mh build tab -----------------------------------------
		self.rb_wdg = rigbuild.RigBuild(self)
		self.tabs.addTab(self.rb_wdg, "Rig Build")

		# # guide build tab -----------------------------------------
		# self.sm_wdg = rigbuild.RigBuild(self)
		# self.tabs.addTab(self.sm_wdg, "SM Rig Build")
		#
		# # # blender build tab -----------------------------------------
		# self.bl_wdg = rigbuild.RigBuild(self)
		# self.tabs.addTab(self.bl_wdg, "Blender")

		# # tool tab -----------------------------------------
		# self.dataload_wdg = toolbox.ToolBox(self)
		# self.tabs.addTab(self.dataload_wdg, "Tools")

		# set widgets ----------------------------------------------------------
		h_layout.addWidget(self.m_header)
		h_layout.addLayout(layout)
		layout.addWidget(self.e_frame)
		layout.addWidget(self.tabs)

		h_layout.setStretch(0, 0)
		h_layout.setStretch(1, 1)
		layout.setStretch(0, 0)
		layout.setStretch(1, 1)

		self.setLayout(h_layout)

		self.settings = QtCore.QSettings("SMRIG", "Rig Builder")
		self.restoreGeometry(self.settings.value("geometry"))

		try:
			self.tabs.setCurrentIndex(self.settings.value("saved_tab", 0) if self.settings.value("saved_tab", 0) else 0)
		except:
			pass

		saved_env = self.settings.value("saved_env")
		if saved_env:
			self.env_widget.job_cmb.setCurrentText(saved_env[0])
			self.env_widget.asset_cmb.setCurrentText(saved_env[1])
			self.env_widget.variant_cmb.setCurrentText(saved_env[2])

		self.env_widget.variant_cmb.currentIndexChanged.connect(self.reload_ui)
		self.env_widget.post_function = self.reload_ui

		self.setMinimumWidth(650)
		self.setMinimumHeight(650)

		self.reload_ui()

		self.script_jobs = create_ui_script_jobs(self.script_job_functions)
		self.script_jobs.extend(create_ui_script_jobs(self.script_job_functions_no_delete, delete=False))

	def reload_ui(self):
		"""
		Reload all pertinent ui dataexporter when asset env is changed
		:return:
		"""
		# self.setting_wdg.reload_ui()
		self.rb_wdg.reload_ui()

	# self.sm_wdg.reload_ui()
	# self.bl_wdg.reload_ui()
	# self.dataload_wdg.reload_ui()

	def closeEvent(self, event, *args, **kwargs):
		"""

		:param event:
		:return:
		"""
		self.save_ui_state()

		if self.script_jobs:
			kill_ui_script_jobs(self.script_jobs)

		QtWidgets.QDialog.closeEvent(self, event)

	def reject(self, *args, **kwargs):
		"""

		:return:
		"""
		self.save_ui_state()

		if self.script_jobs:
			kill_ui_script_jobs(self.script_jobs)

		QtWidgets.QDialog.reject(self)

	def script_job_functions(self):
		"""

		:return:
		"""

	def script_job_functions_no_delete(self):
		"""

		:return:
		"""

		self.rb_wdg.build.manager.reload_manager()
		self.rb_wdg.update_status()
		self.rb_wdg.update_colors()

	def save_ui_state(self):
		"""
		:return:
		"""
		self.settings.setValue("geometry", self.saveGeometry())
		self.settings.setValue("saved_env", [env.get_job(), env.asset.get_asset(), env.asset.get_variant()])
		self.settings.setValue("saved_tab", self.tabs.currentIndex())


def run(reset=False):
	"""

	:return: Qt widget object
	"""
	global char_ui

	if char_ui and not reset:
		char_ui.show()

	else:
		char_ui = CharMain()
		char_ui.show()

	return char_ui

# def run():
#     """
#
#     :return: Qt widget object
#     """
#     global char_ui
#     char_ui = charmain.CharMain()
#     char_ui.show()
#     return char_ui
