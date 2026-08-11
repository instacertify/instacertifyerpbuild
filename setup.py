from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
	long_description = f.read()

setup(
	name="instacertify",
	version="1.0.0",
	description="InstaCertify Consulting ERP on ERPNext v16",
	long_description=long_description,
	long_description_content_type="text/markdown",
	author="InstaCertify",
	author_email="nikhil@instacertify.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[],
)
