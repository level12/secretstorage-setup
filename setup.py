import os.path as osp
import sys

from setuptools import setup, find_packages

cdir = osp.abspath(osp.dirname(__file__))
with open(osp.join(cdir, 'README.rst')) as fo:
    README = fo.read()
with open(osp.join(cdir, 'CHANGELOG.rst')) as fo:
    CHANGELOG = fo.read()

version_fpath = osp.join(cdir, 'sssetup', 'version.py')
version_globals = {}
with open(version_fpath) as fo:
    exec(fo.read(), version_globals)

install_requires = [
    'click',
]


if sys.version_info[0] == 2:
    install_requires.append('pathlib')


setup(
    name="SecretStorage Setup",
    version=version_globals['VERSION'],
    description=('Ease setup of SecretStorage in virtualenvs'),
    long_description='\n\n'.join((README, CHANGELOG)),
    author="Randy Syring",
    author_email="randy.syring@level12.io",
    url='https://github.com/level12/secretstorage-setup',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        ss-setup = sssetup:cli
    """,
)
