# Standard library imports (always available)
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import re
import sys
import subprocess
import os
import time

# Third-party imports will be handled after dependency installation
requests = None
BeautifulSoup = None
urllib3 = None

# ANSI escape codes for colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    END = '\033[0m'

# List of proxy sites to scrape - Updated with current, active sources
proxy_sites = [
    # Popular proxy list websites (still active)
    "https://www.sslproxies.org/",
    "https://www.us-proxy.org/",
    "https://free-proxy-list.net/",
    "https://www.socks-proxy.net/",
    "https://free-proxy-list.net/anonymous-proxy.html",
    "https://www.hidemy.name/en/proxy-list/",
    
    # ProxyScrape API (reliable service)
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all",
    
    # Active GitHub repositories (regularly updated)
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxy-List/main/proxy.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks4/global/socks4_checked.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks5/global/socks5_checked.txt"
]

# Target URL to ping through proxies
TARGET_URL = "https://duckduckgo.com/"

# Timeout for proxy connections in seconds
PROXY_TIMEOUT = 10

# Thread pool settings
MAX_WORKERS = 500

# Global counters and lists for results (thread-safe access)
good_proxies = []
bad_proxies = []
proxies_to_check = queue.Queue()
total_scraped_proxies = 0

# New global counters for scraping status
scraped_success_count = 0
scraped_fail_count = 0
scraping_in_progress = 0

# Locks for thread-safe updates
good_lock = threading.Lock()
bad_lock = threading.Lock()
count_lock = threading.Lock()
scrape_success_lock = threading.Lock()
scrape_fail_lock = threading.Lock()
scrape_progress_lock = threading.Lock()
# New lock for writing to good_proxies.txt
file_write_lock = threading.Lock()

# Events to signal live update threads to stop
stop_live_update_event = threading.Event()
stop_scraping_update_event = threading.Event()


def clear_screen():
    """
    Clears the terminal screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def install_dependencies():
    """
    Automatically checks for and installs required Python packages using pip.
    Provides concise output and handles all dependencies.
    """
    print(f"{Colors.CYAN}Checking and installing required packages...{Colors.END}")
    
    # Map import names to pip package names
    required_packages = {
        "requests": "requests",
        "bs4": "beautifulsoup4", 
        "urllib3": "urllib3"
    }
    
    packages_to_install = []
    
    # Check which packages are missing
    for import_name, pip_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            packages_to_install.append(pip_name)
    
    if not packages_to_install:
        print(f"{Colors.GREEN}All required dependencies are already installed.{Colors.END}")
        return
    
    # Install missing packages
    print(f"  Installing {len(packages_to_install)} missing package(s)...")
    for package in packages_to_install:
        print(f"  Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            print(f"  {Colors.GREEN}{package} installed successfully.{Colors.END}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Error installing {package}: {e}{Colors.END}")
            print(f"Please install {package} manually using: pip install {package}")
            sys.exit(1)
        except Exception as e:
            print(f"{Colors.RED}An unexpected error occurred during installation of {package}: {e}{Colors.END}")
            sys.exit(1)
    
    print(f"{Colors.GREEN}All dependencies installed successfully!{Colors.END}")
    print(f"{Colors.CYAN}Dependency check and installation complete.{Colors.END}")


def import_dependencies():
    """
    Import the required third-party libraries after ensuring they're installed.
    """
    global requests, BeautifulSoup, urllib3
    
    try:
        import requests
        from bs4 import BeautifulSoup
        import urllib3
        
        # Disable InsecureRequestWarning messages
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    except ImportError as e:
        print(f"{Colors.RED}Failed to import required dependencies: {e}{Colors.END}")
        print(f"{Colors.RED}Please try running the script again or install manually with: pip install requests beautifulsoup4 urllib3{Colors.END}")
        sys.exit(1)


def _scrape_single_site(url):
    """
    Scrapes IP addresses and ports from a given proxy list URL and adds them to a global queue.
    """
    global total_scraped_proxies, scraped_success_count, scraped_fail_count, scraping_in_progress
    
    with scrape_progress_lock:
        scraping_in_progress += 1

    display_url = url.split('//')[-1].split('/')[0]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    proxies_found_on_site = 0
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        found_proxies_regex = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', response.text)
        for ip, port in found_proxies_regex:
            proxies_to_check.put(f"{ip}:{port}")
            with count_lock:
                total_scraped_proxies += 1
            proxies_found_on_site += 1

        if 'free-proxy-list.net' in url or 'us-proxy.org' in url or 'sslproxies.org' in url:
            table = soup.find('table', {'id': 'proxylisttable'})
            if table:
                for row in table.find('tbody').find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) > 1:
                        ip = cells[0].get_text(strip=True)
                        port = cells[1].get_text(strip=True)
                        if ip and port and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) and port.isdigit():
                            proxies_to_check.put(f"{ip}:{port}")
                            with count_lock:
                                total_scraped_proxies += 1
                            proxies_found_on_site += 1
        elif 'proxy-list.download' in url:
            pre_tags_found = False
            for pre_tag in soup.find_all('pre'):
                pre_tags_found = True
                for line in pre_tag.get_text().splitlines():
                    match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', line)
                    if match:
                        ip, port = match.groups()
                        proxies_to_check.put(f"{ip}:{port}")
                        with count_lock:
                            total_scraped_proxies += 1
                        proxies_found_on_site += 1
            
            tables = soup.find_all('table')
            if tables:
                for table in tables:
                    for row in table.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) > 1:
                            ip_candidate = cells[0].get_text(strip=True)
                            port_candidate = cells[1].get_text(strip=True)
                            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_candidate) and port_candidate.isdigit():
                                proxies_to_check.put(f"{ip_candidate}:{port_candidate}")
                                with count_lock:
                                    total_scraped_proxies += 1
                                proxies_found_on_site += 1
        
        if proxies_found_on_site > 0:
            with scrape_success_lock:
                scraped_success_count += 1
        else:
            with scrape_fail_lock:
                scraped_fail_count += 1

    except (requests.exceptions.HTTPError, requests.exceptions.RequestException, AttributeError, Exception):
        with scrape_fail_lock:
            scraped_fail_count += 1
    finally:
        with scrape_progress_lock:
            scraping_in_progress -= 1


def _check_single_proxy():
    """
    Checks if a proxy is working by attempting to make a request to TARGET_URL.
    Pulls proxy addresses from the global proxies_to_check queue.
    If good, writes to good_proxies.txt immediately.
    """
    while True:
        proxy_address = proxies_to_check.get()
        if proxy_address is None:
            proxies_to_check.task_done()
            break

        proxies = {
            'http': f'http://{proxy_address}',
            'https': f'http://{proxy_address}'
        }
        try:
            response = requests.get(TARGET_URL, proxies=proxies, timeout=PROXY_TIMEOUT, verify=False)
            if response.status_code == 200:
                with good_lock:
                    good_proxies.append(proxy_address)
                with file_write_lock:
                    with open("good_proxies.txt", "a") as f:  # Open in append mode
                        f.write(f"{proxy_address}\n")
            else:
                with bad_lock:
                    bad_proxies.append(proxy_address)
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError,
                requests.exceptions.Timeout, requests.exceptions.RequestException):
            with bad_lock:
                bad_proxies.append(proxy_address)
        except Exception:
            with bad_lock:
                bad_proxies.append(proxy_address)
        finally:
            proxies_to_check.task_done()


def format_time(seconds):
    """
    Formats a given number of seconds into H hours, M minutes, S seconds.
    """
    if seconds < 0:
        return "N/A" # Or handle as an error if time goes negative

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    time_str = []
    if hours > 0:
        time_str.append(f"{hours}h")
    if minutes > 0 or hours > 0: # Include minutes if there are hours, or if minutes is the largest unit
        time_str.append(f"{minutes}m")
    time_str.append(f"{seconds}s")
    
    return " ".join(time_str)


def live_proxy_check_display(start_time):
    """
    Displays live progress of proxy checking, including elapsed time and estimated time remaining.
    """
    last_processed_count = 0
    last_time = start_time
    # Simple rate tracking for ETR (proxies per second)
    processed_history = [] 

    while not stop_live_update_event.is_set():
        with good_lock:
            current_good = len(good_proxies)
        with bad_lock:
            current_bad = len(bad_proxies)
        
        processed_count = current_good + current_bad
        remaining_count = proxies_to_check.qsize()

        # Ensure processed_count doesn't exceed total_scraped_proxies
        # This can happen if the queue is still being populated during initial checking
        effective_total = total_scraped_proxies if total_scraped_proxies > 0 else (processed_count + remaining_count)
        if processed_count > effective_total:
            processed_count = effective_total
            
        elapsed_time = time.time() - start_time
        formatted_elapsed_time = format_time(elapsed_time)
        
        etr_string = "Calculating ETR..."
        if elapsed_time > 0 and processed_count > 0:
            current_rate = (processed_count - last_processed_count) / (time.time() - last_time + 0.001) # Avoid division by zero
            if current_rate > 0:
                # Add current rate to history, keep a moving average for stability
                processed_history.append(current_rate)
                if len(processed_history) > 10: # Keep last 10 samples
                    processed_history.pop(0)
                
                avg_rate = sum(processed_history) / len(processed_history)
                
                # Use the effective remaining count, which includes items yet to be put in queue from scraping
                # This is tricky as scraping is asynchronous
                # For a more stable ETR, consider it based only on what's *in the queue*
                # Let's adjust: remaining_count is already the queue size.
                if avg_rate > 0 and remaining_count > 0:
                    estimated_remaining_seconds = remaining_count / avg_rate
                    etr_string = f"ETR: {format_time(estimated_remaining_seconds)}"
                else:
                    etr_string = "ETR: N/A" # Not enough data or no remaining items
            else:
                etr_string = "ETR: N/A (Rate 0)"
        else:
            etr_string = "ETR: N/A" # Not enough data yet

        last_processed_count = processed_count
        last_time = time.time()

        sys.stdout.write(f"\r{Colors.BLUE}Checked: {processed_count}/{effective_total} | Good: {Colors.GREEN}{current_good}{Colors.BLUE} | Bad: {Colors.RED}{current_bad}{Colors.BLUE} | Remaining in Queue: {remaining_count} | Elapsed: {formatted_elapsed_time} | {etr_string}{Colors.END}")
        sys.stdout.flush()
        time.sleep(0.5) # Update less frequently for smoother output

    sys.stdout.write("\r" + " " * 200 + "\r") # Clear the line after stopping
    sys.stdout.flush()


def live_scraping_display(start_time):
    """
    Displays live progress of proxy site scraping, including elapsed time and estimated time remaining.
    """
    total_sites = len(proxy_sites)
    last_processed_sites = 0
    last_time = start_time
    # Simple rate tracking for ETR (sites per second)
    processed_site_history = [] 

    while not stop_scraping_update_event.is_set() or scraping_in_progress > 0:
        with scrape_success_lock:
            current_success = scraped_success_count
        with scrape_fail_lock:
            current_fail = scraped_fail_count
        with scrape_progress_lock:
            in_progress = scraping_in_progress

        processed_sites = current_success + current_fail
        remaining_sites = total_sites - processed_sites
        if remaining_sites < 0: remaining_sites = 0 # Safety check

        elapsed_time = time.time() - start_time
        formatted_elapsed_time = format_time(elapsed_time)

        etr_string = "Calculating ETR..."
        if elapsed_time > 0 and processed_sites > 0:
            current_rate = (processed_sites - last_processed_sites) / (time.time() - last_time + 0.001)
            if current_rate > 0:
                processed_site_history.append(current_rate)
                if len(processed_site_history) > 5: # Keep last 5 samples for scraping (fewer sites)
                    processed_site_history.pop(0)
                
                avg_rate = sum(processed_site_history) / len(processed_site_history)
                
                if avg_rate > 0 and remaining_sites > 0:
                    estimated_remaining_seconds = remaining_sites / avg_rate
                    etr_string = f"ETR: {format_time(estimated_remaining_seconds)}"
                else:
                    etr_string = "ETR: N/A"
            else:
                etr_string = "ETR: N/A (Rate 0)"
        else:
            etr_string = "ETR: N/A"

        last_processed_sites = processed_sites
        last_time = time.time()
        
        sys.stdout.write(f"\r{Colors.BLUE}Scraping Sites: {processed_sites}/{total_sites} | Success: {Colors.GREEN}{current_success}{Colors.BLUE} | Failed: {Colors.RED}{current_fail}{Colors.BLUE} | In Progress: {in_progress} | Elapsed: {formatted_elapsed_time} | {etr_string}{Colors.END}")
        sys.stdout.flush()
        time.sleep(0.5) # Update less frequently for smoother output
    
    sys.stdout.write("\r" + " " * 200 + "\r") # Clear the line after stopping
    sys.stdout.flush()


def perform_scraping_flow():
    """
    Orchestrates the scraping of proxies from all defined sites.
    Populates the global proxies_to_check queue.
    """
    global total_scraped_proxies, scraped_success_count, scraped_fail_count, scraping_in_progress
    total_scraped_proxies = 0
    scraped_success_count = 0
    scraped_fail_count = 0
    scraping_in_progress = 0

    # Clear the queue from previous runs
    while not proxies_to_check.empty():
        try:
            proxies_to_check.get(block=False)
        except queue.Empty:
            pass

    print(f"\n{Colors.CYAN}--- Starting Proxy Scraping ---{Colors.END}")
    print(f"{Colors.BLUE}Scanning {len(proxy_sites)} proxy sources for potential proxies...{Colors.END}")
    
    start_time = time.time() # Record start time for scraping

    stop_scraping_update_event.clear()
    scraping_update_thread = threading.Thread(target=live_scraping_display, args=(start_time,)) # Pass start_time
    scraping_update_thread.start()

    with ThreadPoolExecutor(max_workers=min(len(proxy_sites), 20)) as executor: # Limit workers for scraping to avoid overwhelming
        futures = [executor.submit(_scrape_single_site, site) for site in proxy_sites]
        # Wait for all scraping tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                # print(f'{Colors.RED}Scraping worker generated an exception: {exc}{Colors.END}')
                pass # Suppress individual scraping errors from cluttering output
    
    stop_scraping_update_event.set()
    scraping_update_thread.join()

    end_time = time.time() # Record end time for scraping
    elapsed_time = end_time - start_time
    formatted_elapsed_time = format_time(elapsed_time)

    print(f"\n{Colors.CYAN}Scraping complete. Found {total_scraped_proxies} potential proxies. (Elapsed Time: {formatted_elapsed_time}){Colors.END}")
    print(f"Sites Scraped Successfully: {Colors.GREEN}{scraped_success_count}{Colors.END}")
    print(f"Sites Failed to Scrape: {Colors.RED}{scraped_fail_count}{Colors.END}")


def perform_checking_flow():
    """
    Orchestrates the checking of proxies currently in the proxies_to_check queue.
    """
    global good_proxies, bad_proxies
    good_proxies = []
    bad_proxies = []

    # Clear the good_proxies.txt file at the start of a new check
    try:
        with open("good_proxies.txt", "w") as f:
            f.write("")
    except IOError as e:
        print(f"{Colors.RED}Error clearing good_proxies.txt: {e}{Colors.END}")

    if proxies_to_check.empty():
        print(f"{Colors.YELLOW}No proxies in the queue to check. Scraping might have failed or found no proxies.{Colors.END}")
        return

    print(f"\n{Colors.CYAN}--- Starting Proxy Check with {MAX_WORKERS} concurrent threads ---{Colors.END}")
    print(f"{Colors.BLUE}Attempting to connect to {TARGET_URL} through each proxy...{Colors.END}")
    
    start_time = time.time() # Record start time for checking

    stop_live_update_event.clear()
    live_update_thread = threading.Thread(target=live_proxy_check_display, args=(start_time,)) # Pass start_time
    live_update_thread.start()

    # Add None sentinels to signal workers to stop when the queue is empty
    # This must be done *after* all scraping is complete, and total_scraped_proxies is final
    # The check for `proxies_to_check.empty()` above handles the case where scraping yielded nothing.
    # If there are proxies, the workers will consume them.
    # The `proxies_to_check.join()` will ensure all *added* items are processed.
    # The `None` sentinels are primarily for worker threads to exit cleanly once `proxies_to_check.join()` is done.
    for _ in range(MAX_WORKERS):
        proxies_to_check.put(None)


    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(_check_single_proxy) for _ in range(MAX_WORKERS)]
        
        # Wait for all proxies in the queue to be processed
        proxies_to_check.join() # This waits for all items *currently in the queue* to be processed.

        stop_live_update_event.set()
        live_update_thread.join()

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                # print(f'{Colors.RED}Worker thread generated an exception: {exc}{Colors.END}')
                pass # Suppress individual checking errors from cluttering output

    sys.stdout.write(f"\r{Colors.BLUE}Checked: {len(good_proxies) + len(bad_proxies)}/{total_scraped_proxies} | Good: {Colors.GREEN}{len(good_proxies)}{Colors.BLUE} | Bad: {Colors.RED}{len(bad_proxies)}{Colors.BLUE} | Remaining in Queue: 0{Colors.END}\n")
    sys.stdout.flush()

    end_time = time.time() # Record end time for checking
    elapsed_time = end_time - start_time
    formatted_elapsed_time = format_time(elapsed_time)

    print(f"\n{Colors.CYAN}--- Proxy Check Complete (Elapsed Time: {formatted_elapsed_time})---{Colors.END}")
    print(f"Total proxies processed: {len(good_proxies) + len(bad_proxies)}")
    print(f"Good proxies found: {Colors.GREEN}{len(good_proxies)}{Colors.END}")
    print(f"Bad proxies found: {Colors.RED}{len(bad_proxies)}{Colors.END}")

    try:
        with open("bad_proxies.txt", "w") as f:
            for proxy in bad_proxies:
                f.write(f"{proxy}\n")
        print(f"{Colors.RED}Bad proxies saved to bad_proxies.txt{Colors.END}")
    except IOError as e:
        print(f"{Colors.RED}Error saving bad_proxies.txt: {e}{Colors.END}")


if __name__ == "__main__":
    install_dependencies()
    import_dependencies()
    clear_screen()
    print(f"{Colors.CYAN}Starting automatic proxy scraping and checking process...{Colors.END}")
    perform_scraping_flow()
    perform_checking_flow()
    print(f"\n{Colors.CYAN}Process completed. Check 'good_proxies.txt' for working proxies and 'bad_proxies.txt' for non-working ones.{Colors.END}")