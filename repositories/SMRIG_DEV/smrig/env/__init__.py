from smrig.env import assets
from smrig.env import job
from smrig.env import prefs_

# initialize classes
prefs = prefs_.Prefs()
asset = assets.Asset()

__job = job.Job()
__assets = assets.Assets()

# expose _job functions
get_job = __job.get_job
get_jobs = __job.get_jobs
get_job_path = __job.get_job_path

reload_jobs = __job.reload_jobs
create_job = __job.create_job

# expose assets functions
get_assets = __assets.get_assets
reload_assets = __assets.reload_assets
create_asset = assets.create_asset


# wrapper functions
def set_job(name):
	"""
	Wrapper for setting a job and resetting asset env.

	:param name:
	:return:
	"""
	__job.set_job(name)
	reload_assets()
