# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import setup, find_packages

DISTUTILS_DEGUB = True


setup(
    name = 'geodjango-softgis-api',
    version = '0.1',
    description = 'softgis api with REST and javascript',
    url = 'http://github.com/ksnabb/geodjango-softgis-api',
    author = 'Kristoffer Snabb',
    author_email = 'kristoffer.snabb@gmail.com',
    install_requires = [
        'Django >= 1.2',
        'django-email-confirmation >= 0.1.4',
        'django-openid-consumer >= 0.1.1',
	'pymongo >= 1.9'
        ],
    packages = find_packages(),
    include_package_data = True,
    )
