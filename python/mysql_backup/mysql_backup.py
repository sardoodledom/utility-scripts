#!/usr/bin/env python3
import argparse
import paramiko
import logging
import os

from datetime import datetime

LOG = logging.getLogger(__name__)
SSH_USER = "centos"


def backup_database(ssh, database, directory):
    """
    Use paramiko to run mysql dump on the remote host

    :param ssh:
    :param database:
    :param backup_dir:
    :return back_path:
    """

    backup_time = datetime.now().strftime('%m-%d-%Y-%H:%M:%S')
    path = '{0}/{1}.sql'.format(directory, backup_time)
    mysqldump_cmd = "sudo bash -c 'mysqldump {0} > {1}'".format(database,
                                                                path)
    try:
        _, stdout, stderr = ssh.exec_command(mysqldump_cmd)
        exit_status = stdout.channel.recv_exit_status()
        # We should get an exit status of 1 if the path doesn't exist
        if exit_status > 0:
            LOG.error('Command exit status'
                      ' {0} {1}'.format(exit_status, stderr.read().decode()))
            return None
        return path
    except paramiko.ssh_exception.SSHException as e:
        LOG.error('Connection to host failed with error'
                  '{0}'.format(e))


def compress_db_backup(ssh, path):
    """
    Compress backup file with remote host's gzip command

    :param ssh:
    :param path:
    :return:
    """
    compress_cmd = 'sudo gzip {0}'.format(path)
    compressed_path = '{0}.gz'.format(path)
    file_list_output = ''

    try:
        _, stdout, _ = ssh.exec_command(compress_cmd)
        LOG.info('stdout: {0}'.format(stdout.read().decode()))
        _, stdout, _ = ssh.exec_command('ls {0}'.format(compressed_path))
        file_list_output = stdout.read().decode()
        LOG.info('file_list: {0}'.format(file_list_output))
    except paramiko.ssh_exception.SSHException as e:
        LOG.error('Connection to host failed with error'
                  '{0}'.format(e))

    return compressed_path if compressed_path in file_list_output else None


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
    ssh.connect(hostname=hostname, username=username, timeout=180,
                look_for_keys=True)

    return ssh


def create_local_path(path):
    """
    Create local path for backups

    :param path:
    :return:
    """

    if not os.path.exists(path):
        os.makedirs(path)


def create_remote_path(ssh, path):
    """
    Create remote backup path if it doesn't exist

    :param ssh:
    :param path:
    :return:
    """
    create_path_cmd = 'sudo mkdir -p {0}'.format(path)
    try:
        _, stdout, stderr = ssh.exec_command(create_path_cmd)
        exit_status = stdout.channel.recv_exit_status()

        # We should get an exit status of 1 if the path doesn't exist
        if exit_status > 0:
            LOG.error('Command exit status'
                      ' {0} {1}'.format(exit_status, stderr.read().decode()))
            return None
        return path
    except paramiko.ssh_exception.SSHException as e:
        LOG.error('Connection to host failed with error'
                  '{0}'.format(e))


def get_backup_file(ssh, local_path, remote_path):
    """
    Retrieve backup file from MySQL host

    :param ssh:
    :param local_path:
    :param remote_path:
    :return:
    """

    sftp = ssh.open_sftp()
    backup_file = remote_path.split('/')[-1]
    local_path = '/'.join([local_path, backup_file])

    with sftp.open(remote_path, mode='rb') as remote_file:
        contents = remote_file.read()
        with open(local_path, 'wb') as local_file:
            local_file.write(contents)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--local-dir', action='store',
        default='/tmp',
        help="The backup directory on the local host")
    parser.add_argument(
        '--remote-dir', action='store',
        default='/tmp',
        help="The backup directory on the remote database host")
    parser.add_argument(
        '--database', action='store',
        required=True,
        help="The database you want to backup")
    parser.add_argument(
        '--server', action='store',
        required=True,
        help="The database server ip/hostname")
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help="Increase verbosity (specify multiple times for more)")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose >= 1:
        log_level = logging.DEBUG

    format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, datefmt='%m-%d %H:%M', level=log_level)

    ssh = create_connection(args.server, SSH_USER)
    create_local_path(args.local_dir)
    create_remote_path(ssh, args.remote_dir)
    db_backup = backup_database(ssh, args.database, args.remote_dir)

    if db_backup:
        compressed_db_backup = compress_db_backup(ssh, db_backup)
        if compressed_db_backup:
            get_backup_file(ssh, args.local_dir, compressed_db_backup)


if __name__ == '__main__':
    main()
