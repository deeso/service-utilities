#!/usr/bin/env python
from setuptools import setup, find_packages

DESC ='Supporting classes and libraries for other modules'
setup(name='service-utilities',
      version='1.0',
      description=DESC,
      author='adam pridgen',
      author_email='dso@thecoverofnight.com',
      install_requires=['kombu', #'docker',
                        'redis', 'gglsbl',
                        'pymongo', 'pytz',
                        'tzlocal', 'pygrok',
                        'rule-chains', 'flask', 'requests',
                        'toml', 'ipython', 'cherrypy'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      dependency_links=[
            "https://github.com/deeso/rule-chains/tarball/master#egg=rule-chains-1.0.0",
      ],
      license="Apache 2"
      )
