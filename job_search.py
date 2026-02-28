import random
import time
from ddgs import DDGS

def search_jobs(query, location="India", max_results=15, remote_only=False):
    """
    Searches for jobs on LinkedIn, Indeed, Glassdoor, and Naukri using DuckDuckGo (via ddgs).
    
    Args:
        query (str): Job title or keywords.
        location (str): Location for the job search.
        max_results (int): Total number of results to fetch.
        
    Returns:
        list: A list of dictionaries containing job details (title, link, snippet, platform).
    """
    print(f"Searching for '{query}' in '{location}' using DuckDuckGo...")
    all_jobs = []

    platforms = {
        "linkedin": "site:linkedin.com/jobs",
        "indeed": "site:indeed.com",
        "glassdoor": "site:glassdoor.com",
        "naukri": "site:naukri.com"
    }

    def map_region(loc):
        if not loc:
            return None
        key = loc.strip().lower()
        if "india" in key or key in {"in", "bharat"}:
            return "in-en"
        if "united states" in key or key in {"us", "usa"} or "america" in key:
            return "us-en"
        if "united kingdom" in key or key in {"uk", "gb"} or "england" in key:
            return "gb-en"
        if "canada" in key or key == "ca":
            return "ca-en"
        if "australia" in key or key == "au":
            return "au-en"
        if "germany" in key or key in {"de", "deutschland"}:
            return "de-de"
        return None

    results_per_platform = max(2, max_results // len(platforms))
    region = map_region(location)

    try:
        with DDGS() as ddgs:
            for platform, site in platforms.items():
                base_terms = f"\"{query}\""
                if location:
                    base_terms += f" \"{location}\""
                if remote_only:
                    base_terms += " (\"remote\" OR \"work from home\")"
                search_query = f"{site} {base_terms} jobs"
                print(f"  - Searching {platform}...")
                try:
                    results = ddgs.text(search_query, region=region, max_results=results_per_platform)
                    count = 0
                    for result in results:
                        job = {
                            "title": result.get("title", "No Title"),
                            "link": result.get("href", "#"),
                            "snippet": result.get("body", "No description available"),
                            "platform": platform.capitalize()
                        }
                        all_jobs.append(job)
                        count += 1
                    if count == 0:
                        print(f"    No results for {platform}")
                    else:
                        print(f"    Found {count} results for {platform}")
                    time.sleep(random.uniform(1, 2))
                except Exception as e:
                    print(f"Error searching {platform}: {e}")
                    continue
    except Exception as e:
        print(f"Fatal error initializing DDGS: {e}")
        return []

    return all_jobs

if __name__ == "__main__":
    # Test the function
    jobs = search_jobs("Python Developer", "Bangalore", max_results=10)
    print(f"\nTotal jobs found: {len(jobs)}")
    for job in jobs:
        print(f"- {job['title']} ({job['platform']}): {job['link']}")
