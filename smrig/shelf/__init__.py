import os

import maya.cmds as cmds
import maya.mel as mm
import smrig


def shelf():
	shelfName = 'smrig'

	if cmds.layout(shelfName, q=1, ex=1):
		result = mm.eval('deleteShelfTab "{0}";'.format(shelfName))
		if not result:
			raise RuntimeError('Could not delete {0} shelf!'.format(shelfName))

	# delete off disk
	sfiles = [os.path.join(cmds.internalVar(ush=1).split(':')[-1], 'shelf_{0}.mel'.format(shelfName)),
	          os.path.join(cmds.internalVar(ush=1).split(':')[-1], 'shelf_{0}.mel.deleted'.format(shelfName))]

	for sfile in sfiles:
		if os.path.isfile(sfile):
			os.remove(sfile)

	path = os.path.normpath(os.path.join(smrig.base_path, 'shelf', 'shelf_{0}.mel'.format(shelfName)))
	path = path.replace('\\', '/')
	mm.eval('loadNewShelf "{0}"'.format(path))
	mm.eval('saveAllShelves $gShelfTopLevel;')


def rig_shelf():
	shelfName = 'rigtools'

	if cmds.layout(shelfName, q=1, ex=1):
		result = mm.eval('deleteShelfTab "{0}";'.format(shelfName))
		if not result:
			raise RuntimeError('Could not delete {0} shelf!'.format(shelfName))

	# delete off disk
	sfiles = [os.path.join(cmds.internalVar(ush=1).split(':')[-1], 'shelf_{0}.mel'.format(shelfName)),
	          os.path.join(cmds.internalVar(ush=1).split(':')[-1], 'shelf_{0}.mel.deleted'.format(shelfName))]

	for sfile in sfiles:
		if os.path.isfile(sfile):
			os.remove(sfile)

	path = os.path.normpath(os.path.join(smrig.base_path, 'shelf', 'shelf_{0}.mel'.format(shelfName)))
	path = path.replace('\\', '/')
	mm.eval('loadNewShelf "{0}"'.format(path))
	mm.eval('saveAllShelves $gShelfTopLevel;')
