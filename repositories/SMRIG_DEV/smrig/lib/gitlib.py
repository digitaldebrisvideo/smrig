import os
import subprocess


def get_hash():
	"""
	Return smrig git hash.

	:return:
	"""

	try:
		os.chdir(os.path.dirname(__file__))
		hash = subprocess.check_output(["git", "describe", "--always"]).strip().decode()
		print("# smrig git hash: {}".format(hash))

		return hash

	except:

		print("# info")

		return None
