#!/usr/bin/env python3

import paramiko
import logging

from os import stat
from datetime import datetime

LOG = logging.getLogger(__name__)
SSH_USER = "centos"
BACKUP_DIR = "/tmp/"


def create_connection(hostname, username):
    """
    Create a connection to the remote host

    :param hostname:
    :param username:
    :return:
    """
    LOG.info('Trying to connect')
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username, timeout=180, look_for_keys=True)

    return ssh


def backup_database(ssh, database, BACKUP_DIR):
    """
    Use paramiko to run mysql dump on the remote host

    :param ssh:
    :param database:
    :param BACKUP_DIR:
    :return back_path:
    """

    backup_time = datetime.datetime.now().strftime('%m-%d-%Y-%H:%M:%S')
    backup_path = '{0}/{1}.sql'.format(BACKUP_DIR, backup_time)
    mysqldump_cmd = 'mysqldump {0} > {1}'.format(database, BACKUP_DIR)
    try:
        _, stdout, stderr = ssh.exec_command(mysqldump_cmd)
        if stderr is not '':
            LOG.error('stderr is {0}'.format(stderr))
            return False

    except paramiko.ssh_exception.SSHException as e:
        LOG.error('Connection to host failed with error'
                  '{0}'.format(e))

    return backup_path


def compress_backup(ssh, path):
    """
    Compress backup file with remote host's gzip command

    :param ssh:
    :param path:
    :return:
    """
    compress_cmd = 'gzip {0}'.format(path)
    compressed_path = '{0}.gz'.format(path)
    file_list = []

    try:
        _, stdout, _ = ssh.exec_command(compress_cmd)
        LOG.info('stdout: {0}'.format(stdout))
        file_list = ssh.listdir()
    except paramiko.ssh_exception.SSHException as e:
        LOG.error('Connection to host failed with error'
                  '{0}'.format(e))

    return compressed_path if compressed_path in file_list else None


def get_backup_file(ssh, local_path, remote_path):
    """
    Retrieve backup file from MySQL host

    :param ssh:
    :param local_path:
    :param remote_path:
    :return:
    """

    sftp = ssh.open_sftp()
    sftp.get(remote_path, local_path)
    mode = stat(local_path)

    if stat.S_ISREG(mode):
        return local_path

    return None


def main():

    log_level = logging.INFO
    format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, datefmt='%m-%d %H:%M', level=log_level)


if __name__ == '__main__':
    main()
