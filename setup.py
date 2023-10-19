from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in inventeam_lns/__init__.py
from inventeam_lns import __version__ as version

setup(
	name="inventeam_lns",
	version=version,
	description="Lead Nurturing System",
	author="Inventeam Solutions Pvt Ltd",
	author_email="support@inventeam.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
