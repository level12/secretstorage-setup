.. default-role:: code

SecretStorage Setup Introduction
################################

SecretStorage Setup is a small project and command line utility to facilitate the setup
of `SecretStorage`_ in a `virtualenv`_. It was created primarily to make it easy for developers to
use the SecretStorage backend in `keyring_`.

.. _virtualenv: https://virtualenv.pypa.io/en/latest/
.. _keyring: https://pypi.python.org/pypi/keyring

Usage
=====

Install
-------

This package should be installed inside a virtualenv::

    # I'm using vex to create and activate virtualenv.  You can use whatever tool you are used to.
    $ vex -m example
    $ pip install SecretStorage-Setup


Status: Missing Dependencies
----------------------------

If you don't have all the dependencies installed in your system python, you may see something
like::

    $ ss-setup status
    dbus package...not installed for this python
    Crypto package...not installed for this python
    secretstorage package...not installed for this python

In which case, you should see "Dependencies" below for further help.

Linking System Dependencies
---------------------------

Since the SecretStorage dependencies are more easily installed using system tools than installing
into a virtualenv, the `link` command will use symlinks to setup the virtualenv to point to the
system packages::

    $ ss-setup status
    dbus package...needs linking into virtualenv
    Crypto package...needs linking into virtualenv
    secretstorage package...needs linking into virtualenv

    $ ss-setup link
    linking successful, run the status command to verify

    $ ss-setup status
    dbus package...ready
    Crypto package...ready
    secretstorage package...ready

Dependencies
============

`SecretStorage` is dependent on:

* `dbus-python`_
* PyCrypto_

.. _`dbus-python`: http://www.freedesktop.org/wiki/Software/DBusBindings#dbus-python
.. _PyCrypto: https://pypi.python.org/pypi/pycrypto

Debian/Ubuntu System Python
---------------------------

If you are running a Debian based system, you can install all needed dependencies in your system
python(s) as follows::

    $ sudo apt-get install python-dbus python-crypto python3-dbus python3-crypto

Manually Installed Python
-------------------------

If you have installed Python to a custom location, then you will need to build dbus and install
the packages by hand::

    # Assuming you have installed your Python in /opt/python34/ and `python3.4` is linked to the
    # Python binary correctly.
    $ sudo apt-get install libdbus-1-dev libdbus-glib-1-dev
    $ wget http://dbus.freedesktop.org/releases/dbus-python/dbus-python-1.2.0.tar.gz
    $ tar -xzf dbus-python-1.2.0.tar.gz
    $ cd dbus-python-1.2.0
    $ PYTHON=python3.4 ./configure --prefix=/opt/python34
    $ make
    $ sudo make install
    $ sudo /opt/python34/bin/pip install pycrypto secretstorage


Issues & Discussion
====================

Please direct questions, comments, bugs, feature requests, etc. to:
https://github.com/level12/secretstorage-setup/issues

Current Status
==============

Currently tested on Ubuntu 14.04 with:

* Ubuntu Python 2.7
* Ubuntu Python 3.4.0
* Manual install Python 3.4.3

Issues and pull requests welcome.

.. _SecretStorage: https://pypi.python.org/pypi/SecretStorage

