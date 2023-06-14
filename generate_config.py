#!/bin/env python
import configparser
import sys
import time
import docker
import subprocess

client = docker.from_env()

LAST_UPDATE_FILE = '/var/last_%s_update.txt'


def generate_supervisor_config():
    info = client.info()
    services = []
    if 'Swarm' in info and 'NodeID' in info['Swarm'] and info['Swarm']['NodeID'] != "":
        services = client.services.list()

    for service in services:
        labels = service.attrs['Spec']['Labels']
        if 'bugloos.supervisor.program_name' in labels:
            generate_supervisor_ini(service, labels)


def generate_supervisor_ini(service, labels):
    if service_is_ready(service):
        task = get_service_first_available_task(service)
        program_name = labels.get('bugloos.supervisor.program_name')
        command = "docker exec " + task['Status']['ContainerStatus'][
            'ContainerID'] + " " + labels.get('bugloos.supervisor.command')
        numprocs = labels.get('bugloos.supervisor.numprocs', '1')
        process_name = labels.get('bugloos.supervisor.process_name', '')
        directory = labels.get('bugloos.supervisor.directory', '/')
        autostart = labels.get('bugloos.supervisor.autostart', 'true')
        autorestart = labels.get('bugloos.supervisor.autorestart', 'true')
        startsecs = labels.get('bugloos.supervisor.startsecs', '1')
        startretries = labels.get('bugloos.supervisor.startretries', '3')
        stdout_logfile = labels.get('bugloos.supervisor.stdout_logfile', '/dev/fd/1')
        stdout_logfile_maxbytes = labels.get('bugloos.supervisor.stdout_logfile_maxbytes', '0')
        stderr_logfile = labels.get('bugloos.supervisor.stderr_logfile', '/dev/fd/2')
        stderr_logfile_maxbytes = labels.get('bugloos.supervisor.stderr_logfile_maxbytes', '0')
        redirect_stderr = labels.get('bugloos.supervisor.redirect_stderr', 'true')
        environment = labels.get('bugloos.supervisor.environment', '')
        config = configparser.ConfigParser()
        config[f"""program:{program_name}"""] = {
            "command": command,
            "numprocs": numprocs,
            "process_name": process_name,
            "directory": directory,
            "autostart": autostart,
            "autorestart": autorestart,
            "startsecs": startsecs,
            "startretries": startretries,
            "stdout_logfile": stdout_logfile,
            "stdout_logfile_maxbytes": stdout_logfile_maxbytes,
            "stderr_logfile": stderr_logfile,
            "stderr_logfile_maxbytes": stderr_logfile_maxbytes,
            "redirect_stderr": redirect_stderr,
            "environment": environment,
        }
        filePath = f"""/etc/supervisor.d/{program_name}.ini"""

        with open(filePath, 'w') as f:
            config.write(f)

        subprocess.call(['supervisorctl', 'reread'])
        subprocess.call(['supervisorctl', 'update'])

        return program_name
    return ''


def get_service_first_available_task(service):
    return t[0] if (t := service.tasks(filters={"desired-state": "running"})) else None


def service_is_ready(service):
    task = get_service_first_available_task(service)
    if task and task.get('Status').get('State') == 'running':
        return True
    return False


if __name__ == '__main__':
    try:
        generate_supervisor_config()
        for event in client.events(decode=True, filters={'type': 'service', 'event': 'update'}):
            service_id = event.get('Actor').get('ID')
            service = client.services.get(service_id)
            while not service_is_ready(service):
                print(f'Service {service.name} is updating')
                time.sleep(60)  # Wait for 10 seconds before checking again
            print(f'Service {service.name} is ready')
            generate_supervisor_config()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
