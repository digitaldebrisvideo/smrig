import os

import maya.cmds as cmds
from PySide2 import QtWidgets
from maya import OpenMayaUI
from shiboken2 import wrapInstance

try:
	maya_main_window = wrapInstance(long(OpenMayaUI.MQtUtil.mainWindow()), QtWidgets.QWidget)
except:
	maya_main_window = wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), QtWidgets.QWidget)

white_color = "#ccc"
red_color = "#ed3e70"
yellow_color = "#edca2f"
green_color = "#3eed61"
dark_green_color = "#08c767"
blue_color = "#3bc4eb"
grey_color = "#9e9e9e"
button_color = "#3e75ed"


def get_icon_path(file_name):
	"""
	Return absolute path to icon

	:param file_name:
	:return: icon abs path
	:rtype: str
	"""
	return os.path.join(os.path.dirname(__file__), "icons", file_name)


def create_ui_script_jobs(command, new=True, undo=False, redo=False, delete=True, create_node=False, compressUndo=True):
	"""

	:param command:
	:param new:
	:param undo:
	:param redo:
	:param delete:
	:param create_node:
	:param compressUndo:
	:return:
	"""
	sj_numbers = []
	if new:
		sj_numbers.append(cmds.scriptJob(e=['PreFileNewOrOpened', command], compressUndo=compressUndo))
	if undo:
		sj_numbers.append(cmds.scriptJob(e=['Undo', command], compressUndo=compressUndo))
	if redo:
		sj_numbers.append(cmds.scriptJob(e=['Redo', command], compressUndo=compressUndo))
	if delete:
		sj_numbers.append(cmds.scriptJob(ct=['delete', command], compressUndo=compressUndo))
	if create_node:
		sj_numbers.append(cmds.scriptJob(e=['DagObjectCreated', command], compressUndo=compressUndo))
	return sj_numbers


def kill_ui_script_jobs(sj_numbers):
	"""

	:param sj_numbers:
	:return:
	"""
	for sn in sj_numbers:
		try:
			if cmds.scriptJob(ex=sn):
				cmds.scriptJob(kill=sn, foe=True)
		except:
			pass
