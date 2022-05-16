from setuptools import find_packages, setup

__version__ = "0.5.16"
__pkg_name__ = "sypht"

setup(
    name=__pkg_name__,
    version=__version__,
    description="Sypht Python Client",
    author="Sypht Pty Ltd.",
    packages=find_packages(),
    url="https://sypht.com",
    entry_points={"console_scripts": ["sypht = sypht.__main__:main"]},
    classifiers=[
        "Environment :: Console",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    install_requires=["requests>=2.26.0", "urllib3>=1.26.5"],
)
