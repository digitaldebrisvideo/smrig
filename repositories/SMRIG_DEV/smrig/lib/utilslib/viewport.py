import maya.cmds as cmds


def set_dull_panel():
	"""
	Temporarily change to dope sheet or another "dull" window for baking purposes
	Can be used to toggle on a limited basis(at least within the same script scope in most cases).
	"""
	# Get the visible model panel - assumes only one!
	visible_panels = cmds.getPanel(visiblePanels=True)
	model_panel = None
	if visible_panels:
		for panel in visible_panels:
			if panel.find("modelPanel") != -1:
				model_panel = panel
				# Temporarily change to dope sheet or another "dull" window
				cmds.scriptedPanel('dopeSheetPanel1', rp=model_panel, e=1)
	return model_panel


def set_model_panel(model_panel):
	"""
	Set the model panel from a scriptedPanel
	"""
	if model_panel:
		cmds.modelPanel(model_panel, rp="dopeSheetPanel1", e=1)


class ModelPanel(object):
	"""
	Set various options for the maya model panel.

	More types available at:
	https://help.autodesk.com/cloudhelp/2015/CHS/Maya-Tech-Docs/Commands/modelEditor.html

	Example
		.. code-block:: python

			mp = ModelPanel()
			mp.set_allObjects_vis(0)
			mp.set_joints_vis(1)
			mp.set_jointXray_vis(0)
			mp.set_polymeshes_vis(1)
	"""

	def __init__(self):
		self._model_panel = self.get_model_panel()

	# ------------------------------------------------------------------------

	@property
	def model_panel(self):
		"""
		:return: Model panel
		:rtype: str
		"""
		return self._model_panel

	def get_model_panel(self):
		"""
		:return: Model panel
		:rtype: str/None
		"""
		# TODO: support multiple model panels?
		model_panels = cmds.getPanel(visiblePanels=True) or []
		for model_panel in model_panels:
			if model_panel.find("modelPanel") != -1:
				return model_panel

	# ------------------------------------------------------------------------

	def set_all_objects_vis(self, val=1):
		"""
		Turn on/off the display of all objects for the view of the model editor.
		This excludes NURBS, CVs, hulls, grids and manipulators.
		"""
		cmds.modelEditor(self.model_panel, edit=True, allObjects=val)

	def set_renderer(self, renderer_name="vp2Renderer"):
		"""
		:param str renderer_name: 'vp2Renderer' or 'base_OpenGL_Renderer'
		"""
		cmds.modelEditor(self.model_panel, edit=True, rendererName=renderer_name)

	def set_locator_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, locators=value)

	def set_nurbs_curves_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, nurbsCurves=value)

	def set_deformers_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, deformers=value)

	def set_ik_handles_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, ikHandles=value)

	def set_joints_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, joints=value)

	def set_joint_xray_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, jointXray=value)

	def set_lights_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, lights=value)

	def set_grid_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, grid=value)

	def set_polymeshes_vis(self, value=True):
		"""
		:param bool value:
		"""
		cmds.modelEditor(self.model_panel, edit=True, polymeshes=value)
