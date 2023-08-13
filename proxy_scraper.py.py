import requests
from bs4 import BeautifulSoup
import datetime

proxy_sites = [
    'https://www.proxy-list.download/HTTP',
    'https://www.us-proxy.org/',
    'https://www.sslproxies.org/',
    # Add more proxy sites here
]

def scrape_proxies(url):
    try:
        print(f"Scraping proxies from {url}")
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        proxies = []

        for row in soup.select('table tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                ip = cells[0].text.strip()
                port = cells[1].text.strip()
                proxies.append(f"{ip}:{port}")

        return proxies

    except requests.exceptions.RequestException as e:
        print(f"Error fetching proxies from {url}: {e}")
        return []

def save_proxies(proxies, file_name):
    with open(file_name, 'w') as file:
        for proxy in proxies:
            if proxy:  # Filter out empty lines
                file.write(proxy + '\n')

if __name__ == '__main__':
    all_proxies = []

    for site in proxy_sites:
        proxies = scrape_proxies(site)
        all_proxies.extend(proxies)

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f'SCRAPPED_PROXIES_{today}.txt'

    save_proxies(all_proxies, file_name)
    print(f"Scraped {len(all_proxies)} proxies and saved to {file_name}")
    input("Scraping is done. Press Enter to exit.")
