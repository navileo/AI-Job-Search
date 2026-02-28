import os
from resume_utils import extract_text_from_pdf, save_text_to_file
from job_search import search_jobs, display_jobs
from agent_logic import configure_gemini, analyze_and_optimize_resume

def main_menu():
    """
    Displays the main menu.
    """
    print("\n--- AI Job Agent ---")
    print("1. Search for Jobs")
    print("2. Optimize Resume for a Job")
    print("3. Exit")
    return input("Select an option (1-3): ")

def handle_job_search():
    """
    Handles the job search workflow.
    """
    query = input("Enter job title or keywords (e.g., Python Developer): ")
    if not query:
        print("Search cancelled.")
        return
    
    location = input("Enter location (e.g., Bangalore, Remote, USA) [Default: India]: ")
    if not location:
        location = "India"
    
    # We pass the location to our updated search function
    # Note: search_jobs now returns a list of dictionaries with 'platform' key
    all_jobs = search_jobs(query, location)
    display_jobs(all_jobs)

def handle_resume_optimization(model):
    """
    Handles the resume optimization workflow.
    """
    if not model:
        print("Error: Gemini model not configured. Please check your API key.")
        return

    # 1. Get Resume
    resume_path = input("Enter the path to your PDF resume: ")
    if not os.path.exists(resume_path):
        print("Error: File not found.")
        return
    
    print("Extracting text from resume...")
    resume_text = extract_text_from_pdf(resume_path)
    if not resume_text:
        print("Failed to extract text from resume.")
        return

    # 2. Get Job Description
    print("\nHow would you like to provide the Job Description?")
    print("1. Paste text directly")
    print("2. Load from a file")
    jd_choice = input("Select (1 or 2): ")
    
    jd_text = ""
    if jd_choice == '1':
        print("Paste the Job Description below (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        jd_text = "\n".join(lines)
    elif jd_choice == '2':
        jd_path = input("Enter path to JD file: ")
        if os.path.exists(jd_path):
            with open(jd_path, 'r', encoding='utf-8') as f:
                jd_text = f.read()
        else:
            print("File not found.")
            return
    else:
        print("Invalid choice.")
        return

    if not jd_text:
        print("Job Description is empty.")
        return

    # 3. Analyze and Optimize
    print("\nAnalyzing and Optimizing... (This may take a moment)")
    result = analyze_and_optimize_resume(model, resume_text, jd_text)
    
    print("\n--- Analysis Result ---")
    print(result)
    
    # 4. Save Result
    save_option = input("\nDo you want to save this result to a file? (y/n): ")
    if save_option.lower() == 'y':
        filename = input("Enter filename (e.g., optimized_resume.md): ")
        if save_text_to_file(result, filename):
            print(f"Saved to {filename}")

if __name__ == "__main__":
    # Initialize Model
    model = configure_gemini()
    
    while True:
        choice = main_menu()
        
        if choice == '1':
            handle_job_search()
        elif choice == '2':
            handle_resume_optimization(model)
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")
