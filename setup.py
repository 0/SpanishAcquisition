#!/usr/bin/env python2

from setuptools import setup, find_packages


def included_package(p):
	return p.startswith('spacq.') or p == 'spacq'


setup(
	name='Spanish Acquisition',
	version='0.1',
	author='Dmitri Iouchtchenko',
	author_email='diouchtc@uwaterloo.ca',
	description='Package for interfacing with devices and building user '
			'interfaces.',
	packages=[p for p in find_packages() if included_package(p)],
)
