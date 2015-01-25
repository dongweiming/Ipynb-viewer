import os
pjoin = os.path.join

from setuptools import setup


def walk_subpkg(name):
    data_files = []
    package_dir = 'ipynbviewer'
    for parent, dirs, files in os.walk(os.path.join(package_dir, name)):
        # remove package_dir from the path
        sub_dir = os.sep.join(parent.split(os.sep)[1:])
        for f in files:
            data_files.append(os.path.join(sub_dir, f))
    return data_files

pkg_data = {
    "ipynbviewer": walk_subpkg('static') + walk_subpkg('templates')
}

install_requires = [
    l.strip() for l in open(
        pjoin(os.getcwd(), 'requirements.txt')).readlines()
    ]

setup_args = dict(
    name="ipynbviewer",
    version='0.1',
    packages=["ipynbviewer"],
    package_data=pkg_data,
    author="Dongweiming",
    author_email="ciici123@gmail.com",
    url='https://github.com/dongweiming/ipynb-viewer',
    description="Rendering local ipynb to static HTML",
    long_description="nbconvert as a web service",
    license="BSD",
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    install_requires=install_requires,
)

setup(**setup_args)
