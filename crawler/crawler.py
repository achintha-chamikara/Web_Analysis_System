import requests
from urllib.parse import urljoin, urlparse
import time
import json
from datetime import datetime
from colorama import Fore, Style, init
from bs4 import BeautifulSoup

init(autoreset=True)


class WebsiteCrawler:
    def __init__(self, base_url, max_pages=50):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.visited = set()
        self.pages_data = []

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return (
            parsed.scheme in ["http", "https"]
            and parsed.netloc == self.domain
            and bool(parsed.netloc)
        )

    def get_page_info(self, url):
        try:
            start_time = time.time()

            response = requests.get(
                url,
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            response.raise_for_status()

            load_time = round(time.time() - start_time, 2)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract internal links
            links = []
            for a in soup.find_all("a", href=True):
                full_url = urljoin(url, a["href"])
                if self.is_valid_url(full_url):
                    links.append(full_url)

            # Extract images
            images = []
            for img in soup.find_all("img", src=True):
                full_img = urljoin(url, img["src"])
                images.append(full_img)

            # Extract meta description
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_desc = meta_tag.get("content", "")

            title = "No Title"
            if soup.title and soup.title.string:
                title = soup.title.string.strip()

            page_info = {
                "url": url,
                "status_code": response.status_code,
                "title": title,
                "meta_description": meta_desc,
                "load_time_seconds": load_time,
                "word_count": len(soup.get_text(" ", strip=True).split()),
                "image_count": len(images),
                "internal_links": list(set(links)),
                "internal_links_count": len(set(links)),
                "h1_tags": [h.get_text(strip=True) for h in soup.find_all("h1")],
                "h2_tags": [h.get_text(strip=True) for h in soup.find_all("h2")],
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            return page_info, list(set(links))

        except requests.exceptions.Timeout:
            print(Fore.RED + f"  [TIMEOUT] Could not fetch {url}")
            return None, []

        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"  [REQUEST ERROR] Could not crawl {url} → {e}")
            return None, []

        except Exception as e:
            print(Fore.RED + f"  [ERROR] Could not crawl {url} → {e}")
            return None, []

    def crawl(self):
        print(Fore.CYAN + f"\n{'=' * 55}")
        print(Fore.CYAN + "  Website Analysis System - Crawler Engine")
        print(Fore.CYAN + f"{'=' * 55}")
        print(Fore.YELLOW + f"  Target   : {self.base_url}")
        print(Fore.YELLOW + f"  Max Pages: {self.max_pages}")
        print(Fore.CYAN + f"{'=' * 55}\n")

        queue = [self.base_url]

        while queue and len(self.visited) < self.max_pages:
            url = queue.pop(0)

            if url in self.visited:
                continue

            self.visited.add(url)
            print(
                Fore.GREEN
                + f"  [Crawling {len(self.visited)}/{self.max_pages}] "
                + Style.RESET_ALL
                + url
            )

            page_info, links = self.get_page_info(url)

            if page_info:
                self.pages_data.append(page_info)

                for link in links:
                    if link not in self.visited and link not in queue:
                        queue.append(link)

            time.sleep(0.5)  # polite crawling

        print(Fore.CYAN + f"\n{'=' * 55}")
        print(Fore.GREEN + "  Crawling Complete!")
        print(Fore.YELLOW + f"  Total Pages Crawled : {len(self.pages_data)}")
        print(Fore.CYAN + f"{'=' * 55}\n")

        return self.pages_data

    def save_results(self, filepath="data/crawl_results.json"):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.pages_data, f, indent=4, ensure_ascii=False)
        print(Fore.GREEN + f"  Results saved to → {filepath}\n")