import random
import time
from ddgs import DDGS

def search_jobs(query, location="India", max_results=15):
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
    
    # Define platform-specific keywords
    platforms = [
        "linkedin",
        "indeed",
        "glassdoor",
        "naukri"
    ]
    
    # Calculate results per platform (distribute evenly)
    results_per_platform = max(2, max_results // len(platforms))
    
    try:
        with DDGS() as ddgs:
            for platform in platforms:
                search_query = f"{query} {location} {platform} jobs"
                print(f"  - Searching {platform}...")
                
                try:
                    # Use ddgs.text() which returns a generator of results
                    # We limit to results_per_platform
                    # Note: max_results in ddgs.text is the max number of results to return from the generator
                    results = ddgs.text(search_query, max_results=results_per_platform)
                    
                    count = 0
                    for result in results:
                        # Create a job object
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

                    # Be polite to the search engine (though DDGS handles some rate limiting)
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
