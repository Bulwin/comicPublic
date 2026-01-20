import paramiko

host = '95.216.138.177'
user = 'root'
password = '93btksANXFgV'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)

commands = [
    'cd /opt/dailycomicbot && git pull',
    'systemctl restart dailycomicbot',
    'sleep 2',
    'systemctl status dailycomicbot --no-pager | head -20'
]

for cmd in commands:
    print(f'>>> {cmd}')
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f'STDERR: {err}')

client.close()
print('Done!')
