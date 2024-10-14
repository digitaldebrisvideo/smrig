import logging
import os

import maya.mel as mel

log = logging.getLogger("smrig.mel")

required_maya_scripts = ["createAndAssignShader.mel",
                         "channelBoxCommand.mel",
                         "cleanUpScene.mel",
                         "ikSpringSolver"]


def source():
	"""
	Source all mel files in mel directory plus required scripts.

	:return:
	"""
	mel_dir = os.path.dirname(__file__)
	files = [os.path.join(mel_dir, f).replace("\\", "/") for f in os.listdir(mel_dir) if f.endswith("mel")]

	for mel_file in files + required_maya_scripts:
		try:
			mel.eval('source "{}";'.format(mel_file))
			log.debug("Sourced: {}".format(mel_file))

		except ImportError:
			log.error("ERROR: {}".format(mel_file), exc_info=True)
