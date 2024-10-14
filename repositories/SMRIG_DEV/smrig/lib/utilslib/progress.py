# TODO: move to guilib?
import maya.cmds as cmds

from smrig.lib.utilslib import mel


class ProgressBar(object):
	"""
	The progress bar context will help keep track of task that take quite a
	long time. The context will make it easier to initialize, manage and kill
	the progress bar. Because the progress bar can be used as a context it
	will automatically initialize on entry and kill on exit of the context.

	Example:
		.. code-block:: python

			with ProgressBar(maximum=10) as progress_bar:
				for i in range(10):
					time.sleep(0.1)
					progress_bar.next()

	:param int maximum:
	:param str message:
	"""

	def __init__(self, maximum=100, message="In progress..."):
		self._maximum = maximum
		self._message = message
		self._progress_bar = mel.get_mel_global_variable("$gMainProgressBar")

	# ------------------------------------------------------------------------

	def __enter__(self):
		self.initialize()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.kill()

	# ------------------------------------------------------------------------

	@property
	def message(self):
		"""
		:return: Message
		:rtype: str
		"""
		return self._message

	@property
	def maximum(self):
		"""
		:return: Maximum number of iteration
		:rtype: int
		"""
		return self._maximum

	@property
	def progress_bar(self):
		"""
		:return: Path to progress bar
		:rtype: str
		"""
		return self._progress_bar

	# ------------------------------------------------------------------------

	def initialize(self):
		"""
		Initialize the progress bar. It will begin the progress and set the
		message and maximum number of iterations.
		"""
		cmds.progressBar(
			self.progress_bar,
			edit=True,
			beginProgress=True,
			isInterruptable=False,
			status=self.message,
			maxValue=self.maximum
		)

	def next(self):
		"""
		Increase the progress bar amount by one.
		"""
		cmds.progressBar(self.progress_bar, edit=True, step=True)

	def kill(self):
		"""
		End the progress bar.
		"""
		cmds.progressBar(self.progress_bar, edit=True, endProgress=True)
