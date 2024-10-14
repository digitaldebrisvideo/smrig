class Default(object):

	def __init__(self):
		pass

	def post_skel(self):
		"""
		Runs after skeleton has been built.

		:return:
		"""
		pass

	def post_rig(self):
		"""
		Runs after the control rig has been built.

		:return:
		"""
		pass

	def pre_bind(self):
		"""
		Runs before the model is bound.

		:return:
		"""
		pass

	def post_bind(self):
		"""
		Runs after the model is bound.

		:return:
		"""
		pass

	def post_finalize(self):
		"""
		Last function to run in the build.

		:return:
		"""
		pass
