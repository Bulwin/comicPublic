import paramiko
import sys

# Устанавливаем кодировку для вывода
sys.stdout.reconfigure(encoding='utf-8')

host = '95.216.138.177'
user = 'root'
password = '93btksANXFgV'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)

# Посмотреть свежие логи
cmd = 'journalctl -u dailycomicbot -n 30 --no-pager'
print(f'>>> {cmd}')
stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)
err = stderr.read().decode('utf-8', errors='ignore')
if err:
    print(f'STDERR: {err}')

client.close()
