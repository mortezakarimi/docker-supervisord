#!/bin/env python
import docker
import os
import time
import subprocess

client = docker.from_env()

LAST_UPDATE_FILE = '/var/last_%s_update.txt'


def is_service_updated(service_name):
    service = client.services.get(service_name)
    current_update = service.attrs.get('UpdatedAt')
    last_update = get_last_service_update(service_name)
    if current_update and current_update < last_update:
        update_last_service_update(service_name, current_update)
        return True
    return False


def get_last_service_update(service_name):
    file_path = LAST_UPDATE_FILE % service_name
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            return f.read().strip()
    return ''


def update_last_service_update(service_name, timestamp):
    file_path = LAST_UPDATE_FILE % service_name
    with open(file_path, 'w') as f:
        f.write(timestamp)


while True:
    # Check if the service has been updated
    if is_service_updated('my_stack_php'):
        # Reload Supervisor configuration
        subprocess.call(['supervisorctl', 'reread'])
        subprocess.call(['supervisorctl', 'update'])

    time.sleep(60)
