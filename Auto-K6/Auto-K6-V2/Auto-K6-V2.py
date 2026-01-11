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

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich import print as rprint
except ImportError:
    print("[!] Installing graphics library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich import print as rprint

console = Console()

title = "Auto-K6 V2 - LTX74"
if os.name == 'nt':
    os.system(f'title {title}')
else:
    sys.stdout.write(f"\x1b]2;{title}\x07")


os.system('cls' if os.name == 'nt' else 'clear')

LOGO = """[bold magenta]                                                                      
 _______ _______ _______ _______        __  __ ______      ___ ___ ______ 
|   _   |   |   |_     _|       |______|  |/  |    __|    |   |   |__    |
|       |   |   | |   | |   -   |______|     <|  __  |    |   |   |    __|
|___|___|_______| |___| |_______|      |__|\__|______|     \_____/|______|
[/bold magenta]
                                                                    
[bold magenta]Auto-K6 V2 - https://k6.surge.sh[/bold magenta]

[dim]Created by LTX74[/dim]
"""

class K6Manager:
    def __init__(self):
        self.os_name = platform.system().lower()
        self.history_file = "k6_history.json"

    def check_k6(self):
        return shutil.which("k6") is not None

    def install_k6(self):
        console.print(f"\n[!] k6 not detected. Installation for {self.os_name}...", style="bold yellow")
        print()
        try:
            if "windows" in self.os_name:
                # Définition du chemin direct vers l'exécutable Chocolatey
                choco_exe = r"C:\ProgramData\chocolatey\bin\choco.exe"

                # Si choco n'est pas dans le PATH, on tente l'installation via PowerShell
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
                print()
                input("\033[34m Press Enter to restart the script...\033[0m")
                time.sleep(1)
                os.system('cls' if os.name == 'nt' else 'clear')
                python = sys.executable
                os.execl(python, python, *sys.argv)

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

            print()
            console.print("[+] k6 installed successfully!", style="bold green")
            time.sleep(2.5)
            os.system('cls' if os.name == 'nt' else 'clear')
            return True

        except Exception as e:
            console.print(f"[!] Installation error : {e}", style="red")
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
            console.print(f"[!] Error saving history: {e}", style="red")
            
    def show_menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        rprint(LOGO)
        rprint(Panel("[bold green]Welcome to Auto-K6 V2 - Full Version![/bold green]", border_style="green"))

        print()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=10)
        table.add_column("Action", style="white")

        table.add_row("1", "Run a k6 test (URL)")
        table.add_row("2", "View history")
        table.add_row("3", "Reinstall k6")
        table.add_row("4", "Tiktok aro.x.74")
        table.add_row("5", "Check site status")
        table.add_row("6", "Scan Website")
        table.add_row("7", "k6 test on IP address")
        table.add_row("8", "Contact LTX74")
        table.add_row("0", "Quit")

        rprint(table)
        print()
        return Prompt.ask("Choice", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"], default="1")

    def get_config(self):
        rprint("\n[bold yellow]--- URL Test Configuration ---[/bold yellow]")
        print()
        
        method = Prompt.ask("HTTP Method", choices=["GET", "POST", "PUT", "DELETE"], default="GET")
        url = Prompt.ask("Target URL")

        if not re.match(r'^https?://', url):
            rprint("[!] Invalid URL. Must start with http:// or https://", style="red")
            return None
        
        vus = IntPrompt.ask("Number of VUs (Users)", default=3000)
        duration = Prompt.ask("Duration (ex: 30s, 5m)", default="20s")

        body = None
        if method in ["POST", "PUT"]:
            body_input = Prompt.ask("JSON Body (Enter to ignore)", default="")
            if body_input.strip():
                try:
                    json.loads(body_input)
                    body = body_input
                except json.JSONDecodeError:
                    rprint("[!] The body is not a valid JSON.", style="red")
                    return None

        return {"method": method, "url": url, "vus": vus, "duration": duration, "body": body}

    def get_ip_config(self):
        rprint("\n[bold yellow]--- IP Test Configuration ---[/bold yellow]")
        print()
        
        ip_address = Prompt.ask("\033[36mTarget IP Address \033[0m")
        
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            rprint("[!] Invalid IP address.", style="red")
            return None
        
        protocol = Prompt.ask("Protocol", choices=["HTTP", "HTTPS"], default="HTTP").lower()
        default_port = 80 if protocol == "http" else 443
        port = IntPrompt.ask(f"Port ({default_port} by default)", default=default_port)
        
        if not (1 <= port <= 65535):
            rprint("[!] Invalid port. Must be between 1 and 65535.", style="red")
            return None
        
        method = Prompt.ask("HTTP Method", choices=["GET", "POST", "PUT", "DELETE"], default="GET")
        host_header = Prompt.ask("Host Header (optional, ex: example.com)", default="")
        
        vus = IntPrompt.ask("Number of VUs (Users)", default=3000)
        duration = Prompt.ask("Duration (ex: 30s, 5m)", default="20s")

        body = None
        if method in ["POST", "PUT"]:
            body_input = Prompt.ask("JSON Body (Enter to ignore)", default="")
            if body_input.strip():
                try:
                    json.loads(body_input)
                    body = body_input
                except json.JSONDecodeError:
                    rprint("[!] The body is not a valid JSON.", style="red")
                    return None

        return {
            "method": method, 
            "ip": ip_address, 
            "port": port,
            "protocol": protocol,
            "host_header": host_header,
            "vus": vus, 
            "duration": duration, 
            "body": body
        }

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
    let params = {json.dumps(params) if params else '{}'};
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
    let params = {json.dumps(params) if params else '{}'};
    let response = http.{method_lower}('{url}', params);
    sleep(1);
}}
"""
        return script

    def execute_test(self, cfg):
        script_content = self.generate_script(cfg)
        script_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".js") as f:
                f.write(script_content)
                script_path = f.name

            rprint(f"\n[bold green][+] Ready to attack {cfg['url']} ({cfg['method']})...[/bold green]")
            if Confirm.ask("Confirm launch?", default=True):
                try:
                    subprocess.run(f'k6 run "{script_path}"', shell=True, check=True)
                    record = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "url": cfg['url'],
                        "method": cfg['method'],
                        "vus": cfg['vus'],
                        "duration": cfg['duration'],
                        "status": "FINISHED",
                        "type": "URL_TEST"
                    }
                    self.save_history(record)
                    rprint("[bold green][+] Test completed successfully![/bold green]")
                except subprocess.CalledProcessError as e:
                    rprint(f"[bold red][!] Error executing k6:[/bold red]")
                    rprint(f"[red]{e.stderr}[/red]")
                except KeyboardInterrupt:
                    rprint("\n[!] Test stopped by user.")
                except Exception as e:
                    rprint(f"[bold red][!] Unexpected error: {e}[/bold red]")
                    
        except Exception as e:
            rprint(f"[bold red][!] Error preparing test: {e}[/bold red]")
        finally:
            if script_path and os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except Exception as e:
                    rprint(f"[yellow][!] Unable to delete temporary file: {e}[/yellow]")

    def execute_ip_test(self, cfg):
        script_content = self.generate_ip_script(cfg)
        script_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".js") as f:
                f.write(script_content)
                script_path = f.name

            target = f"{cfg['protocol']}://{cfg['ip']}:{cfg['port']}"
            rprint(f"\n[bold green][+] Ready to attack {target} ({cfg['method']})...[/bold green]")
            if Confirm.ask("Confirm launch?", default=True):
                try:
                    subprocess.run(f'k6 run "{script_path}"', shell=True, check=True)
                    record = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "url": target,
                        "method": cfg['method'],
                        "vus": cfg['vus'],
                        "duration": cfg['duration'],
                        "status": "FINISHED",
                        "type": "IP_TEST"
                    }
                    self.save_history(record)
                    rprint("[bold green][+] Test completed successfully![/bold green]")
                    
                except subprocess.CalledProcessError as e:
                    rprint(f"[bold red][!] Error executing k6:[/bold red]")
                    rprint(f"[red]{e.stderr}[/red]")
                except KeyboardInterrupt:
                    rprint("\n[!] Test stopped by user.")
                except Exception as e:
                    rprint(f"[bold red][!] Unexpected error: {e}[/bold red]")
                    
        except Exception as e:
            rprint(f"[bold red][!] Error preparing test: {e}[/bold red]")
        finally:
            if script_path and os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except Exception as e:
                    rprint(f"[yellow][!] Unable to delete temporary file: {e}[/yellow]")

    def show_history(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        rprint(Panel("[bold blue]History[/bold blue]"))
        if not self.history:
            rprint("[yellow]Empty.[/yellow]")
        else:
            table = Table(show_header=True)
            table.add_column("Date")
            table.add_column("Target")
            table.add_column("Method")
            table.add_column("VUs")
            table.add_column("Type")
            for h in self.history:
                test_type = h.get('type', 'URL_TEST')
                table.add_row(h['timestamp'], h['url'], h['method'], str(h['vus']), test_type)
            rprint(table)
        input("\nEnter to continue...")
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')

    def check_site_status(self):
        print()
        print("\033[35m--- Site Status Check ---\033[0m")
        print()
        url = input("\033[36mEnter the site URL to check (ex: https://example.com): \033[0m").strip()
        if not url:
            return
        if not re.match(r'^https?://', url):
            url = 'https://' + url  
        try:
            time.sleep(1)
            print()
            print("\033[94mChecking site status... (10s max)\033[0m")
            print()
            reponse = requests.get(url, timeout=10)
            if reponse.status_code == 200:
                rprint(f"[bold green][+] The site {url} is online![/bold green]")
            else:
                rprint(f"[bold yellow][!] The site {url} responded with status {reponse.status_code}.[/bold yellow]")
        except requests.RequestException as e:
            rprint(f"[bold red][!] The site {url} is offline or inaccessible. Error: {e}[/bold red]")
        input("\nEnter to continue...")
        time.sleep(1)

    def get_ssl_info(self, hostname, port=443):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    issuer = dict(x[0] for x in cert['issuer'])
                    subject = dict(x[0] for x in cert['subject'])
                    return {
                        'issuer': issuer.get('organizationName', 'N/A'),
                        'subject': subject.get('organizationName', 'N/A'),
                        'version': cert['version'],
                        'serial': cert['serialNumber'],
                        'not_before': cert['notBefore'],
                        'not_after': cert['notAfter'],
                        'valid': True
                    }
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def get_dns_info(self, hostname):
        try:
            ip = socket.gethostbyname(hostname)
            return {'ip': ip}
        except Exception as e:
            return {'ip': 'N/A', 'error': str(e)}

    def get_ip_info(self, ip):
        try:
            host_info = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5).json()
            return {
                'hostname': host_info.get("hostname", "N/A"),
                'org': host_info.get("org", "N/A"),
                'city': host_info.get("city", "N/A"),
                'region': host_info.get("region", "N/A"),
                'country': host_info.get("country", "N/A"),
                'location': host_info.get("loc", "N/A")
            }
        except Exception as e:
            return {'error': str(e)}

    def scan_website(self):
        print()
        print("\033[35m--- Website Scan ---\033[0m")
        print()
        url = input("\033[36mEnter the site URL to scan (ex: https://example.com): \033[0m").strip()
        if not url:
            return
        if not re.match(r'^https?://', url):
            url = 'https://' + url
        
        parsed_url = re.match(r'^https?://([^/]+)', url)
        if not parsed_url:
            rprint(f"[bold red][!] Invalid URL: {url}[/bold red]")
            input("\nEnter to continue...")
            return
        hostname = parsed_url.group(1)
        
        print()
        print("\033[94mStarting site scan... (Analysis in progress)\033[0m")
        print()
        
        results = {}
        
        def get_response_info():
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                headers = dict(response.headers)
                technologies = []
                if 'server' in headers:
                    technologies.append(f"Server: {headers['server']}")
                if 'x-powered-by' in headers:
                    technologies.append(f"Powered by: {headers['x-powered-by']}")
                if 'x-generator' in headers:
                    technologies.append(f"Generator: {headers['x-generator']}")
                
                return {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'content_type': headers.get('content-type', 'N/A'),
                    'content_length': headers.get('content-length', len(response.content)),
                    'technologies': technologies,
                    'headers': headers
                }
            except Exception as e:
                return {'error': str(e)}
        
        def get_ip_and_dns():
            dns_info = self.get_dns_info(hostname)
            if 'ip' in dns_info and dns_info['ip'] != 'N/A':
                ip_info = self.get_ip_info(dns_info['ip'])
                return {**dns_info, **ip_info}
            return dns_info
        
        def get_ssl_cert():
            if url.startswith('https://'):
                return self.get_ssl_info(hostname)
            return {'valid': False, 'error': 'Not HTTPS'}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(get_response_info): 'response',
                executor.submit(get_ip_and_dns): 'ip_dns',
                executor.submit(get_ssl_cert): 'ssl'
            }
            
            for future in as_completed(futures):
                result_type = futures[future]
                try:
                    results[result_type] = future.result()
                except Exception as e:
                    results[result_type] = {'error': str(e)}
        
        console.print(f"\n[bold green]--- Scan results for {url} ---[/bold green]\n")
        
        if 'response' in results:
            resp = results['response']
            if 'error' in resp:
                console.print(f"[bold red]Request error: {resp['error']}[/bold red]")
            else:
                console.print(f"[bold cyan]Status:[/bold cyan] {resp['status_code']}")
                console.print(f"[bold cyan]Response time:[/bold cyan] {resp['response_time']} ms")
                console.print(f"[bold cyan]Content type:[/bold cyan] {resp['content_type']}")
                console.print(f"[bold cyan]Content size:[/bold cyan] {resp['content_length']} bytes")
                
                if resp['technologies']:
                    console.print(f"[bold cyan]Detected technologies:[/bold cyan]")
                    for tech in resp['technologies']:
                        console.print(f"  • {tech}")
        
        if 'ip_dns' in results:
            dns = results['ip_dns']
            console.print(f"\n[bold cyan]IP Address:[/bold cyan] {dns.get('ip', 'N/A')}")
            if 'hostname' in dns and dns['hostname'] != 'N/A':
                console.print(f"[bold cyan]Hostname:[/bold cyan] {dns['hostname']}")
            if 'org' in dns and dns['org'] != 'N/A':
                console.print(f"[bold cyan]Provider:[/bold cyan] {dns['org']}")
            if 'city' in dns and dns['city'] != 'N/A':
                location = f"{dns['city']}, {dns.get('region', '')}, {dns.get('country', '')}"
                console.print(f"[bold cyan]Location:[/bold cyan] {location}")
        
        if 'ssl' in results:
            ssl = results['ssl']
            console.print(f"\n[bold cyan]SSL Certificate:[/bold cyan] ", end="")
            if ssl.get('valid', False):
                console.print("[bold green]Valid[/bold green]")
                console.print(f"[bold cyan]Issued by:[/bold cyan] {ssl.get('issuer', 'N/A')}")
                console.print(f"[bold cyan]Issued to:[/bold cyan] {ssl.get('subject', 'N/A')}")
                console.print(f"[bold cyan]Valid until:[/bold cyan] {ssl.get('not_after', 'N/A')}")
            else:
                console.print("[bold red]Invalid or unavailable[/bold red]")
                if 'error' in ssl:
                    console.print(f"[bold red]Error:[/bold red] {ssl['error']}")
        
        input("\nEnter to continue...")
        time.sleep(1)

    def run(self):
        while True:
            if not self.manager.check_k6():
                os.system('cls' if os.name == 'nt' else 'clear')
                print("""
 _______ _______ _______ _______        __  __ ______      ___ ___ ______ 
|   _   |   |   |_     _|       |______|  |/  |    __|    |   |   |__    |
|       |   |   | |   | |   -   |______|     <|  __  |    |   |   |    __|
|___|___|_______| |___| |_______|      |__|\__|______|     \_____/|______|

By LTX
""")
                print()
                if Confirm.ask("k6 missing. Install?", default=True):
                    self.manager.install_k6()
                    if not self.manager.check_k6():
                        sys.exit(1)
                else:
                    sys.exit(0)

            choice = self.show_menu()

            if choice == "1":
                cfg = self.get_config()
                if cfg:
                    self.execute_test(cfg)

            elif choice == "2":
                self.show_history()

            elif choice == "3":
                print()
                rprint(f"\n[bold green][+] Reinstalling k6...[/bold green]")
                time.sleep(1)
                print()
                self.manager.install_k6()

            elif choice == "4":
                time.sleep(1)
                webbrowser.open("https://www.tiktok.com/@aro.x.74")

            elif choice == "5":
                time.sleep(1)
                self.check_site_status()

            elif choice == "6":
                time.sleep(1)
                self.scan_website()

            elif choice == "7":
                cfg = self.get_ip_config()
                if cfg:
                    self.execute_ip_test(cfg)

            elif choice == "8":
                time.sleep(1)
                webbrowser.open("https://t.me/LTX74")

            elif choice == "0":
                os.system('cls' if os.name == 'nt' else 'clear')
                rprint(LOGO)
                time.sleep(1)
                os.system('cls' if os.name == 'nt' else 'clear')
                sys.exit(0)

if __name__ == "__main__":
    try:
        App().run()
    except KeyboardInterrupt:
        rprint("\nStopped.")
        sys.exit(0)

# Made by LTX74
