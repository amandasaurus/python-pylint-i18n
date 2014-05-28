#! /usr/bin/env python

from setuptools import setup

setup(name="pylint-i18n",
      version="1.0.0",
      description="Find strings in your code that should be passed through gettext",
      author="Rory McCann",
      author_email="rory@technomancy.org",
      url="http://www.technomancy.org/python/pylint-i18n-lint-checker/",
      py_modules=["missing_gettext"],
      test_suite='tests',
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Internationalization',
        'Topic :: Software Development :: Localization',
        'Topic :: Software Development :: Quality Assurance',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
      ],
      install_requires=['pylint'],
)
