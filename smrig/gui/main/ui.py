from PySide2 import QtCore, QtWidgets, QtGui

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path, create_ui_script_jobs, kill_ui_script_jobs
from smrig.gui.tool import endtools
from smrig.gui.tool import modelsettings
from smrig.gui.tool import rigbuild
from smrig.gui.widget import assetenv
from smrig.gui.widget import header

global smrig_ui
smrig_ui = None


class Main(QtWidgets.QDialog):

	def __init__(self, parent=maya_main_window):
		super(Main, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)
		self.setWindowTitle("SMRIG")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		h_layout = QtWidgets.QVBoxLayout(self)
		h_layout.setContentsMargins(0, 0, 0, 0)

		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(10, 0, 10, 10)

		self.m_header = header.Header(self, large=True, logo=True, title="SMRig")

		# asset Env ------------------------------------------
		self.e_frame = QtWidgets.QFrame(self)
		self.e_frame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
		self.env_widget = assetenv.AssetEnv(self)
		self.env_widget.variant_cmb.currentIndexChanged.connect(self.save_ui_state)

		e_layout = QtWidgets.QVBoxLayout(self)
		e_layout.addWidget(self.env_widget)
		self.e_frame.setLayout(e_layout)

		# tabs ------------------------------------------------
		self.tabs = QtWidgets.QTabWidget(self)

		# guide guides tab -----------------------------------------
		# self.guides_wdg = guidebuild.GuideBuild(self)
		# self.tabs.addTab(self.guides_wdg, "Guides")

		# START HERE tab -----------------------------------------

		self.settings_wdg = modelsettings.ModelSettings(self)
		self.tabs.addTab(self.settings_wdg, "START HERE")

		#  build tab -----------------------------------------
		self.build_wdg = rigbuild.RigBuild(self)
		self.tabs.addTab(self.build_wdg, "Build")

		# end here build tab -----------------------------------------
		self.endtools_wdg = endtools.EndTools(self)
		self.tabs.addTab(self.endtools_wdg, "END HERE")

		# guide data export tab -----------------------------------------
		# self.dataexport_wdg = datasave.DataSave(self)
		# self.tabs.addTab(self.dataexport_wdg, "Export Data")

		# data import tab -----------------------------------------
		# self.dataload_wdg = dataimporter.DataImporter(self)
		# self.tabs.addTab(self.dataload_wdg, "Load Data")

		# guide build tab -----------------------------------------
		# self.dataload_wdg = toolbox.ToolBox(self)
		# self.tabs.addTab(self.dataload_wdg, "Toolbox")

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

		self.settings = QtCore.QSettings("SM_Studio", "smrig")
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

		self.setMinimumWidth(500)
		self.setMinimumHeight(650)

		self.reload_ui()

		self.script_jobs = create_ui_script_jobs(self.script_job_functions)
		self.script_jobs.extend(create_ui_script_jobs(self.script_job_functions_no_delete, delete=False))

	def reload_ui(self):
		"""
		Reload all pertinent ui dataexporter when asset env is changed
		:return:
		"""

		self.build_wdg.reload_ui()

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
		# self.guides_wdg.list_parts()
		self.build_wdg.build.manager.reload_manager()
		self.build_wdg.update_status()
		self.build_wdg.update_colors()

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
	global smrig_ui

	if smrig_ui and not reset:
		smrig_ui.show()

	else:
		smrig_ui = Main()
		smrig_ui.show()

	return smrig_ui
