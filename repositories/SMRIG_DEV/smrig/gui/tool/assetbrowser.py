
try:
	from PySide2 import QtWidgets, QtCore, QtGui
except:
	from PySide6 import QtWidgets, QtCore, QtGui

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import os
from smrig import env
from smrig.lib import pathlib
import shutil
from smrig.lib import pathlib, attributeslib
from smrig.lib.deformlib import blendshape
from smrig import dataio, dataioo

try:
	from shiboken2 import wrapInstance
except ImportError:
	from shiboken6 import wrapInstance
try:
	maya_main_window = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
except:
	maya_main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

# Define the default directory for asset handling
ICON_SIZE = 400  # Increased icon size for larger thumbnails


# Function to get the Maya Main Window
def get_maya_main_window():
	main_window_ptr = omui.MQtUtil.mainWindow()
	return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


# Main Asset Manager UI Class
class AssetManagerUI(QtWidgets.QMainWindow):
	def __init__(self, parent=get_maya_main_window()):
		super(AssetManagerUI, self).__init__(parent)
		self.setWindowTitle("Asset Manager")
		self.setMinimumSize(900, 600)  # Set initial size

		DEFAULT_IMPORT_DIR = self.get_library_directory()

		# Main Splitter Layout to allow adjustable resizing
		self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		self.setCentralWidget(self.main_splitter)

		# Left Side - Asset List and Controls
		self.left_widget = QtWidgets.QWidget()
		self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)
		self.main_splitter.addWidget(self.left_widget)

		# Directory Layout
		self.dir_layout = QtWidgets.QHBoxLayout()
		self.dir_label = QtWidgets.QLabel("Asset Directory:")
		self.dir_field = QtWidgets.QLineEdit(DEFAULT_IMPORT_DIR)
		self.dir_browse_btn = QtWidgets.QPushButton("Browse")
		self.dir_layout.addWidget(self.dir_label)
		self.dir_layout.addWidget(self.dir_field)
		self.dir_layout.addWidget(self.dir_browse_btn)

		# Asset List
		self.ui_list_widget = QtWidgets.QListWidget()

		# Buttons Layout
		self.button_layout = QtWidgets.QHBoxLayout()

		# Buttons
		self.ui_open_btn = QtWidgets.QPushButton("Open")
		self.ui_import_btn = QtWidgets.QPushButton("Import")
		self.ui_export_btn = QtWidgets.QPushButton("Export")
		self.ui_delete_btn = QtWidgets.QPushButton("Delete")


		# Add buttons to layout
		self.button_layout.addWidget(self.ui_open_btn)
		self.button_layout.addWidget(self.ui_import_btn)
		self.button_layout.addWidget(self.ui_export_btn)
		self.button_layout.addWidget(self.ui_delete_btn)

		# Add widgets to the left layout
		self.left_layout.addLayout(self.dir_layout)
		self.left_layout.addWidget(self.ui_list_widget)
		self.left_layout.addLayout(self.button_layout)

		# Right Side - Thumbnail Display
		self.right_widget = QtWidgets.QWidget()
		self.right_layout = QtWidgets.QVBoxLayout(self.right_widget)
		self.main_splitter.addWidget(self.right_widget)

		# Centered Thumbnail Display Area
		self.thumbnail_container = QtWidgets.QWidget()
		self.thumbnail_layout = QtWidgets.QVBoxLayout(self.thumbnail_container)
		self.thumbnail_layout.setAlignment(QtCore.Qt.AlignCenter)
		self.ui_info_widget = QtWidgets.QListWidget()
		self.ui_info_widget.setIconSize(QtCore.QSize(ICON_SIZE, ICON_SIZE))
		self.thumbnail_layout.addWidget(self.ui_info_widget)

		# Re-generate Thumbnail Button
		self.regenerate_btn = QtWidgets.QPushButton("Re-generate Thumbnail")
		self.regenerate_btn.clicked.connect(self.regenerate_thumbnail)
		self.thumbnail_layout.addWidget(self.regenerate_btn)

		# Add Thumbnail Display Area to the Right Layout
		self.right_layout.addWidget(self.thumbnail_container)

		# Connect signals and slots
		self.dir_browse_btn.clicked.connect(self.browse_directory)
		self.dir_field.textChanged.connect(self.update_lib_lib_asset_list)
		self.ui_list_widget.itemClicked.connect(self.display_detail)
		self.ui_open_btn.clicked.connect(self.open_lib_asset)
		self.ui_import_btn.clicked.connect(self.import_lib_asset)
		# self.ui_export_btn.clicked.connect(self.export_shapelib_asset)
		self.ui_export_btn.clicked.connect(self.export_lib_asset)
		self.ui_delete_btn.clicked.connect(self.delete_lib_asset)

		# Initial Population of Asset List
		self.update_lib_lib_asset_list()

	def get_library_directory(self):
		"""
		:return:
		"""
		# asset = env.asset.get_asset()
		# if not asset:
		# 	return ("Asset not set")
		#
		# lib_folder = ""
		# model_filepath = env.asset.get_models()[0].get("file_path")
		# if model_filepath:
		# 	folder = model_filepath.replace(model_filepath.split("/")[-1], "")
		# 	lib_folder = pathlib.normpath(os.path.join(folder, "Rig", "Library"))
		# else:
		# 	warning("Model not set.  Using Current Project")
		lib_folder = pathlib.normpath(os.path.join(cmds.workspace(expandName="scenes"), "Rig", "Library"))
		if not os.path.exists(lib_folder):
			pathlib.make_dirs(lib_folder)
		DEFAULT_IMPORT_DIR = lib_folder
		return DEFAULT_IMPORT_DIR

	def browse_directory(self):
		# Allow the user to browse and select a new directory
		directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Directory", self.dir_field.text())
		if directory:
			self.dir_field.setText(directory)

	def update_lib_lib_asset_list(self):
		# Populate the asset list with .mb files in the specified directory
		directory = self.dir_field.text()
		self.ui_list_widget.clear()
		if os.path.exists(directory):
			mb_files = [f for f in os.listdir(directory) if f.endswith('.mb')]
			for mb_file in mb_files:
				item = QtWidgets.QListWidgetItem(mb_file)
				item.setData(QtCore.Qt.UserRole, os.path.join(directory, mb_file))

				# Load and set the thumbnail if exists
				thumbnail_path = os.path.join(directory, f"{os.path.splitext(mb_file)[0]}.png")
				if os.path.exists(thumbnail_path):
					item.setIcon(QtGui.QIcon(thumbnail_path))

				self.ui_list_widget.addItem(item)

	def display_detail(self):
		# Display detailed information and thumbnail of the selected item
		self.ui_info_widget.clear()
		item = self.ui_list_widget.currentItem()
		if item:
			file_path = item.data(QtCore.Qt.UserRole)
			thumbnail_path = os.path.join(self.dir_field.text(),
			                              f"{os.path.splitext(os.path.basename(file_path))[0]}.png")

			if os.path.exists(thumbnail_path):
				thumbnail_item = QtWidgets.QListWidgetItem()
				thumbnail_item.setIcon(QtGui.QIcon(thumbnail_path))
				self.ui_info_widget.addItem(thumbnail_item)

			self.ui_info_widget.addItem(QtWidgets.QListWidgetItem(f"Name: {os.path.basename(file_path)}"))
			self.ui_info_widget.addItem(QtWidgets.QListWidgetItem(f"Size: {os.path.getsize(file_path)} bytes"))
			self.ui_info_widget.addItem(QtWidgets.QListWidgetItem(
				f"Last Edit: {QtCore.QDateTime.fromSecsSinceEpoch(int(os.path.getmtime(file_path))).toString()}"))

	def open_lib_asset(self):
		# Open the selected .mb file
		item = self.ui_list_widget.currentItem()
		if item:
			file_path = item.data(QtCore.Qt.UserRole)
			cmds.file(file_path, open=True, force=True)

	def import_lib_asset(self):
		# Import the selected .mb file into the current scene
		item = self.ui_list_widget.currentItem()
		if item:
			file_path = item.data(QtCore.Qt.UserRole)
			cmds.file(file_path, i=True)

	def export_lib_asset(self):
		"""

		:param type:  for now the choices are blendshape or node.  if we use presets in the future, that will be added as an option"
		:return:
		"""
		# Export the selected node(s) to a .mb file in the current directory with a snapshot
		selected_nodes = cmds.ls(selection=True)
		# selected_channel_attrs = attributeslib.get_selected_attributes(node_path=True)
		# selected_editor_targets: object = blendshape.get_selected_targets()

		if selected_channel_attrs or selected_editor_targets:
			self.export_shapelib_asset()
		else:
			if not selected_nodes:
				QtWidgets.QMessageBox.warning(self, "No Selection", "Please select an object to export.")
				return
		for selected in selected_nodes:
			export_name, _ = QtWidgets.QInputDialog.getText(self, "Export Asset",
			                                                "Enter the name for the exported asset:",
			                                                QtWidgets.QLineEdit.Normal,
			                                                selected)

			if not export_name:
				return
			export_path = pathlib.normpath(os.path.join(self.dir_field.text(), f"{export_name}.mb"))
			thumbnail_path = pathlib.normpath(os.path.join(self.dir_field.text(), f"{export_name}.png"))

			# Capture viewport snapshot
			self.capture_viewport_snapshot(thumbnail_path)
			cmds.file(export_path, exportSelected=True, type="mayaBinary", force=True)
			mel_cmd = ('file -typ "mayaBinary" -es  \"' + export_path + '"')
			cmds.thumbnailCaptureComponent(capture=1, fdp=0, fdc=mel_cmd)
			cmds.thumbnailCaptureComponent(save=export_path)
			cmds.thumbnailCaptureComponent(closeCurrentSession=True)

			# Set the thumbnail for the exported item
			item = QtWidgets.QListWidgetItem(f"{export_name}.mb")
			item.setData(QtCore.Qt.UserRole, export_path)
			item.setIcon(QtGui.QIcon(thumbnail_path))
			self.ui_list_widget.addItem(item)

			print("Export Complete", f"Asset exported to {export_path}")

			self.update_lib_lib_asset_list()


	def export_shapelib_asset(self):
		"""
		export Blend shapes to. Shape library.
		command.
		set all to zero
		isolates and takes a snapshot of geo
		exports files to blenshape_library
		Export the selected node(s) to a .mb file in the current directory with a snapshot

		:return:
		"""

		# get selected attributes from channel box and script editor and then get all selected nodes and filer out default geo
		selected_channel_attrs = attributeslib.get_selected_attributes(node_path=True)
		selected_editor_targets: object = blendshape.get_selected_targets()
		selected_nodes = cmds.ls(sl=1, type="transform")
		exclude = ["Head_hi", "Eyes_hi", "Teeth_hi", "Body_hi", "Caruncles_hi"]
		export_nodes = [x for x in exclude if not x in exclude]
		export_attrs = selected_channel_attrs + selected_editor_targets
		if not export_attrs and not selected_nodes:
			QtWidgets.QMessageBox.warning(self, "Nothing selected",
			                              "3 ways to export selection 1. select geometry nodes 2.  select bs attributes in maya's shapeEditor 3.  select attributes on bs node in the channel box")
			return
		# set  controls to zero,  loop through selected shape attrs, set value of target to 1 and dupllicate
		if export_attrs:
			ctls = dataio.utils.get_controls()
			pre_ctl_data = dataio.types.attribute_values.get_data(ctls)
			cmds.xform(ctls, a=1, t=[0, 0, 0])
			cmds.xform(ctls, a=1, ro=[0, 0, 0])
		for selected in export_attrs:
			blend_node = selected.split(".")[0]
			target_attr = selected.split(".")[1]
			geo = cmds.blendShape(blend_node, q=1, geometry=1)
			cmds.setAttr(selected, 1)
			dup = cmds.duplicate(geo, rr=True,  name=target_attr + "_bsgeo")
			attributeslib.set_attributes([dup[0]], ["t", "r", "s", "v", "ro", "jo", "radius"], lock=False, keyable=True,
			                             user_defined=True)
			cmds.parent(dup[0], world=True)
			export_nodes.append(dup[0])

			# prompt user for new name if desired and build asset export path
			export_name, _ = QtWidgets.QInputDialog.getText(self, "Export Asset",
				                                                "Enter the name for the exported asset:",
				                                                QtWidgets.QLineEdit.Normal,
				                                                node)
			if not export_name:
				return

			export_path = os.path.join(self.dir_field.text(), f"{export_name}.mb")
			thumbnail_path = os.path.join(self.dir_field.text(), f"{export_name}.png")

			# Isolate, capture thumbnail and export attr as blendshape
			cam = self.prep_lib_thumbnail(node)
			mel_cmd = ('file -typ "mayaBinary" -es  \"' + export_path + '"')
			cmds.thumbnailCaptureComponent(capture=0, fdp=0, fdc=mel_cmd)
			cmds.thumbnailCaptureComponent(save=export_path)
			cmds.thumbnailCaptureComponent(closeCurrentSession=True)
			self.capture_viewport_snapshot(thumbnail_path)
			cmds.file(export_path, exportSelected=True, type="mayaBinary", force=True)
			self.archive_lib_element(name=node)

			# Set the thumbnail for the exported item
			item = QtWidgets.QListWidgetItem(f"{export_name}.mb")
			item.setData(QtCore.Qt.UserRole, export_path)
			item.setIcon(QtGui.QIcon(thumbnail_path))
			self.ui_list_widget.addItem(item)

			print("Export Complete", f"Asset exported to {export_path}")
			self.update_lib_lib_asset_list()
			if cmds.objExists(cam):
				cmds.delete(cam)

		self.update_lib_lib_asset_list()
		QtWidgets.QMessageBox.information(self, "exportCompleted", "All export Completed Successfully")

	def prep_lib_thumbnail(self, node=None):
		"""
		creates cam and  isolates node
		:return camera is returned so it can be deleted after the loop
		"""
		if not node:
			return ("please specify node for snapshot")
		cam = "snap_cam"
		if not cmds.objExists("snap_cam"):
			cam = cmds.camera(name="snap_cam")[0]
			panel = cmds.getPanel(visiblePanels=True)[0]
			cmds.lookThru(panel, cam)
			cmds.select(node)
			cmds.viewFit(cam, fitFactor=1.0)  # Frame the selected object perfectly in the camera view
			isolated_panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
			cmds.isolateSelect(isolated_panel, state=1)
		return (cam)


	def archive_lib_element(self, name):
		"""
		finds the latest version of file of versions up one
		if no file exists then v1 of file will be copied and moved to backup folder
		:type name:  base name of file
		:return:
		"""
		# check to see if file name  exist.
		archive_dir = pathlib.normpath(os.path.join(self.dir_field.text(), "archive"))
		export_path = pathlib.normpath(os.path.join(self.dir_field.text(), name + ".mb"))
		thumbnail_path  = pathlib.normpath(os.path.join(self.dir_field.text(), name + ".png"))
		# if dir doesn't exist, it will be created here
		if not os.path.exists(archive_dir):
			pathlib.make_dirs(archive_dir)
		#copy, version and move to back up directory
		version_obj = pathlib.Version(archive_dir, name + ".mb", "mayaBinary")
		version_path =pathlib.normpath(version_obj.get_new_version_path())
		try:
			shutil.copy(export_path, version_path)
			if os.path.exists(thumbnail_path):
				os.remove(thumbnail_path)
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, "Error",
			                               f"Could not archive asset: {str(e)} ")

		# if not os.path.exists(version_path):
		# 	try:
		# 		shutil.copy(export_path, version_path)
		# 		os.remove(export_path)
		# 		# if os.path.exists(thumbnail_path):
		# 		# 	os.remove(thumbnail_path)
		# 		# self.update_lib_lib_asset_list()
		# 	except Exception as e:
		# 		QtWidgets.QMessageBox.critical(self, "Error",
		# 		                               f"Could not archive asset: {str(e)} ")

	def capture_viewport_snapshot(self, save_path):
		# Capture a snapshot of the current viewport
		cmds.playblast(frame=[cmds.currentTime(query=True)], format='image', completeFilename=save_path, viewer=False,
		               showOrnaments=False, width=800, height=600)
		print(f"Snapshot saved at {save_path}")

	def regenerate_thumbnail(self):
		# Re-generate the thumbnail for the currently selected item
		item = self.ui_list_widget.currentItem()
		if item:
			file_path = item.data(QtCore.Qt.UserRole)
			thumbnail_path = os.path.join(self.dir_field.text(),
			                              f"{os.path.splitext(os.path.basename(file_path))[0]}.png")
			self.capture_viewport_snapshot(thumbnail_path)
			self.display_detail()

	def delete_lib_asset(self):
		# Delete the selected .mb file from the directory
		item = self.ui_list_widget.currentItem()
		if item:
			file_path = item.data(QtCore.Qt.UserRole)
			confirm = QtWidgets.QMessageBox.question(self, "Delete Asset",
			                                         f"Are you sure you want to delete {file_path}?",
			                                         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
			if confirm == QtWidgets.QMessageBox.Yes:
				try:
					os.remove(file_path)
					thumbnail_path = os.path.join(self.dir_field.text(),
					                              f"{os.path.splitext(os.path.basename(file_path))[0]}.png")
					if os.path.exists(thumbnail_path):
						os.remove(thumbnail_path)
					self.update_lib_lib_asset_list()
					QtWidgets.QMessageBox.information(self, "Delete Complete", "Asset deleted successfully.")
				except Exception as e:
					QtWidgets.QMessageBox.critical(self, "Error", f"Could not delete asset: {str(e)}")


# Show the UI
def show():
	global window
	if cmds.window("AssetManagerWindow", exists=True):
		cmds.deleteUI("AssetManagerWindow", wnd=True)

	window = AssetManagerUI()
	window.setObjectName("AssetManagerWindow")
	window.show()
	return window


