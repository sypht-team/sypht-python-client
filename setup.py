from setuptools import setup, find_packages

__version__ = '0.1.2'
__pkg_name__ = 'sypht'

setup(
    name = __pkg_name__,
    version = __version__,
    description = 'Sypht Python Client',
    author='Sypht Pty Ltd.',
    packages = find_packages(),
    url = 'https://sypht.com',
    entry_points = {},
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Artificial Intelligence'
    ],
    install_requires=[
        'requests==2.19.1',
        'six==1.11.0'
    ]
)
