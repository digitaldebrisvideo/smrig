import logging
import os

from smrig.env import prefs_
from smrig.env import utils
from smrig.userprefs import USE_FACILITY_PIPELINE

prefs = prefs_.Prefs()
current_job = os.getenv("VP_PROJECT")
log = logging.getLogger("smrig.env.job")


@utils.singleton
class Job(object):

	def __init__(self):

		# variables
		self._job = None
		self._job_path = None
		self._jobs_dict = {}
		self._base_directory = prefs.get_path_template().split("{job}")[0]

		# load assets
		self.reload_jobs()

	# ------------------------------------------------------------------------

	def get_job(self):
		"""
		:return: Active job
		:rtype: str/None
		"""
		return self._job

	def get_job_path(self):
		"""
		:return: Job base directory.
		:rtype: str/None
		"""
		return self._job_path

	def verify_job(self, name):
		"""
		:param str name:
		:return: Job name
		:rtype: str
		:raise RuntimeError: When job with provided name doesn't exist.
		"""
		self.reload_jobs()
		job = name if name in self._jobs_dict.keys() else None

		# validate asset
		if not job:
			error_message = "Unable to verify job '{}', options are {}".format(name, sorted(self._jobs_dict.keys()))
			log.error(error_message)
			raise RuntimeError(error_message)

		return job

	def set_job(self, name):
		"""
		:param str name:
		"""
		# get asset
		self.reload_jobs()

		if not name:
			self._job = None
			self._job_path = None
			log.debug("Set job: {} {}".format(self._job, self._job_path))
			return

		self._job = self.verify_job(name)
		self._job_path = self._jobs_dict.get(name)

		log.debug("Set job: {} {}".format(self._job, self._job_path))

	# ------------------------------------------------------------------------
	def get_jobs(self):
		"""
		:return: Assets related to the current project
		:rtype: list[Asset]
		"""
		self.reload_jobs()
		return sorted(self._jobs_dict.keys())

	def reload_jobs(self):
		"""
		Clear the cache on the assets function, which means that next time the
		assets are queried
		"""
		self._base_directory = prefs.get_path_template().split("{job}")[0]

		jobs = [d for d in os.listdir(self._base_directory) if
		        not d.startswith(".") and os.path.isdir(utils.join(self._base_directory, d))]

		if USE_FACILITY_PIPELINE and current_job:
			jobs = [current_job]

		job_dirs = [utils.join(self._base_directory, d) for d in jobs]

		for job, directory in zip(jobs, job_dirs):
			self._jobs_dict[job] = directory

		log.debug("Reloaded jobs")

	def create_job(self, name):
		"""
		Create a new job.

		:param name:
		:return:
		"""
		if USE_FACILITY_PIPELINE:
			log.warning("Cannot create job when LOCK_JOB setting is enabled.")
			return

		self.reload_jobs()
		self._base_directory = prefs.get_path_template().split("{job}")[0]

		name = utils.construct_name(name)
		if name in self.get_jobs():
			error_message = "{} is already an existing job.".format(name)
			log.warning(error_message)

			self.reload_jobs()
			self.set_job(name)
			return

		directory = utils.join(self._base_directory, name)
		utils.make_dirs(directory)

		if os.path.isdir(directory):
			log.info("Created job: {}".format(name))
			self.reload_jobs()
			self.set_job(name)
