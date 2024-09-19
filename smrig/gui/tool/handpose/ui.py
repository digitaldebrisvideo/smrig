import logging

from PySide2 import QtCore, QtWidgets, QtGui
from maya import cmds

from smrig import env
from smrig.gui.mayawin import maya_main_window, get_icon_path
from smrig.lib import attributeslib
from smrig.lib import decoratorslib

log = logging.getLogger("smrig")


class HandPose(QtWidgets.QDialog):
	ctrl = None
	attr = None
	prefix = None
	pose_grps = None
	ctrls = None
	ctrl_suffix = env.prefs.get_suffix("animControl")
	grp_suffix = env.prefs.get_suffix("transform")
	type_token = "finger"

	valid_attrs = ["spread",
	               "fist",
	               "cup",
	               "reverseCup"]

	attr_tokens = {"MultX": "rx",
	               "MultY": "ry",
	               "MultZ": "rz"}

	def __init__(self, parent=maya_main_window):
		super(HandPose, self).__init__(parent)

		# Parent widget under Maya main window
		self.setParent(parent)

		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("sm Rig | Hand Pose UI")
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
		self.setWindowIcon(QtGui.QIcon(get_icon_path("logo.png")))

		layout = QtWidgets.QVBoxLayout(self)

		stamp_btn = QtWidgets.QPushButton("Stamp Pose")
		unstamp_btn = QtWidgets.QPushButton("Unstamp Pose")
		mirror_btn = QtWidgets.QPushButton("Copy Poses")
		save_btn = QtWidgets.QPushButton("Save All Poses")

		stamp_btn.clicked.connect(self.stamp_pose)
		unstamp_btn.clicked.connect(self.unstamp_pose)
		mirror_btn.clicked.connect(self.copy_pose)
		save_btn.clicked.connect(self.save)

		layout.addWidget(stamp_btn)
		layout.addWidget(unstamp_btn)
		layout.addWidget(mirror_btn)
		layout.addWidget(save_btn)

		self.setMinimumHeight(141)
		self.setMaximumHeight(141)
		self.setMinimumWidth(235)
		self.setMaximumWidth(235)

	def get_ctrl_attr(self, check_attribnute_name=True):
		"""

		:param check_attribnute_name:
		:return:
		"""
		self.ctrl = None
		self.attr = None
		self.prefix = None
		self.pose_grps = None
		self.ctrls = None

		selection = cmds.ls(sl=1)
		ctrl = selection[0] if selection else None
		if not ctrl:
			cmds.warning("Select a hand ctrl to set poses on!")
			return

		for attr in self.valid_attrs:
			if not cmds.objExists(ctrl + "." + attr):
				msg = attr + " not exist on this ctrl!"
				cmds.warning(msg)
				return

		selected_attrs = [a.split(".")[-1] for a in attributeslib.get_selected_attributes(ctrl)]

		if check_attribnute_name:
			if not selected_attrs:
				cmds.warning("Select an attribute in the channelbox to set poses on!")
				return

			attr = selected_attrs[0]
			if attr not in self.valid_attrs and "Curl" not in attr:
				cmds.warning("Current attr is not settable: " + attr)
				return

			self.attr = attr

		self.ctrl = ctrl
		self.type_token = "toe" if "toe" in ctrl else "finger"
		self.prefix = ctrl.split("{}s".format(self.type_token))[0]
		self.pose_grps = cmds.ls("{}*_{}_fk*_offset1_GRP".format(self.prefix, self.type_token))
		self.ctrls = [c.replace("offset1_" + self.grp_suffix, self.ctrl_suffix) for c in self.pose_grps]

		return True

	@decoratorslib.undoable
	@decoratorslib.preserve_selection
	def stamp_pose(self):
		"""

		:return:
		"""
		if not self.get_ctrl_attr():
			return

		for ctrl, grp in zip(self.ctrls, self.pose_grps):
			for tkn, att in self.attr_tokens.items():
				pose_attribute = "{}.{}{}".format(grp, self.attr, tkn)
				ctrl_attribute = "{}.{}".format(ctrl, att)

				if cmds.objExists(pose_attribute):
					cmds.setAttr(pose_attribute, cmds.getAttr(ctrl_attribute) * 0.1)

				else:
					log.warning("{} doesnt exist.. cannot set".format(pose_attribute))

			cmds.xform(ctrl, a=True, ro=[0, 0, 0])

		print("Stamped pose: {}.{}".format(self.ctrl, self.attr))

	@decoratorslib.undoable
	@decoratorslib.preserve_selection
	def unstamp_pose(self):
		"""

		:return:
		"""
		if not self.get_ctrl_attr():
			return

		attributeslib.reset_attributes(self.ctrl)

		for ctrl, grp in zip(self.ctrls, self.pose_grps):
			for tkn, att in self.attr_tokens.items():
				pose_attribute = "{}.{}{}".format(grp, self.attr, tkn)
				ctrl_attribute = "{}.{}".format(ctrl, att)

				if cmds.objExists(pose_attribute):
					cmds.setAttr(ctrl_attribute, cmds.getAttr(pose_attribute) * 10)

				else:
					log.warning("{} doesnt exist.. cannot set".format(pose_attribute))

		print("Unstamped pose: {}.{}".format(self.ctrl, self.attr))

	@decoratorslib.undoable
	def copy_pose(self):
		"""

		:return:
		"""
		if not self.get_ctrl_attr(check_attribnute_name=False):
			return

		selection = cmds.ls(sl=1)
		if not len(selection) == 2:
			cmds.warning("Select the source, then the desitnation hand ctrls to copy.")
			return

		dst_prefix = selection[1].split("{}s".format(self.type_token))[0]
		attrs = cmds.listAttr(self.ctrl, ud=True, k=True)

		for ctrl, grp in zip(self.ctrls, self.pose_grps):
			dst_grp = grp.replace(self.prefix, dst_prefix, 1)

			for attr in attrs:
				for tkn in self.attr_tokens.keys():
					src_pose_attribute = "{}.{}{}".format(grp, attr, tkn)
					dst_pose_attribute = "{}.{}{}".format(dst_grp, attr, tkn)

					if cmds.objExists(dst_pose_attribute):
						cmds.setAttr(dst_pose_attribute, cmds.getAttr(src_pose_attribute))

		cmds.select(selection[1])
		print("Copied poses from: {} to: {}".format(self.ctrl, selection[1]))

	def save(self):
		"""

		:return:
		"""
		nodes = [n.split(".")[0] for n in cmds.ls("*.smrigFingerPoses")]
		if not nodes:
			log.warning("Nothing to export")

		dataio.save_to_asset("attributeValues", nodes=nodes)


def run():
	"""

	:return:
	"""
	hand_ui = HandPose()
	hand_ui.show()
	return hand_ui
