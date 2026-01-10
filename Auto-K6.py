import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import webbrowser

title = "Auto-K6 - LTX74"
if os.name == 'nt':
    os.system(f'title {title}')
else:
    sys.stdout.write(f"\x1b]2;{title}\x07")

logo = """\033[34m
  /$$$$$$              /$$                       /$$   /$$  /$$$$$$ 
 /$$__  $$            | $$                      | $$  /$$/ /$$__  $$
| $$  \ $$ /$$   /$$ /$$$$$$    /$$$$$$         | $$ /$$/ | $$  \__/
| $$$$$$$$| $$  | $$|_  $$_/   /$$__  $$ /$$$$$$| $$$$$/  | $$$$$$$ 
| $$__  $$| $$  | $$  | $$    | $$  \ $$|______/| $$  $$  | $$__  $$
| $$  | $$| $$  | $$  | $$ /$$| $$  | $$        | $$\  $$ | $$  \ $$
| $$  | $$|  $$$$$$/  |  $$$$/|  $$$$$$/        | $$ \  $$|  $$$$$$/
|__/  |__/ \______/    \___/   \______/         |__/  \__/ \______/                                       
                                                                    
            Made by LTX74 - https://auto-k6.surge.sh

\033[34m---------------------------------------------------------------------------\033[0m
\033[31m| This is Auto-K6, a load testing tool.\033[0m
\033[33m| For more information, visit : https://auto-k6.surge.sh\033[0m
\033[34m---------------------------------------------------------------------------\033[0m
"""

os.system('cls' if os.name == 'nt' else 'clear')

time.sleep(1)
webbrowser.open("https://auto-k6.surge.sh")

time.sleep(2)
print(logo)

time.sleep(1)

def run(cmd, admin=False):
    print(f"\033[32m[+] {cmd}\033[0m")
    subprocess.run(cmd, shell=True, check=False)

def k6_installed():
    return shutil.which("k6") is not None

def install_k6():
    os_name = platform.system().lower()

    print("\033[31m[*] k6 not detected!\033[0m")
    print()

    if os_name == "windows":
        print()
        print("\033[33m[!] Please install chocolatey then k6 manually.\033[0m")
        print()
        input("\033[34m Press Enter to restart the script...\033[0m")
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')
        python = sys.executable
        os.execl(python, python, *sys.argv)

    elif os_name == "linux":
        print()
        print("\033[33m[!] Please install chocolatey then k6 manually.\033[0m")
        print()
        input("\033[34m Press Enter to restart the script...\033[0m")
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')
        python = sys.executable
        os.execl(python, python, *sys.argv)

    elif os_name == "darwin":
        print()
        print("\033[33m[!] Please install chocolatey then k6 manually.\033[0m")
        print()
        input("\033[34m Press Enter to restart the script...\033[0m")
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')
        python = sys.executable
        os.execl(python, python, *sys.argv)

    else:
        print("\033[31m[!] Unsupported OS\033[0m")
        sys.exit(1)

def generate_k6_script(url):
    return f"""
import http from 'k6/http';
import {{ sleep }} from 'k6';

export default function () {{
    http.post('{url}');
    sleep(1);
}}
"""

def main():
    if not k6_installed():
        install_k6()

    if not k6_installed():
        print("\033[31m[!] k6 still not installed.\033[0m")
        sys.exit(1)

    print("\033[32m[+] k6 detected\033[0m")
    print()

    url = input("\033[34mTarget URL (ex: https://example.com) : \033[0m").strip()
    vus = input("\033[34mNumber of VUs (Max = 6500) : \033[0m").strip()
    duration = input("\033[34mDuration ex 1s, 5m, 10h, 7d (Max = 2m) : \033[0m").strip()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".js") as f:
        f.write(generate_k6_script(url).encode())
        script_path = f.name

    def vus_max():
        try:
            return int(vus) <= 6500
        except ValueError:
            return False
    if not vus_max():
        time.sleep(2)
        print()
        print("\033[31m[!] The maximum number of VUs for Auto-K6 is 6500.\033[0m")
        time.sleep(3)
        print()
        print("\033[34mRestarting script...\033[0m")
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def duree_max():
        if duration.endswith('s'):
            try:
                return int(duration[:-1]) <= 120
            except ValueError:
                return False
        elif duration.endswith('m'):
            try:
                return int(duration[:-1]) <= 2
            except ValueError:
                return False
        return False
    if not duree_max():
        time.sleep(2)
        print()
        print("\033[31m[!] The maximum duration for Auto-K6 is 2 minutes.\033[0m")
        time.sleep(3)
        print()
        print("\033[34mRestarting script...\033[0m")
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')
        python = sys.executable
        os.execl(python, python, *sys.argv)


    print()
    print("\033[32m[+] Starting k6 test...\n\033[0m")

    time.sleep(2)

    run(f'k6 run --vus {vus} --duration {duration} "{script_path}"')

    time.sleep(2)
    print()
    input("\33[32mPress Enter to restart the script...\033[0m")
    time.sleep(1)
    os.system('cls' if os.name == 'nt' else 'clear')
    python = sys.executable
    os.execl(python, python, *sys.argv)

if __name__ == "__main__":

    main()
