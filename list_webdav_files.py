import paramiko
import os
import xml.etree.ElementTree as ET

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

share_token = "YggdBLfdninEJX9"
url = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{share_token}/2026-03/"

cmd = f'curl -u {share_token}: -s -X PROPFIND --header "Depth: 1" {url}'
stdin, stdout, stderr = client.exec_command(cmd)
xml_output = stdout.read().decode()

if not xml_output:
    print("No output from curl.")
    print("Stderr:", stderr.read().decode())
else:
    # Basic parsing of the DAV XML
    try:
        root = ET.fromstring(xml_output)
        namespaces = {'d': 'DAV:'}
        for resp in root.findall('d:response', namespaces):
            href = resp.find('d:href', namespaces).text
            filename = os.path.basename(href.rstrip('/'))
            if filename:
                print(filename)
    except Exception as e:
        print("Failed to parse XML:", e)
        print(xml_output[:1000])

client.close()
