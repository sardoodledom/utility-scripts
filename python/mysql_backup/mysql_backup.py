import argparse
import paramiko
import logging
import os

from datetime import datetime

LOG = logging.getLogger(__name__)
SSH_USER = "centos"


def backup_database(ssh, database, backup_dir):
    """
    Use paramiko to run mysql dump on the remote host

    :param ssh:
    :param database:
    :param backup_dir:
    :return back_path:
    """

    backup_time = datetime.datetime.now().strftime('%m-%d-%Y-%H:%M:%S')
    backup_file_path = '{0}/{1}.sql'.format(backup_dir, backup_time)
    mysqldump_cmd = 'sudo mysqldump {0} > {1}'.format(database,
                                                      backup_file_path)
    try:
        _, stdout, stderr = ssh.exec_command(mysqldump_cmd)
        if stderr is not '':
            LOG.error('stderr is {0}'.format(stderr))
            return False
    except paramiko.ssh_exception.SSHException as e:
        LOG.error('Connection to host failed with error'
                  '{0}'.format(e))

    return backup_file_path


def compress_db_backup(ssh, backup_file_path):
    """
    Compress backup file with remote host's gzip command

    :param ssh:
    :param path:
    :return:
    """
    compress_cmd = 'sudo gzip {0}'.format(backup_file_path)
    compressed_path = '{0}.gz'.format(backup_file_path)
    file_list = []

    try:
        _, stdout, _ = ssh.exec_command(compress_cmd)
        LOG.info('stdout: {0}'.format(stdout.read().decode()))
        file_list = ssh.listdir()
    except paramiko.ssh_exception.SSHException as e:
        LOG.error('Connection to host failed with error'
                  '{0}'.format(e))

    return compressed_path if compressed_path in file_list else None


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

        # We should get an exit status of 1 if the path doesn't exist
        if stderr.channel.recv_exit_status == 1:
            # LOG.error('stderr is {0}'.format(stderr.read().decode()))
            return False
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
    sftp.get(remote_path, local_path)


def main():
    # We're not doing anything here yet
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
        '-v', '--verbose', action='count', default=0,
        help="Increase verbosity (specify multiple times for more)")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose >= 1:
        log_level = logging.DEBUG

    format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, datefmt='%m-%d %H:%M', level=log_level)


if __name__ == '__main__':
    main()
