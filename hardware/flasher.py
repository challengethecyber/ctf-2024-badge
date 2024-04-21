import os
import sys
import re
import hashlib
import subprocess

def genhash(team_num):
	return hashlib.sha1(b"ChallengeTheCyber2024BakerySalt%d" % team_num).hexdigest()

arg = sys.argv[1]
assert arg.startswith("BT")
team_num = int(arg.split("BT")[1].strip())

print("[*] Flashing for team BT%d, key: %s" % (team_num, genhash(team_num)))

print("[*] Finding COM device...")

while True:
	port = os.popen("powershell -c [System.IO.Ports.SerialPort]::getportnames()").read().strip()
	if len(port) == 0:
		continue

	assert len(port.splitlines()) == 1, "Multiple COM devices"
	assert re.fullmatch(r"COM\d+", port)
	break

print(f"[+] Selected: {port}")

print(f"\n[*] Erasing flash ...")

subprocess.run(f'esptool --port {port} --chip esp8266 --baud 460800 erase_flash', shell=True, stderr=sys.stderr, stdout=sys.stdout)

print(f"\n[*] Writing base firmware ...")

subprocess.run(f'esptool --port {port} --chip esp8266 --baud 460800 write_flash --flash_size=detect 0 ESP8266_GENERIC-20240105-v1.22.1.bin', shell=True, stderr=sys.stderr, stdout=sys.stdout)

print(f"\n[*] Uploading badgefs")

#subprocess.run(f'ampy -p {port} mkdir lib', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
#subprocess.run(f'ampy -p {port} mkdir img', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/img img', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/lib lib', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/boot.py boot.py', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")

"""
subprocess.run(f'ampy -p {port} put badgefs/img/chef.fb img/chef.fb', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/img/croissant.fb img/croissant.fb', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/img/croissant_sm.fb img/croissant_sm.fb', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/img/donut.fb img/donut.fb', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/img/donut_sm.fb img/donut_sm.fb', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/img/flag.fb img/flag.fb', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/lib/ubutton.py lib/ubutton.py', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
subprocess.run(f'ampy -p {port} put badgefs/boot.py boot.py', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")
"""

open("config.tmp","w").write('config = {"wifi_ssid": "BakeryIOT_2G", "wifi_pass": "FreshCroissants2024", "score_server": "192.168.76.2", "team_num": "BT%d", "team_key": "%s"}' % (team_num, genhash(team_num)))
subprocess.run(f'ampy -p {port} put config.tmp config.py', shell=True, stderr=sys.stderr, stdout=sys.stdout); print(".")

print("[*] List root:")
subprocess.run(f'ampy -p {port} ls', shell=True, stderr=sys.stderr, stdout=sys.stdout)

print("[*] Read MAC + hard reset")

result = subprocess.run(f'esptool --port {port} --chip esp8266 --baud 460800 --after hard_reset read_mac', shell=True, capture_output=True, text=True)
maccy = result.stdout.split("MAC: ")[1].splitlines()[0]

logline = f"Team=BT{team_num} MAC={maccy}"
print(f"   ==> {logline}")
open("deviceconfigs.txt", "a+").write(logline+"\n")

print(f"[+] Done")