# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 SUSE LLC
#
# This file is part of ipa.
#
# See LICENSE for license information.

try:
    import configparser as ConfigParser
except ImportError:
    import ConfigParser

import fnmatch
import paramiko
import os
import random
import sys
import time
import yaml

from contextlib import contextmanager
from ipa_exceptions import IpaSSHException, IpaUtilsException
from tempfile import NamedTemporaryFile

CHARS = 'abcdefghijklmnopqrstuvwxyz'
CLIENT_CACHE = {}


def clear_cache(ip=None):
    """Clear the client cache or remove key matching the given ip."""
    if ip:
        with ignored(KeyError):
            del CLIENT_CACHE[ip]
    else:
        CLIENT_CACHE.clear()


def establish_ssh_connection(ip,
                             ssh_private_key,
                             ssh_user,
                             port,
                             attempts=5,
                             timeout=None):
    """Establish ssh connection and return paramiko client.

    If connection cannot be established in given number of attempts
    raise IpaProviderException.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()

    sys.stdout.write('Establishing ssh connection.')
    sys.stdout.flush()
    while attempts:
        try:
            client.connect(
                ip,
                port=port,
                username=ssh_user,
                key_filename=ssh_private_key,
                timeout=timeout
            )
        except:
            # Print without new lines
            sys.stdout.write('.')
            sys.stdout.flush()
            attempts -= 1
            time.sleep(10)
        else:
            print('\nConnection established.\n')
            return client

    raise IpaSSHException(
        'Failed to establish SSH connection to instance.'
    )


def execute_ssh_command(client, cmd):
    """Execute given command using paramiko and return stdout, stderr."""
    try:
        stdin, stdout, stderr = client.exec_command(cmd)
        err = stderr.read()
        if err:
            raise IpaSSHException(err)
        out = stdout.read()
    except:
        raise
    return out


def find_test_files(test_dirs, names=None):
    """Walk all dirs and find path of given test file names.

    If names is None find all test files in the given test
    directories and return the list.

    Raise IpaUtilsException:
    - If there are multiple test files or test descriptions with the
      same name.
    - If a test file or test description cannot be found.
    - If there is a name overlap with a test file and test
      description.
    """
    if names and not isinstance(names, list):
        raise IpaUtilsException(
            'Names must be a list containing test names'
            ' and/or test descriptions.'
        )

    tests = {}
    descriptions = {}
    for test_dir in test_dirs:
        for root, dirs, files in os.walk(test_dir):
            test_files = fnmatch.filter(files, 'test_*.py')
            description_files = fnmatch.filter(files, 'test_*.yaml')

            for test_file in test_files:
                path = os.path.join(root, test_file)
                name, ext = test_file.split('.')
                if name not in tests:
                    tests[name] = path
                else:
                    raise IpaUtilsException(
                        'Duplicate test file name found: %s, %s'
                        % (path, tests.get(name))
                    )

            for description_file in description_files:
                path = os.path.join(root, description_file)
                name, ext = description_file.split('.')
                if name in tests:
                    raise IpaUtilsException(
                        'Test description name matches test file: %s, %s'
                        % (path, tests.get(name))
                    )
                elif name not in descriptions:
                    descriptions[name] = path
                else:
                    raise IpaUtilsException(
                        'Duplicate test description file name found: %s, %s'
                        % (path, descriptions.get(name))
                    )

    if not names:
        tests.update(descriptions)
        return tests

    names = set(names)
    description_names = names & set(descriptions)
    names = names - description_names
    for name in description_names:
        names.update(
            get_tests_from_description(
                    name,
                    descriptions
            )
        )

    test_files = {}
    for name in names:
        try:
            test_name, test_case = name.split('::', 1)
        except:
            test_name, test_case = name, None

        path = tests.get(test_name, None)
        if not path:
            raise IpaUtilsException(
                'Test file with name: %s cannot be found.' % test_name
            )

        if test_case:
            path = ''.join([path, '::', test_case])
        test_files[name] = path

    return test_files


def get_config(config_path):
    """Parse ini config file."""
    if not os.path.isfile(config_path):
        raise IpaUtilsException(
            'Config file not found: %s' % config_path
        )

    config = ConfigParser.ConfigParser()
    try:
        result = config.read(config_path)
        if not result:
            raise
    except:
        raise IpaUtilsException(
            'Error parsing config file: %s' % config_path
        )

    return config


def get_from_config(config, section, default_section, entry):
    """Retrieve an entry from the configuration"""
    value = None
    with ignored(ConfigParser.Error):
        value = config.get(section, entry)

    if not value:
        try:
            value = config.get(default_section, entry)
        except ConfigParser.Error:
            raise IpaUtilsException(
                'Unable to get %s value from config' % entry
            )
    return value


def get_tests_from_description(name,
                               descriptions,
                               parsed=None):
    """Recursively collect all tests in test description.
    Args:
        name (str): Yaml test description file name.
        descriptions (dict): Dict of test description name
                             (key) and absolute file paths
                             (value).
        parsed (list): List of description paths which have
                       already been parsed to prevent infinte
                       recursion.
    """
    tests = []
    if not parsed:
        parsed = []

    description = descriptions.get(name, None)
    if not description:
        raise IpaUtilsException(
            'Test description file with name: %s cannot be located.'
            % name
        )

    if description in parsed:
        return tests

    parsed.append(description)
    test_data = get_yaml_config(description)

    if 'tests' in test_data:
        tests += test_data.get('tests')

    if 'include' in test_data:
        for description_name in test_data.get('include'):
            tests += get_tests_from_description(
                description_name,
                descriptions,
                parsed
            )

    return tests


def get_random_string(length=12, allowed_chars=CHARS):
    """Create random string of length with allowed characters."""
    return ''.join(random.choice(allowed_chars) for _ in range(length))


def get_ssh_client(ip,
                   ssh_private_key,
                   ssh_user='root',
                   port=22,
                   attempts=3,
                   timeout=10):
    """Attempt to establish and test ssh connection."""
    if ip in CLIENT_CACHE:
        return CLIENT_CACHE[ip]

    client = None
    while attempts:
        try:
            client = establish_ssh_connection(
                ip,
                ssh_private_key,
                ssh_user,
                port,
                timeout=timeout
            )
            execute_ssh_command(client, 'ls')
        except:
            if client:
                client.close()
            attempts -= 1
            timeout += timeout
        else:
            CLIENT_CACHE[ip] = client
            return client

    raise IpaSSHException(
        'Attempt to establish SSH connection failed.'
    )


def get_yaml_config(config_path):
    """Load yaml config file and return dictionary.

    TODO: This will need refactoring similar to the test search.
    """
    config_path = os.path.expanduser(config_path)
    if not os.path.isfile(config_path):
        raise IpaUtilsException(
            'Config file not found: %s' % config_path
        )

    with open(config_path, 'r') as f:
        config = yaml.load(f)
    return config


@contextmanager
def ignored(*exceptions):
    """Ignore the provided exception(s)."""
    try:
        yield
    except exceptions:
        pass


@contextmanager
def redirect_output(fileobj):
    """Redirect standard out to file."""
    old = sys.stdout
    sys.stdout = fileobj
    try:
        yield fileobj
    finally:
        sys.stdout = old


@contextmanager
def ssh_config(ssh_user, ssh_private_key):
    """Create temporary ssh config file."""
    try:
        ssh_file = NamedTemporaryFile(delete=False)
        ssh_file.write('Host *\n')
        ssh_file.write('    IdentityFile %s\n' % ssh_private_key)
        ssh_file.write('    User %s' % ssh_user)
        ssh_file.close()
        yield ssh_file.name
    finally:
        with ignored(OSError):
            os.remove(ssh_file.name)