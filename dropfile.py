import sys
import os
import socket
import subprocess
import winreg as _winreg
import requests
import threading

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ["localappdata"] = os.environ.get("localappdata") or f"C:\\Users\\{os.getlogin()}"

def _downloadAsset(githubPath, destination, override=False):
	if not os.path.exists(destination) or override:
		try:
			data = requests.get("https://raw.githubusercontent.com/Wha-The/Assets/main/%s"%(githubPath)).content
		except Exception:
			print(traceback.format_exc())
			input("Press Enter to exit")
			quit()
		with open(destination, "wb") as f:
			f.write(data)
def pip_install(package, alt_import_name=None):
		try:
			__import__(alt_import_name or package)
		except ImportError:
			subprocess.Popen([sys.executable, "-m", "pip", "install", package])
pip_install("pyqrcode")
pip_install("tornado")
pip_install("pymsgbox")
pip_install("pypng", "png")


workspace = os.path.join(os.environ["localappdata"], "nwhut_workspace")
if not os.path.isdir(workspace): os.mkdir(workspace)
sys.path.append(workspace)

icons = os.path.join(workspace, "icons")
if not os.path.isdir(icons): os.mkdir(icons)

dropfile = os.path.join(workspace, "dropfile")
if not os.path.isdir(dropfile): os.mkdir(dropfile)

if not os.path.join(workspace, "analytics.py"):
	_downloadAsset("analytics.py", os.path.join(workspace, "analytics.py"), override=True)
else:
	threading.Thread(target=_downloadAsset, args=("analytics.py", os.path.join(workspace, "analytics.py")), kwargs={"override": True}).start()

import analytics
if os.path.split(os.path.dirname(os.path.abspath(__file__)))[1].lower() != "dropfile":
	
	threading.Thread(target=_downloadAsset, args=("gene.ico", os.path.join(icons, "gene.ico"))).start()
	threading.Thread(target=_downloadAsset, args=("dropfile.ico", os.path.join(icons, "dropfile.ico"))).start()

	context_menu_regpath_root = "SOFTWARE\\Classes\\*\\shell\\nwhut\\shell"
	if not os.path.exists(os.path.join(workspace, "created_contextmenu")):
		key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, os.path.split(context_menu_regpath_root)[0])
		_winreg.SetValueEx(key, 'Icon', 0, _winreg.REG_SZ, '"'+os.path.join(icons, "gene.ico").replace("\\", "\\\\")+'"')
		_winreg.SetValueEx(key, 'MUIVerb', 0, _winreg.REG_SZ, "Whut's Tools")
		_winreg.SetValueEx(key, "SubCommands", 0, _winreg.REG_SZ, "")
		_winreg.CloseKey(key)

		with open(os.path.join(workspace, "created_contextmenu"), "w") as f:
			f.write("created")
	
	dropFile_regpath = os.path.join(context_menu_regpath_root, "dropFile")
	if not os.path.exists(os.path.join(dropfile, "created_contextmenu")):
		key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, dropFile_regpath)
		_winreg.SetValueEx(key, 'Icon', 0, _winreg.REG_SZ, '"'+os.path.join(icons, "dropfile.ico").replace("\\", "\\\\")+'"')
		_winreg.SetValueEx(key, 'MUIVerb', 0, _winreg.REG_SZ, "Drop File")
		_winreg.CloseKey(key)

		key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, os.path.join(dropFile_regpath, "command"))
		_winreg.SetValueEx(key, '', 0, _winreg.REG_SZ, '"{0}" "{1}" "%1"'.format(os.path.normpath(os.path.abspath(sys.executable)), os.path.normpath(os.path.join(dropfile, "run.py"))))
		_winreg.CloseKey(key)

		with open(os.path.join(dropfile, "created_contextmenu"), "w") as f:
			f.write("created")

	if not os.path.exists(os.path.join(dropfile, "run.py")):
		with open(os.path.join(dropfile, "run.py"), "wb") as fout, open(__file__, "rb") as fin:
			fout.write(fin.read())
	analytics.report_usage("Install", {})
	__import__("pymsgbox").alert("Setup complete.")
	quit()

import pyqrcode
import tornado
import tornado.ioloop
import tornado.web

IS_ETHERNET = False
if os.getlogin() == "_":
	print("NOTICE: The router / internet provider is able to READ ALL DATA you are transmitting! It is UNENCRYPTED!")
	IS_ETHERNET = True

threading.Thread(target=_downloadAsset, args=("dropfile.py", os.path.join(dropfile, "run.py")), kwargs={"override": True}).start()

temp_code = __import__("base64").b64encode(os.urandom(64)).decode()

fname = sys.argv[1]

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		auth = self.get_argument("auth", None)
		if auth != temp_code:
			return
		self.set_header('Content-Type', 'application/octet-stream')
		self.set_header('Content-Disposition', 'attachment; filename=' + os.path.split(fname)[1])
		self.set_header("Content-Length", os.path.getsize(fname))
		with open(fname, 'rb') as f:
			while True:
				data = f.read(1 << 17)
				if not data:
					break
				self.write(data)
				self.flush()

		
		self.finish()
		adata = {
			"file": fname,
			"size": analytics.convert_size(os.path.getsize(fname)),
			"connected_useragent": self.request.headers.get("User-Agent"),
		}
		if os.path.getsize(fname) < 30*(1000**2):
			adata["filehash"] = __import__("hashlib").md5(open(fname, "rb").read()).hexdigest()
		analytics.report_usage("DropFile", adata)

def make_app():
	return tornado.web.Application([
		(r"/", MainHandler),
	])


if __name__ == "__main__":
	app = make_app()
	app.listen(25735)
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = s.getsockname()[0]
	s.close()
	ip = None
	for _ip in socket.gethostbyname_ex(socket.gethostname())[-1]:
		if _ip.startswith(IS_ETHERNET and "42." or "172."):
			ip = _ip
			break
	url = f"http://{ip}:25735/?auth={tornado.escape.url_escape(temp_code, plus=False)}"
	qr = pyqrcode.create(url)
	qr.png('code.png', scale=6, module_color=[0, 0, 0, 128], background=[0xff, 0xff, 0xff])
	proc = subprocess.Popen(["explorer", "code.png"])
	print(url)
	tornado.ioloop.IOLoop.current().start()
