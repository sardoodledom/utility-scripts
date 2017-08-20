#!/usr/bin/env python3

import paramiko
from datetime import datetime

SSH_USER="centos"
BACKUP_PATH="/tmp/"

def create_connection(hostname, username):
    """
    Create a connection to the remote host
    
    :param hostname: 
    :param username: 
    :return: 
    """
    logger.info('Trying to connect')
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username, timeout=180, look_for_keys=True)

    return ssh

def backup_database(ssh, database, BACKUP_PATH):
    """
    Use paramiko to run mysql dump on the remote host
    
    :param ssh: 
    :param database: 
    :param BACKUP_PATH: 
    :return: 
    """

    backup_time = datetime.datetime.now().strftime('%m-%d-%Y-%H:%M:%S')
    BACKUP_PATH = '{0}/{1}.sql'.format(BACKUP_PATH, backup_time)
    mysqldump_cmd = "mysqldump {0} > {1}".format(database, BACKUP_PATH)
    try:
        _, stdout, stderr = ssh.exec_command(mysqldump_cmd)
    except SSHException as e:
        logger.error('Connection to MySQL host failed with error'
                     '{0}'.format(e))

    return BACKUP_PATH

