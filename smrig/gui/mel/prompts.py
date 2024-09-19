from functools import partial

import maya.cmds as cmds


def confirm_dialog(title="smrig", message="Are you sure?", button=["Yes", "No"], icon="info"):
	"""
	Wrapper for confirm dialog.

	:param title:
	:param message:
	:param button:
	:param icon:
	:return: bool
	"""
	result = cmds.confirmDialog(title=title,
	                            message=message,
	                            button=button,
	                            defaultButton=button[0],
	                            cancelButton=button[1],
	                            dismissString=button[1],
	                            icon=icon)

	if result == button[0]:
		return True
	return False


def prompt_dialog(title="smrig", message="Are you sure?", button=["Yes", "No"]):
	"""
	Wrapper for confirm dialog.

	:param title:
	:param message:
	:param button:
	:return: bool
	"""
	result = cmds.promptDialog(title=title,
	                           message=message,
	                           button=button,
	                           defaultButton=button[0],
	                           cancelButton=button[1],
	                           dismissString=button[1])

	if result == button[0]:
		return cmds.promptDialog(query=True, text=True)

	return False


def option_prompt(current_side="", current_name="", editable_side=True, editable_name=True, message=None):
	"""
	MEL modal dialog for specifying new side and new name options.

	:param str current_side:
	:param str current_name:
	:return: new_side, new_name
	:rtype: list
	"""

	def ui(current_side="", current_name="", editable_side=True, editable_name=True, message=None):
		"""
		mel ui layout

		:param str current_side:
		:param str current_name:
		:return:
		"""
		default_msg = 'Current options will result in name clashes.\nPlease change "side" or "name" options.'
		message = message if message else default_msg

		form = cmds.setParent(q=True)
		icon = cmds.iconTextButton(style="iconOnly", flat=1, image1="warning_24x24.png")
		text = cmds.text(l=message)

		sfg = cmds.textFieldGrp(l="Side: ", text=current_side, cw2=[60, 60], ad2=2, editable=editable_side)
		nfg = cmds.textFieldGrp(l="Name: ", text=current_name, cw2=[60, 60], ad2=2, editable=editable_name)

		cmd = "'{} {}'.format"
		cmd += "(cmds.textFieldGrp('{}', q=1, text=True), cmds.textFieldGrp('{}', q=1, text=True))".format(sfg, nfg)

		b1 = cmds.button(l="Continue", c="cmds.layoutDialog( dismiss={} )".format(cmd))
		b2 = cmds.button(l="Cancel", c="cmds.layoutDialog( dismiss='Cancel' )")

		cmds.formLayout(form, e=True,
		                attachForm=[(icon, 'top', 12),
		                            (icon, 'left', 20),
		                            (text, 'top', 12),
		                            (text, 'right', 12),
		                            (sfg, "left", 6),
		                            (sfg, "right", 6),
		                            (nfg, "left", 6),
		                            (nfg, "right", 6),
		                            (b1, "left", 12),
		                            (b2, "right", 12),
		                            (b1, "bottom", 12),
		                            (b2, "bottom", 12)],
		                attachControl=[(text, "left", 12, icon),
		                               (sfg, "top", 12, text),
		                               (nfg, "top", 3, sfg),
		                               (b1, "top", 6, nfg),
		                               (b2, "top", 6, nfg)],
		                attachPosition=[(b1, "right", 4, 50),
		                                (b2, "left", 4, 50)])

	result = cmds.layoutDialog(ui=partial(ui, current_side, current_name, editable_side, editable_name, message),
	                           title="smrig")
	return None if result == "Cancel" else result.split(" ")


def migrate_prompt(paths):
	"""
	MEL modal dialog for specifying migrate target path.

	:param list paths:
	:return: target path
	:rtype: str
	"""

	def ui(paths):
		"""
		mel ui layout

		:param list paths:
		:return: selected path
		"""
		form = cmds.setParent(q=True)

		column = cmds.columnLayout(adj=1, rs=6)

		cmds.text(l='Migrate part module to target path:')
		tsl = cmds.textScrollList(numberOfRows=len(paths), ams=0, h=min(len(paths) * 24, 100))

		for path in paths:
			cmds.textScrollList(tsl, e=1, append=path)

		cmd = "'{}'.format"
		cmd += "(cmds.textScrollList('{}', q=1, si=True)[0])".format(tsl)

		cmds.setParent(form)
		b1 = cmds.button(l="Migrate", c="cmds.layoutDialog( dismiss={} )".format(cmd))
		b2 = cmds.button(l="Cancel", c="cmds.layoutDialog( dismiss='Cancel' )")

		cmds.formLayout(form, e=True,
		                attachForm=[
			                (column, 'top', 12),
			                (column, 'left', 12),
			                (column, 'right', 12),

			                (b1, "left", 12),
			                (b2, "right", 12),
			                (b1, "bottom", 12),
			                (b2, "bottom", 12)],

		                attachControl=(column, "bottom", 10, b1),

		                attachPosition=[(b1, "right", 4, 50),
		                                (b2, "left", 4, 50)],

		                attachNone=[(b1, 'top'), (b2, "top")]
		                )

	result = cmds.layoutDialog(ui=partial(ui, paths), title="smrig")
	return None if result == "Cancel" else result
