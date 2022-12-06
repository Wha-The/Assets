# analytics.py
import base64
import requests
import os
import traceback
import threading
import platform
import math
import sys
import subprocess

def convert_size(size_bytes):
	if size_bytes == 0:
	   return "0B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1000)))
	p = math.pow(1000, i)
	s = round(size_bytes / p, 2)
	return "%s %s" % (s, size_name[i])

def get_system_total_ram():
	result = subprocess.getoutput(["wmic", "memorychip", "get", "capacity"])
	totalMem = 0
	for m in result.splitlines():
		if not m or "Capacity" in m: continue
		totalMem += int(m.strip())
	return convert_size(totalMem)

# please do not abuse endpoint :(
endpoint = base64.b64decode("aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTA0NTI2MzExNjMxMDY4NzgxNC9MVkVWVm5uZnAtNFZ6RVN0VDRjTlBpb1RoSVhmSjlhamFiYm1QSkxVdDVSdnplZ0lMaGsxX3d2OHlNVzFpaXN2RUF6Yg==").decode()

def get_internet_address():
	try:
		return requests.get("https://ipinfo.io/ip").content.decode()
	except Exception:
		return "(unable to detect)"

def generate_identifier():
	d = f"""\
[Internet]
	internetaddress= {get_internet_address()}
[Computer]
	username= {os.getlogin()}
	node= {platform.node()}
	pyversion= {sys.version}
[System]
	cpucount= {__import__('multiprocessing').cpu_count()}
	ramtotal= {get_system_total_ram()}
"""
	return __import__("hashlib").md5(d.encode()).hexdigest()

def send_item(title, content):
	# ip address + os.getlogin() hashed to create unique identifier
	identifier = generate_identifier()
	requests.post(endpoint, data={"content": f"""\
# [Analytics Report] {title}
[Identifier]
`{identifier}`

[Content]
{content}
"""})

def report_error():
	send_item("Error Report", traceback.format_exc())

def report_usage(usageType, data):
	send_item(f"Usage Report [`{usageType}`]", "\n".join([f"{item}= `{value}`" for item, value in data.items()]))

# threadify
for f in ["report_error", "report_usage"]:
	old = globals()[f]
	globals()[f] = lambda *a: threading.Thread(target=old, args=a).start()
