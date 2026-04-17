from crawler.crawler import WebsiteCrawler
from data.database import DatabaseManager
from colorama import Fore, init

init(autoreset=True)

if __name__ == "__main__":
    url = input("Enter website URL (e.g. https://example.com): ").strip()

    if not url:
        print(Fore.RED + "No URL provided. Exiting.")
        raise SystemExit

    # Phase 1 - Crawl
    print(Fore.CYAN + "\n  Starting crawler...")
    crawler = WebsiteCrawler(base_url=url, max_pages=20)
    results = crawler.crawl()

    if not results:
        print(Fore.RED + "No pages were crawled. Exiting.")
        raise SystemExit

    crawler.save_results()

    # Phase 2 - Save to database
    print(Fore.CYAN + "\n  Processing & saving to database...")
    db = DatabaseManager()
    session_id = db.save_crawl_data(url, results)
    summary, df = db.get_summary(session_id)

    print(Fore.CYAN + f"\n{'='*55}")
    print(Fore.CYAN + "  Website Summary Report")
    print(Fore.CYAN + f"{'='*55}")
    for key, value in summary.items():
        print(Fore.YELLOW + f"  {key:<22}" + Fore.WHITE + f": {value}")
    print(Fore.CYAN + f"{'='*55}\n")
    db.close()