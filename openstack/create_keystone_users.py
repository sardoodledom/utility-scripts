#!/usr/bin/env python
import logging
import os
import random
import re
import string
from keystoneclient.auth.identity import v2
from keystoneclient import session
from keystoneclient.v2_0 import client

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
LOG = logging.getLogger(__name__)
LOG.setLevel('INFO')

KEYSTONE_USERS = {
    'admin_user': {
        'roles': ['admin', '_member_'],
        'tenants': ['tenant_1', 'tenant_2', 'tenant_3']
    },
    'user_1': {
        'roles': ['_member_'],
        'tenants': ['tenant_1']
    },
    'user_2': {
        'roles': ['_member_'],
        'tenants': ['tenant_2']
    },
    'user_3': {
        'roles': ['_member_'],
        'tenants': ['tenant_4']
    },
    'user_4': {
        'roles': ['_member_'],
        'tenants': ['tenant_4']
    }
}


def create_tenant(client, tenant_name):
    try:
        tenant = None
        tenant_list = client.tenants.list()
        for tenant_class in tenant_list:
            if tenant_name == tenant_class.name:
                LOG.info('Found tenant {0}'.format(tenant_class.name))
                tenant = tenant_class
        if not tenant:
            LOG.info('Created tenant {0}'.format(tenant_class.name))
            tenant = client.tenants.create(tenant_name, enabled=True)
        return tenant
    except Exception as e:
        LOG.error('Tenant creation failed {0}'.format(e))


def create_user(client, tenant, username):
    try:
        user = None
        user_list = client.users.list()
        for user_class in user_list:
            if username == user_class.name:
                user = user_class
        if not user:
            user = client.users.create(name=username, password=None,
                                       tenant_id=tenant.id)
        return user
    except Exception as e:
        LOG.error('User creation failed {0}'.format(e))


def add_roles(client, user, tenant, role_list):
    user_roles = client.roles.roles_for_user(user, tenant)
    for role_name in role_list:
        LOG.info('role_name is {0}'.format(role_name))
        try:
            role = client.roles.find(name=role_name)
            if role not in user_roles:
                LOG.info('Adding user {0} to role {1} '
                         'in tenant is {2}'.format(user.name, role.name,
                                                   tenant.name))
                client.roles.add_user_role(user, role, tenant)
            else:
                LOG.info('User {0} already has role {1} '
                         'in tenant {1}'.format(user.name, role.name,
                                                tenant.name))
        except Exception as e:
            LOG.error('Role add failed {0}'.format(e))


def main():
    creds = {}
    creds['auth_url'] = os.environ['OS_AUTH_URL']
    creds['username'] = os.environ['OS_USERNAME']
    creds['password'] = os.environ['OS_PASSWORD']
    creds['tenant_name'] = os.environ['OS_TENANT_NAME']
    creds['insecure'] = True

    auth = v2.Password(auth_url=os.environ['OS_AUTH_URL'],
                       username=os.environ['OS_USERNAME'],
                       password=os.environ['OS_PASSWORD'],
                       tenant_name=os.environ['OS_TENANT_NAME'])
    sess = session.Session(auth=auth)
    keystone = client.Client(session=sess)
    for k, v in KEYSTONE_USERS.items():
        username = k
        roles = v.get('roles')
        tenants = v.get('tenants')
        for tenant_name in tenants:
            LOG.info('username {0} tenant {1} '
                     'role_list {2}'.format(username, tenant_name, roles))
            tenant = create_tenant(keystone, tenant_name)
            user = create_user(keystone, tenant, username)
            add_roles(keystone, user, tenant, roles)

if __name__ == '__main__':
    main()
