import distutils.sysconfig as distutils_sysconfig
import os
import pathlib
import sysconfig
import sys


class FatalError(Exception):
    pass


class MessageLogger(object):
    def __init__(self):
        self.messages = []
        self.init()

    def init(self):
        pass

    def log(self, msg):
        self.messages.append(msg)

    @property
    def label(self):
        return NotImplemented


class SystemSetup(MessageLogger):

    def init(self):
        """
            Determine where the
        """
        self.uses_major_version_package_dpath = False
        self.dist_packages_dpath = None
        self.site_packages_dpath = None

        # See stuff like:
        #  /usr/lib/python3.5
        #  /opt/python34/lib/python3.4
        #  /usr/lib/python2.7
        stdlib_dpath = pathlib.Path(distutils_sysconfig.get_python_lib(standard_lib=True))
        self.log('Stdlib directory: {}'.format(stdlib_dpath))

        # See if we are dealing with a Python that stores files in a major version directory
        # path like:
        # /usr/lib/python3/dist-packages
        dist_packages_dpath = stdlib_dpath.joinpath('dist-packages')
        if dist_packages_dpath.exists():
            self.dist_packages_dpath = dist_packages_dpath
            self.log('dist-packages directory: {}'.format(dist_packages_dpath))
        else:
            minor_version_dpath, _ = str(stdlib_dpath).rsplit('.', 1)
            minor_version_dist_packages_dpath = pathlib.Path(minor_version_dpath, 'dist-packages')
            if minor_version_dist_packages_dpath.exists():
                self.uses_major_version_package_dpath = True
                self.dist_packages_dpath = minor_version_dist_packages_dpath
                self.log('dist-packages directory: {}'.format(minor_version_dist_packages_dpath))

        # Look for the site-packages directory.
        site_packages_dpath = stdlib_dpath.joinpath('site-packages')
        if site_packages_dpath.exists():
            self.site_packages_dpath = site_packages_dpath
            self.log('site-packages directory: {}'.format(site_packages_dpath))

        # Look for the /usr/local/lib version if applicable.
        stdlib_strpath = str(stdlib_dpath)
        if stdlib_strpath.startswith('/usr/lib/python'):
            stdlib_strpath = stdlib_strpath.replace('/usr/lib/', '/usr/local/lib/')
            site_packages_dpath = pathlib.Path(stdlib_strpath, 'site-packages')
            if site_packages_dpath.exists():
                self.site_packages_dpath = site_packages_dpath
                self.log('site-packages directory: {}'.format(site_packages_dpath))

    @property
    def label(self):
        return 'system'


class SystemPackage(MessageLogger):
    """
        Assuming you are in a virtualenv, this class can find shared object files and directories
        in the system python's site packages area.  Presumably as a precursor to linking them into
        the virtualenv.
    """
    shared_objects = ()

    def __init__(self, system_setup):
        self.messages = []
        self.system_setup = system_setup
        self._package_dpath = None
        self.use_multiarch_fnames = False

    @property
    def label(self):
        return self.package

    def locate_package_dpath(self):
        """
            Determine where we will find this package: in dist-packages or site-packages.
        """
        dpath = self.system_setup.site_packages_dpath.joinpath(self.package)
        if dpath.exists():
            return self.system_setup.site_packages_dpath
        dpath = self.system_setup.dist_packages_dpath.joinpath(self.package)
        if dpath.exists():
            if self.system_setup.uses_major_version_package_dpath:
                self.use_multiarch_fnames = True
            return self.system_setup.dist_packages_dpath
        # Couldn't find package directory, return False to indicate this.
        return False

    def package_dpath(self):
        """
            Cached version of locate_package_dpath()
        """
        # We have already looked for the package and can't find it.
        if self._package_dpath is False:
            return None
        if self._package_dpath is None:
            self._package_dpath = self.locate_package_dpath()
        return self._package_dpath

    def syspy_dpath(self, dname):
        return self.package_dpath().joinpath(dname)

    def syspy_so_fpath(self, identifier):
        if self.use_multiarch_fnames:
            fname = '{}.{}-{}.so'.format(identifier, sysconfig.get_config_var('SOABI'),
                                         sysconfig.get_config_var('MULTIARCH'))
        else:
            fname = '{}.so'.format(identifier)

        return self.package_dpath().joinpath(fname)

    def file_system_paths(self):
        paths = [self.syspy_so_fpath(ident) for ident in self.shared_objects]
        paths.append(self.syspy_dpath(self.package))
        return paths

    @property
    def available(self):
        available = True
        for fspath in self.file_system_paths():
            if not fspath.exists():
                available = False
                self.messages.append('Couldn\'t find system python file: {}'.format(fspath))
        return available

    @property
    def status(self):
        if self.ready:
            return '{} package...ready'.format(self.package)
        if self.available:
            return '{} package...needs linking into virtualenv'.format(self.package)
        return '{} package...not installed for this python'.format(self.package)

    def link_to(self, target_dpath):
        if not self.available:
            raise FatalError('Package {} is unavailable, run `ss-setup status -v` command for'
                             ' more info.'.format(self.package))

        for fspath in self.file_system_paths():
            target_fpath = pathlib.Path(target_dpath, fspath.name)
            if target_fpath.exists():
                if not target_fpath.is_symlink():
                    self.messages.append('path already exists, assuming local package available: {}'.format(target_fpath))
                    continue
                target_fpath.unlink()
            target_fpath.symlink_to(fspath)
            self.messages.append('linked {} to {}'.format(target_fpath, fspath))


class DBUSPackage(SystemPackage):
    shared_objects = '_dbus_bindings', '_dbus_glib_bindings'
    package = 'dbus'

    @property
    def ready(self):
        try:
            import dbus
            import dbus.types
            dbus.types   # silence flake8
            return True
        except Exception:
            return False


class CryptoPackage(SystemPackage):
    package = 'Crypto'

    @property
    def ready(self):
        try:
            import Crypto
            Crypto  # silence flake8
            return True
        except Exception:
            return False


class SecretStorage(SystemPackage):
    package = 'secretstorage'

    @property
    def ready(self):
        try:
            # this will throw an exception of all the dependencies didn't get setup correctly
            import secretstorage
            bus = secretstorage.dbus_init()
            list(secretstorage.get_all_collections(bus))
            return True
        except Exception:
            return False


class Action(MessageLogger):
    def __init__(self, verbose):
        super(Action, self).__init__()
        self.system_setup = system_setup = SystemSetup()
        self.packages = DBUSPackage(system_setup), CryptoPackage(system_setup), \
            SecretStorage(system_setup)
        self.verbose = verbose

    def yield_messages(self):
        for message in self.messages:
            yield message
        if self.verbose:
            yield 'Troubleshooting messages follow:'
            for msg_logger in [self.system_setup] + list(self.packages):
                for message in msg_logger.messages:
                    yield '    {}: {}'.format(msg_logger.label, message)

class Status(Action):
    def run(self):
        for package in self.packages:
            self.log(package.status)

class Linker(Action):

    def run(self):
        venv_dpath = os.environ.get('VIRTUAL_ENV')
        if venv_dpath is None:
            self.log('Error: not not in a virtualenv.')
            return

        venv_lib_dpath = distutils_sysconfig.get_python_lib()

        if self.verbose:
            self.log.append('Virtualenv site-packages directory: {}'.format(venv_lib_dpath))

        for package in self.packages:
            package.link_to(venv_lib_dpath)

        return True

    def messages(self):
        for message in self._messages:
            yield message
        if self.verbose:
            yield 'More information follows:'
            for message in self.system_setup.logs:
                yield '    system: {}'.format(message)

            for package in self.packages:
                for message in package.messages:
                    yield '    {}: {}'.format(package.package, message)
