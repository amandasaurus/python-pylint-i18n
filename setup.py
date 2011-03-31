#! /usr/bin/env python

from distutils.core import setup

setup(name="pylint-i18n",
      version="0.1.3",
      description="Find strings in your code that should be passed through gettext",
      author="Rory McCann",
      author_email="rory@technomancy.org",
      url="http://www.technomancy.org/python/pylint-i18n-lint-checker/",
      py_modules=["missing_gettext"],
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Internationalization',
        'Topic :: Software Development :: Localization',
        'Topic :: Software Development :: Quality Assurance',
      ],
      install_requires=['pylint'],
)
