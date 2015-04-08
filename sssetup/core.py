import distutils.sysconfig as distutils_sysconfig
import os
import pathlib
import sysconfig


class FatalError(Exception):
    pass


class SystemPackage(object):
    """
        Assuming you are in a virtualenv, this class can find shared object files and directories
        in the system python's site packages area.  Presumably as a precursor to linking them into
        the virtualenv.
    """
    shared_objects = ()

    def __init__(self):
        self.messages = []

    @property
    def syspy_packages_dpath(self):
        stdlib_dpath = pathlib.Path(distutils_sysconfig.get_python_lib(standard_lib=True))
        if stdlib_dpath.joinpath('site-packages').exists():
            return stdlib_dpath.joinpath('site-packages')

        # if we didn't find site-packages, then try a Debian python3 layout. In that case,
        # stdlib_dpath is like:
        #
        #    /usr/lib/python3.4
        #
        # But we need to get to
        #
        #    /usr/lib/python3/dist-packages
        parent_dpath = stdlib_dpath.parent
        py3_dpath = parent_dpath.joinpath('python3').joinpath('dist-packages')
        if py3_dpath.exists():
            return py3_dpath
        self.messages.append('Couldn\'t find a dist-packages or site-packages directory from {}'
                             .format(stdlib_dpath))
        # todo: probably not the right behavior to return stdlib_dpath, but I don't want to throw an
        # exception at this point.
        return stdlib_dpath

    def syspy_dpath(self, dname):
        return self.syspy_packages_dpath.joinpath(dname)

    def syspy_so_fpath(self, identifier):
        # todo: the file name isn't always simple, sometimes it's like:
        # _dbus_glib_bindings.cpython-34m-x86_64-linux-gnu.so
        fname = '{}.{}-{}.so'.format(identifier, sysconfig.get_config_var('SOABI'),
                                     sysconfig.get_config_var('MULTIARCH'))
        if self.syspy_packages_dpath.joinpath(fname).exists():
            return self.syspy_packages_dpath.joinpath(fname)
        self.messages.append('Didn\'t find platform specific .so {}, assuming "plain" file exists'
                             .format(fname))

        fname = '{}.so'.format(identifier)
        return self.syspy_packages_dpath.joinpath(fname)

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
                    raise FatalError('Target path for linking exists, but is not a symlink: {}'
                                     .format(target_fpath))
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


class Status(object):
    def __init__(self, verbose):
        self.packages = DBUSPackage(), CryptoPackage(), SecretStorage()
        self.verbose = verbose

    def messages(self):
        for package in self.packages:
            yield package.status
        if self.verbose:
            yield 'Troubleshooting messages follow:'
            for package in self.packages:
                for message in package.messages:
                    yield '    {}: {}'.format(package.package, message)


class Linker(object):

    def __init__(self, verbose):
        self.packages = DBUSPackage(), CryptoPackage(), SecretStorage()
        self.verbose = verbose
        self._messages = []

    def run(self):
        venv_dpath = os.environ.get('VIRTUAL_ENV')
        if venv_dpath is None:
            self._messages.append('Error: not not in a virtualenv.')
            return

        venv_lib_dpath = distutils_sysconfig.get_python_lib()

        if self.verbose:
            self._messages.append('Virtualenv site-packages directory: {}'.format(venv_lib_dpath))

        for package in self.packages:
            package.link_to(venv_lib_dpath)

        return True

    def messages(self):
        for message in self._messages:
            yield message
        if self.verbose:
            yield 'More information follows:'
            for package in self.packages:
                for message in package.messages:
                    yield '    {}: {}'.format(package.package, message)
