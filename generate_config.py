#!/bin/env python
import docker
from xmlrpc.client import ServerProxy
import configparser
import sys

server = ServerProxy('http://localhost:9001/RPC2')

client = docker.from_env()


def generate_supervisor_config():
    info = client.info()
    services = []
    containers = []
    if info['Swarm']['NodeID'] == "":
        containers = client.containers.list()
    else:
        services = client.services.list()

    for container in containers:
        supervisor_config = ''
        labels = container.attrs['Config']['Labels']
        if 'bugloos.supervisor.program_name' in labels:
            program_name = labels.get('bugloos.supervisor.program_name')
            command = "docker run --rm " + container.attrs.get('Image') + " " + labels.get('bugloos.supervisor.command')
            numprocs = labels.get('bugloos.supervisor.numprocs', '1')
            directory = labels.get('bugloos.supervisor.directory', '/')
            autostart = labels.get('bugloos.supervisor.autostart', 'true')
            autorestart = labels.get('bugloos.supervisor.autorestart', 'true')
            startsecs = labels.get('bugloos.supervisor.startsecs', '1')
            startretries = labels.get('bugloos.supervisor.startretries', '3')
            stdout_logfile = labels.get('bugloos.supervisor.stdout_logfile', 'AUTO')
            stderr_logfile = labels.get('bugloos.supervisor.stderr_logfile', '/dev/fd/1')
            stdout_logfile_maxbytes = labels.get('bugloos.supervisor.stdout_logfile_maxbytes', '0')
            environment = labels.get('bugloos.supervisor.environment', '')

            config = configparser.ConfigParser()
            config[f"""program:{program_name}"""]={
            "command": command,
            "numprocs": numprocs,
            "directory": directory,
            "autostart": autostart,
            "autorestart": autorestart,
            "startsecs": startsecs,
            "startretries": startretries,
            "stdout_logfile": stdout_logfile,
            "stderr_logfile": stderr_logfile,
            "stdout_logfile_maxbytes": stdout_logfile_maxbytes,
            "environment": environment,
            }
            with open(f"""/etc/supervisor.d/{program_name}.ini""", 'w') as f:
                config.write(f)

    for service in services:
        supervisor_config = ''
        labels = service.attrs['Spec']['Labels']
        if 'bugloos.supervisor.program_name' in labels:
            program_name = labels.get('bugloos.supervisor.program_name')
            command = labels.get('bugloos.supervisor.command')
            numprocs = labels.get('bugloos.supervisor.numprocs', '1')
            directory = labels.get('bugloos.supervisor.directory', '/')
            autostart = labels.get('bugloos.supervisor.autostart', 'true')
            autorestart = labels.get('bugloos.supervisor.autorestart', 'true')
            startsecs = labels.get('bugloos.supervisor.startsecs', '1')
            startretries = labels.get('bugloos.supervisor.startretries', '3')
            stdout_logfile = labels.get('bugloos.supervisor.stdout_logfile', '/dev/fd/1')
            stdout_logfile_maxbytes = labels.get('bugloos.supervisor.stdout_logfile_maxbytes', '0')
            stderr_logfile = labels.get('bugloos.supervisor.stderr_logfile', '/dev/fd/2')
            stderr_logfile = labels.get('bugloos.supervisor.stderr_logfile_maxbytes', '0')
            redirect_stderr = labels.get('bugloos.supervisor.redirect_stderr', 'true')
            environment = labels.get('bugloos.supervisor.environment', '')

            config = configparser.ConfigParser()
            config[f"""program:{program_name}"""]={
            "command": command,
            "numprocs": numprocs,
            "directory": directory,
            "autostart": autostart,
            "autorestart": autorestart,
            "startsecs": startsecs,
            "startretries": startretries,
            "stdout_logfile": stdout_logfile,
            "stderr_logfile": stderr_logfile,
            "stdout_logfile_maxbytes": stdout_logfile_maxbytes,
            "environment": environment,
            }
            with open(f"""/etc/supervisor.d/{program_name}.ini""", 'w') as f:
                config.write(f)

    server.supervisor.reloadConfig()
    server.supervisor.addProcessGroup(program_name)
    sys.exit(0)


if __name__ == '__main__':
    try:
        generate_supervisor_config()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
