import threading
import requests
from queue import Queue

def check_and_install_dependencies():
    try:
        import requests
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(["python", '-m', 'pip', 'install', 'requests'])

def test_proxy(proxy, proxy_type):
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}',
        }
        response = requests.get('https://www.google.com', proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"Proxy {proxy} ({proxy_type}) is working.")
            with open('good_proxies.txt', 'a') as f:
                f.write(proxy + '\n')
        else:
            print(f"Proxy {proxy} ({proxy_type}) DEAD")
    except:
        print(f"Proxy {proxy} ({proxy_type}) DEAD")

def proxy_checker():
    check_and_install_dependencies()

    proxy_type = input("Select a proxy type:\n1. HTTP\n2. SOCKS4\n3. SOCKS5\nEnter your choice (1/2/3): ")
    if proxy_type == '1':
        proxy_type_str = 'HTTP'
    elif proxy_type == '2':
        proxy_type_str = 'SOCKS4'
    elif proxy_type == '3':
        proxy_type_str = 'SOCKS5'
    else:
        print("Invalid choice. Please select a valid option.")
        return

    proxies_file = input("Drag and drop the proxy list file here: ")
    try:
        with open(proxies_file, 'r') as f:
            proxies = [line.strip() for line in f]
    except FileNotFoundError:
        print("Proxy list file not found.")
        return

    def worker():
        while proxies:
            proxy = proxies.pop()
            test_proxy(proxy, proxy_type_str)

    num_threads = 100
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    proxy_checker()
    input("All proxies have been checked. Press Enter to exit...")
