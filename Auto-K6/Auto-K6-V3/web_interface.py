"""
Auto-K6 V2 - Version adaptée pour interface web
Conserve 100% de la logique originale
"""
import os
import sys
import subprocess
import platform
import shutil
import json
import tempfile
import time
import re
import ipaddress
from datetime import datetime
import webbrowser
import requests
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

class K6Manager:
    def __init__(self):
        self.os_name = platform.system().lower()
        self.history_file = "k6_history.json"

    def check_k6(self):
        return shutil.which("k6") is not None

    def install_k6(self):
        print(f"\n[!] Installation de k6 pour {self.os_name}...")
        try:
            if "windows" in self.os_name:
                choco_exe = r"C:\ProgramData\chocolatey\bin\choco.exe"
                
                if not shutil.which("choco"):
                    try:
                        subprocess.run(
                            'powershell -NoProfile -ExecutionPolicy Bypass -Command '
                            '"[System.Net.ServicePointManager]::SecurityProtocol = '
                            '[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
                            'iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\'))"',
                            shell=True,
                            check=True
                        )
                    except:
                        pass

                subprocess.run(f'"{choco_exe}" install k6 -y', shell=True, check=True)

            elif "linux" in self.os_name:
                subprocess.run(
                    "sudo rm -f /usr/share/keyrings/k6-archive-keyring.gpg && "
                    "curl -fsSL https://dl.k6.io/key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/k6-archive-keyring.gpg && "
                    "echo 'deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main' | sudo tee /etc/apt/sources.list.d/k6.list > /dev/null && "
                    "sudo apt update && "
                    "sudo apt install -y k6",
                    shell=True,
                    check=True
                )

            elif "darwin" in self.os_name:
                subprocess.run("brew install k6", shell=True, check=True)

            print("[+] k6 installé avec succès!")
            return True

        except Exception as e:
            print(f"[!] Erreur d'installation : {e}")
            return False

class App:
    def __init__(self):
        self.manager = K6Manager()
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.manager.history_file):
            try:
                with open(self.manager.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self, test_data):
        self.history.insert(0, test_data)
        try:
            with open(self.manager.history_file, 'w') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"[!] Erreur sauvegarde historique: {e}")

    def generate_script(self, cfg):
        options_js = f"vus: {cfg['vus']}, duration: '{cfg['duration']}'"
        method_lower = cfg['method'].lower()
        
        params = {}
        if cfg['body']:
            params['body'] = f"JSON.stringify({cfg['body']})"

        script = f"""
import http from 'k6/http';
import {{ sleep }} from 'k6';

export let options = {{
    {options_js}
}};

export default function () {{
    let params = {json.dumps(params) if params else '{{}}'};
    let response = http.{method_lower}('{cfg['url']}', params);
    sleep(1);
}}
"""
        return script

    def generate_ip_script(self, cfg):
        options_js = f"vus: {cfg['vus']}, duration: '{cfg['duration']}'"
        url = f"{cfg['protocol']}://{cfg['ip']}:{cfg['port']}/"
        method_lower = cfg['method'].lower()
        
        params = {}
        if cfg['host_header']:
            params['headers'] = {'Host': cfg['host_header']}
        if cfg['body']:
            params['body'] = f"JSON.stringify({cfg['body']})"

        script = f"""
import http from 'k6/http';
import {{ sleep }} from 'k6';

export let options = {{
    {options_js}
}};

export default function () {{
    let params = {json.dumps(params) if params else '{{}}'};
    let response = http.{method_lower}('{url}', params);
    sleep(1);
}}
"""
        return script