"""
Auto-K6 V2 - Interface Web Complète
Backend Flask avec exécution réelle de k6
"""

# Made by LTX


from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import subprocess
import json
import tempfile
import os
import sys
import threading
from datetime import datetime
import time
import re
import ipaddress
import requests
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
import shutil
import signal
import traceback

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

HISTORY_FILE = "k6_history.json"
active_tests = {}
test_processes = {}

class K6Manager:
    def __init__(self):
        self.os_name = platform.system().lower()
        self.history_file = HISTORY_FILE

    def check_k6(self):
        """Vérifier si k6 est installé"""
        return shutil.which("k6") is not None

    def install_k6(self):
        """Installer k6"""
        try:
            if "windows" in self.os_name:
                result = subprocess.run(
                    'powershell -Command "if (!(Get-Command choco -ErrorAction SilentlyContinue)) {'
                    'Set-ExecutionPolicy Bypass -Scope Process -Force; '
                    '[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
                    'iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\')) '
                    '}" && choco install k6 -y',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            
            elif "linux" in self.os_name:
                result = subprocess.run(
                    "curl -s https://dl.k6.io/key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/k6-archive-keyring.gpg && "
                    "echo 'deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main' | sudo tee /etc/apt/sources.list.d/k6.list && "
                    "sudo apt-get update && sudo apt-get install -y k6",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            
            elif "darwin" in self.os_name:
                result = subprocess.run("brew install k6", shell=True, capture_output=True, text=True)
                return result.returncode == 0
            
            return False
        except Exception as e:
            print(f"Erreur installation k6: {e}")
            return False

k6_manager = K6Manager()

def load_history():
    """Charger l'historique depuis le fichier"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        return []
    except json.JSONDecodeError as e:
        print(f"Erreur JSON dans l'historique: {e}")
        try:
            os.remove(HISTORY_FILE)
        except:
            pass
        return []
    except Exception as e:
        print(f"Erreur chargement historique: {e}")
        return []

def save_history(test_data):
    """Sauvegarder l'historique dans le fichier"""
    try:
        history = load_history()
        
        history.insert(0, test_data)
        
        if len(history) > 100:
            history = history[:100]

        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Historique sauvegardé ({len(history)} entrées)")
        return True
    except Exception as e:
        print(f"Erreur sauvegarde historique: {e}")
        print(traceback.format_exc())
        return False

def create_k6_script_url(method, url, vus, duration, body=None):
    """Créer un script k6 pour URL"""
    url = url.replace('"', '\\"')
    
    script = f"""import http from 'k6/http';
import {{ sleep }} from 'k6';

export let options = {{
    vus: {vus},
    duration: '{duration}'
}};

export default function () {{
"""
    
    if body and method in ['POST', 'PUT']:
        if isinstance(body, str):
            try:
                json.loads(body)
                body_str = body
            except:
                body_str = json.dumps(body)
        else:
            body_str = json.dumps(body)
        
        script += f"""
    let payload = {body_str};
    let params = {{ headers: {{ 'Content-Type': 'application/json' }} }};
    let res = http.{method.lower()}("{url}", payload, params);
"""
    else:
        script += f"""
    let res = http.{method.lower()}("{url}");
"""
    
    script += """    sleep(1);
}"""
    
    return script

def create_k6_script_ip(method, ip, port, protocol, host_header, vus, duration, body=None):
    """Créer un script k6 pour IP"""
    url = f"{protocol}://{ip}:{port}/"
    
    script = f"""import http from 'k6/http';
import {{ sleep }} from 'k6';

export let options = {{
    vus: {vus},
    duration: '{duration}'
}};

export default function () {{
"""
    
    params = {}
    if host_header:
        params['headers'] = {'Host': host_header}
    
    if body and method in ['POST', 'PUT']:
        if isinstance(body, str):
            try:
                json.loads(body)
                body_str = body
            except:
                body_str = json.dumps(body)
        else:
            body_str = json.dumps(body)
        
        script += f"""
    let payload = {body_str};
    let params = {json.dumps(params) if params else '{{}}'};
    params.headers = params.headers || {{}};
    params.headers['Content-Type'] = 'application/json';
    let res = http.{method.lower()}("{url}", payload, params);
"""
    else:
        if params:
            script += f"""
    let params = {json.dumps(params)};
    let res = http.{method.lower()}("{url}", null, params);
"""
        else:
            script += f"""
    let res = http.{method.lower()}("{url}");
"""
    
    script += """    sleep(1);
}"""
    
    return script

def run_test_generic(test_id, test_type, config):
    """Fonction générique pour exécuter un test k6"""
    try:
        if test_type == 'url':
            script = create_k6_script_url(
                method=config.get('method', 'GET'),
                url=config['url'],
                vus=int(config.get('vus', 10)),
                duration=config.get('duration', '10s'),
                body=config.get('body')
            )
            target_url = config['url']
        else:
            script = create_k6_script_ip(
                method=config.get('method', 'GET'),
                ip=config['ip'],
                port=int(config.get('port', 80)),
                protocol=config.get('protocol', 'http'),
                host_header=config.get('host_header', ''),
                vus=int(config.get('vus', 10)),
                duration=config.get('duration', '10s'),
                body=config.get('body')
            )
            target_url = f"{config.get('protocol', 'http')}://{config['ip']}:{config.get('port', 80)}"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(script)
            script_path = f.name
        
        print(f"Script k6 créé: {script_path}")
        
        start_time = time.time()

        if platform.system() == "Windows":
            process = subprocess.Popen(
                ['k6', 'run', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            process = subprocess.Popen(
                ['k6', 'run', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
        
        test_processes[test_id] = process
        
        stdout, stderr = process.communicate(timeout=300)
        execution_time = time.time() - start_time

        if test_id in test_processes:
            del test_processes[test_id]
        output = stdout
        if stderr:
            output += "\n\nSTDERR:\n" + stderr

        record = {
            'id': test_id,
            'timestamp': datetime.now().isoformat(),
            'type': f'{test_type.upper()}_TEST',
            'url': target_url,
            'method': config.get('method', 'GET'),
            'vus': int(config.get('vus', 10)),
            'duration': config.get('duration', '10s'),
            'execution_time': round(execution_time, 2),
            'status': 'SUCCESS' if process.returncode == 0 else 'FAILED',
            'return_code': process.returncode,
            'output': output[:5000],
            'script': script[:2000]
        }

        save_history(record)
        active_tests[test_id] = {'status': 'completed', 'result': record}
        
        if os.path.exists(script_path):
            os.unlink(script_path)
            
    except subprocess.TimeoutExpired:
        if test_id in test_processes:
            try:
                process = test_processes[test_id]
                if platform.system() == "Windows":
                    process.kill()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except:
                pass
        
        target_url = config.get('url', f"{config.get('protocol', 'http')}://{config.get('ip', '')}:{config.get('port', '')}")
        record = {
            'id': test_id,
            'timestamp': datetime.now().isoformat(),
            'type': f'{test_type.upper()}_TEST',
            'url': target_url,
            'method': config.get('method', 'GET'),
            'vus': int(config.get('vus', 10)),
            'duration': config.get('duration', '10s'),
            'status': 'TIMEOUT',
            'output': 'Test timeout après 5 minutes'
        }
        save_history(record)
        active_tests[test_id] = {'status': 'completed', 'result': record}
        
        if test_id in test_processes:
            del test_processes[test_id]
            
    except Exception as e:
        print(f"Erreur test {test_type}: {e}")
        print(traceback.format_exc())
        if test_id in test_processes:
            del test_processes[test_id]
        active_tests[test_id] = {'status': 'error', 'error': str(e)}

@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')

@app.route('/api/check_k6')
def api_check_k6():
    """API: Vérifier si k6 est installé"""
    installed = k6_manager.check_k6()
    return jsonify({'installed': installed})

@app.route('/api/install_k6', methods=['POST'])
def api_install_k6():
    """API: Installer k6"""
    try:
        success = k6_manager.install_k6()
        return jsonify({'success': success, 'message': 'Installation terminée'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/url', methods=['POST'])
def api_test_url():
    """API: Exécuter un test sur URL"""
    data = request.json
    
    if not data.get('url'):
        return jsonify({'error': 'URL requise'}), 400
    
    url = data['url'].strip()
    if not re.match(r'^https?://', url):
        url = 'https://' + url
    
    test_id = f"url_{int(time.time())}_{os.urandom(4).hex()}"
    
    def run_url_test():
        config = {
            'url': url,
            'method': data.get('method', 'GET'),
            'vus': int(data.get('vus', 10)),
            'duration': data.get('duration', '10s'),
            'body': data.get('body')
        }
        run_test_generic(test_id, 'url', config)
    
    thread = threading.Thread(target=run_url_test)
    thread.daemon = True
    thread.start()
    
    active_tests[test_id] = {'status': 'running'}
    return jsonify({'test_id': test_id, 'status': 'started'})

@app.route('/api/test/ip', methods=['POST'])
def api_test_ip():
    """API: Exécuter un test sur IP"""
    data = request.json
    
    try:
        ip = data.get('ip', '').strip()
        ipaddress.ip_address(ip)
    except:
        return jsonify({'error': 'Adresse IP invalide'}), 400
    
    test_id = f"ip_{int(time.time())}_{os.urandom(4).hex()}"
    
    def run_ip_test():
        config = {
            'ip': ip,
            'port': int(data.get('port', 80)),
            'protocol': data.get('protocol', 'http'),
            'host_header': data.get('host_header', ''),
            'method': data.get('method', 'GET'),
            'vus': int(data.get('vus', 10)),
            'duration': data.get('duration', '10s'),
            'body': data.get('body')
        }
        run_test_generic(test_id, 'ip', config)
    
    thread = threading.Thread(target=run_ip_test)
    thread.daemon = True
    thread.start()
    
    active_tests[test_id] = {'status': 'running'}
    return jsonify({'test_id': test_id, 'status': 'started'})

@app.route('/api/test/stop/<test_id>', methods=['POST'])
def api_stop_test(test_id):
    """API: Arrêter un test en cours"""
    try:
        if test_id in active_tests and active_tests[test_id].get('status') == 'running':
            
            if test_id in test_processes:
                process = test_processes[test_id]
                try:
                    if platform.system() == "Windows":
                        process.terminate()
                        time.sleep(1)
                        if process.poll() is None:
                            process.kill()
                    else:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    
                    process.wait(timeout=5)
                except Exception as e:
                    print(f"Erreur arrêt processus: {e}")
                
                del test_processes[test_id]
            
            active_tests[test_id] = {
                'status': 'stopped',
                'stopped_at': datetime.now().isoformat(),
                'message': 'Test arrêté par l\'utilisateur'
            }
            
            record = {
                'id': test_id,
                'timestamp': datetime.now().isoformat(),
                'type': 'MANUAL_STOP',
                'status': 'STOPPED',
                'output': 'Test arrêté par l\'utilisateur',
                'stopped_manually': True
            }
            save_history(record)
            
            return jsonify({'success': True, 'message': 'Test arrêté'})
        
        return jsonify({'success': False, 'error': 'Test non trouvé ou non en cours'}), 404
        
    except Exception as e:
        print(f"Erreur arrêt test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/status/<test_id>')
def api_test_status(test_id):
    """API: Obtenir le statut d'un test"""
    test_data = active_tests.get(test_id, {'status': 'not_found'})
    return jsonify(test_data)

@app.route('/api/history')
def api_history():
    """API: Obtenir l'historique"""
    try:
        history = load_history()
        return jsonify(history)
    except Exception as e:
        print(f"Erreur chargement historique API: {e}")
        return jsonify([])

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    """API: Effacer l'historique"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return jsonify({'success': True, 'message': 'Historique effacé'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history/<test_id>')
def api_history_test(test_id):
    """API: Obtenir un test spécifique"""
    try:
        history = load_history()
        for test in history:
            if test.get('id') == test_id:
                return jsonify(test)
        return jsonify({'error': 'Test non trouvé'}), 404
    except Exception as e:
        print(f"Erreur recherche test: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/api/check_site', methods=['POST'])
def api_check_site():
    """API: Vérifier un site"""
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL requise'}), 400
    
    if not re.match(r'^https?://', url):
        url = 'https://' + url
    
    try:
        start_time = time.time()
        response = requests.get(
            url, 
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (Auto-K6 V2)'},
            verify=False
        )
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({
            'online': True,
            'url': url,
            'status_code': response.status_code,
            'response_time': response_time,
            'headers': dict(response.headers),
            'content_length': len(response.content)
        })
        
    except requests.RequestException as e:
        return jsonify({
            'online': False,
            'url': url,
            'error': str(e)
        })

@app.route('/api/scan_website', methods=['POST'])
def api_scan_website():
    """API: Scanner un site web"""
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL requise'}), 400
    
    if not re.match(r'^https?://', url):
        url = 'https://' + url
    
    results = {}
    
    def check_response():
        try:
            start_time = time.time()
            response = requests.get(
                url,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Auto-K6 V2)'},
                verify=False
            )
            response_time = round((time.time() - start_time) * 1000, 2)
            
            tech = []
            headers = dict(response.headers)
            
            server = headers.get('server', '')
            if server:
                tech.append(f"Server: {server}")
            
            powered_by = headers.get('x-powered-by', '')
            if powered_by:
                tech.append(f"Powered by: {powered_by}")
            
            generator = headers.get('x-generator', '')
            if generator:
                tech.append(f"Generator: {generator}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': response_time,
                'content_type': headers.get('content-type', 'N/A'),
                'content_length': headers.get('content-length', len(response.content)),
                'technologies': tech
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_dns():
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            ip = socket.gethostbyname(hostname)
            
            try:
                ip_info = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5).json()
                return {
                    'success': True,
                    'ip': ip,
                    'hostname': hostname,
                    'city': ip_info.get('city', 'N/A'),
                    'region': ip_info.get('region', 'N/A'),
                    'country': ip_info.get('country', 'N/A'),
                    'org': ip_info.get('org', 'N/A')
                }
            except:
                return {
                    'success': True,
                    'ip': ip,
                    'hostname': hostname
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_ssl():
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            if parsed.scheme != 'https':
                return {'success': False, 'error': 'Not HTTPS'}
            
            hostname = parsed.hostname
            port = parsed.port or 443
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    issuer = dict(x[0] for x in cert['issuer'])
                    subject = dict(x[0] for x in cert['subject'])
                    
                    return {
                        'success': True,
                        'valid': True,
                        'issuer': issuer.get('organizationName', issuer.get('commonName', 'N/A')),
                        'subject': subject.get('commonName', 'N/A'),
                        'not_before': cert.get('notBefore', 'N/A'),
                        'not_after': cert.get('notAfter', 'N/A')
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            'response': executor.submit(check_response),
            'dns': executor.submit(check_dns),
            'ssl': executor.submit(check_ssl)
        }
        
        for name, future in futures.items():
            try:
                results[name] = future.result(timeout=15)
            except Exception as e:
                results[name] = {'success': False, 'error': str(e)}
    
    return jsonify({
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'results': results
    })

@app.route('/api/system/info')
def api_system_info():
    """API: Informations système"""
    return jsonify({
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'k6_installed': k6_manager.check_k6(),
        'k6_path': shutil.which('k6')
    })

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║               Auto-K6 V2 - Interface Web                 ║
    ║               Version Complète - LTX74                   ║
    ║               http://localhost:5000                      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    if k6_manager.check_k6():
        print("[✓] k6 est installé")
    else:
        print("[!] k6 n'est pas installé")
        print("[!] Utilisez l'interface pour l'installer")
    
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        print(f"[✓] Fichier d'historique créé: {HISTORY_FILE}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

# Made by LTX