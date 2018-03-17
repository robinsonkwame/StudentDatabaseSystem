from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
	long_description = f.read()

setup(
	name='''ckanext-emailauth''',
	version='0.1.0',
	description='''Email authentication''',
	long_description=long_description,
	url='https://github.com/robinsax/ckanext-emailauth',
	author='''Robin Saxifrage''',
	author_email='''robinsaxifrage@live.ca''',
	
	license='AGPL',
	classifiers=[
		'Development Status :: 1 - Beta',
		'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
		'Programming Language :: Python :: 2.7',
	],
	
	keywords='''CKAN''',
	packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
	namespace_packages=['ckanext'],
	install_requires=[],
	include_package_data=True,
	package_data={},
	data_files=[],
	
	entry_points='''
		[ckan.plugins]
		emailauth=ckanext.emailauth.plugin:EmailAuthPlugin
		
		[babel.extractors]
		ckan = ckan.lib.extract:extract_ckan
	''',
	message_extractors={
		'ckanext': [
			('**.py', 'python', None),
			('**.js', 'javascript', None),
			('**/templates/**.html', 'ckan', None),
		],
	}
)

