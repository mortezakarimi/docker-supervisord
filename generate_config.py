#!/bin/env python
import docker
from xmlrpc.client import ServerProxy, Fault
import os
import configparser
import sys
import time

server = ServerProxy('http://localhost:9001/RPC2')

client = docker.from_env()


def generate_supervisor_config():
    info = client.info()
    services = []
    if info['Swarm']['NodeID'] != "":
        services = client.services.list()

    for service in services:
        labels = service.attrs['Spec']['Labels']
        if 'bugloos.supervisor.program_name' in labels:
            program_name = generate_supervisor_ini(service, labels)


def generate_supervisor_ini(service, labels):
    program_name = labels.get('bugloos.supervisor.program_name')
    command = "sh -c 'docker exec $(docker ps -q -f name=" + service.attrs['Spec']['Name'] + " -f health=healthy) " + labels.get('bugloos.supervisor.command')+"'"
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
    if os.path.exists(filePath):
        os.unlink(filePath)

    with open(filePath, 'w') as f:
        config.write(f)

    server.supervisor.reloadConfig()
    try:
        server.supervisor.addProcessGroup(program_name)
    except Fault as e:
        print(e.faultString)
        server.supervisor.restart()
    return program_name


def is_service_ready(service):
    """
    Checks if a service is ready by verifying that all tasks are running and
    healthy.
    """
    tasks = service.tasks()
    for task in tasks:
        if task.get('Status').get('State') != 'running':
            return False
    return True


if __name__ == '__main__':
    try:
        generate_supervisor_config()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
