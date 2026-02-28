import os
import time
import random
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def configure_gemini():
    """
    Configures the Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        # Default to 2.0 Flash, but we will handle fallback in generation functions
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return None

def generate_with_retry(model, prompt):
    """
    Helper function to generate content with retry logic and model fallback.
    """
    # List of models to try in order of preference
    # Try the passed model first (usually gemini-2.0-flash), then fallback to other versions
    models_to_try = [
        model, 
        'gemini-2.0-flash-lite', 
        'gemini-2.0-flash-001',
        'gemini-2.5-flash',
        'gemini-1.5-flash'
    ]
    
    last_error = None
    
    for current_model_candidate in models_to_try:
        current_model = None
        
        # If it's a string, create a model instance; otherwise use the object
        if isinstance(current_model_candidate, str):
            try:
                print(f"Attempting to use model: {current_model_candidate}")
                current_model = genai.GenerativeModel(current_model_candidate)
            except Exception as e:
                print(f"Skipping model {current_model_candidate} due to init error: {e}")
                continue
        else:
            current_model = current_model_candidate

        # Retry loop for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = current_model.generate_content(prompt)
                return response.text
            except exceptions.ResourceExhausted as e:
                # 429 Error - Quota Exceeded
                # If we hit a rate limit, we should probably try the NEXT model sooner
                # rather than waiting too long on this one, especially if the wait time is 20s+
                print(f"Quota exceeded for current model. Attempt {attempt+1}/{max_retries}.")
                
                # Check if we should switch models immediately on the first 429
                # If this is not the last model, maybe just break and try the next one?
                # But sometimes a short wait helps.
                
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                if attempt == max_retries - 1:
                     print("Max retries reached for this model.")
                else:
                    print(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                
                last_error = e
            except Exception as e:
                # Other errors (e.g. 404, 500) - try next model immediately
                print(f"Error with model: {e}")
                last_error = e
                break # Break retry loop to try next model in outer loop
        
        # If we exhausted retries for this model, continue to next model
        print("Switching to fallback model...")

    return f"Error: Unable to generate content. Please try again later. Details: {last_error}"

def analyze_and_optimize_resume(model, resume_text, job_description):
    """
    Analyzes the resume against the JD and optimizes if necessary.
    """
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) Resume Optimizer.
    
    Your Task:
    1. Compare the provided RESUME content with the JOB DESCRIPTION.
    2. Calculate a "Match Percentage" (0-100%) based on skills, experience, and keywords.
    3. If the Match Percentage is >= 80%, return ONLY a message stating the match percentage and that no changes are needed.
    4. If the Match Percentage is < 80%, you MUST rewrite the resume to improve the match score.
    
    Constraints for Rewriting:
    - You CAN modify: Professional Summary, Skills, formatting, and "Other" sections (like hobbies or volunteer work if relevant).
    - You MUST NOT modify: Education background, Certificates, Internships, Projects (Title, Company, Dates must stay exact; bullet points can be slightly tweaked for keywords but keep the core truth).
    - **CRITICAL**: The input resume text may contain a section "--- EXTRACTED HYPERLINKS ---" at the bottom. **Use these URLs** to correctly hyperlink LinkedIn, Portfolio, GitHub, or other profiles in the Contact Information section. Do not invent links.
    - **Formatting Requirements**:
    - Use " | " to separate Company/School and Dates. Example: `**Company Name** | Jan 2020 - Present`
    - Use " | " to separate Role and Location. Example: `*Software Engineer* | New York, NY`
    - Use standard Markdown headers (# Name, ## Section).
    - Use "-" for bullet points.
    - Do NOT use horizontal rules (---).
    - Ensure the output is clean and ready for PDF generation.
    - Focus on adding relevant keywords from the JD into the Summary and Skills sections.
    
    Input Data:
    
    === JOB DESCRIPTION ===
    {job_description}
    
    === RESUME CONTENT ===
    {resume_text}
    
    Output Format:
    If Match >= 80%:
    "Match Score: [Score]%\n\nGreat match! No significant changes needed."
    
    If Match < 80%:
    "Match Score: [Score]%\n\nOptimization Required. Here is the updated ATS-friendly resume:\n\n[Markdown Resume Content]"
    """
    
    return generate_with_retry(model, prompt)

def generate_cover_letter(model, resume_text, job_description):
    """
    Generates a tailored cover letter based on the resume and job description.
    """
    prompt = f"""
    You are a professional career coach and expert cover letter writer.
    
    Your Task:
    Write a compelling, professional cover letter tailored to the specific JOB DESCRIPTION using the candidate's RESUME.
    
    Guidelines:
    1.  **Professional Tone**: Use a formal yet enthusiastic tone.
    2.  **Highlight Relevance**: Focus on skills and experiences from the RESUME that directly match the JOB DESCRIPTION requirements.
    3.  **Structure**:
        -   **Header**: Placeholders for [Your Name], [Your Address], [Date], [Hiring Manager Name], [Company Name], [Company Address].
        -   **Opening**: State the position being applied for and express strong interest.
        -   **Body Paragraphs (2-3)**: Connect specific achievements from the resume to the needs of the role. Use metrics if available in the resume.
        -   **Closing**: Reiterate enthusiasm and request an interview.
        -   **Sign-off**: "Sincerely," followed by [Your Name].
    4.  **Conciseness**: Keep it to one page (approx. 300-400 words).
    5.  **No Hallucinations**: Do not invent experiences not present in the resume. If information is missing (like company name), use placeholders like [Company Name].
    
    Input Data:
    
    === JOB DESCRIPTION ===
    {job_description}
    
    === RESUME CONTENT ===
    {resume_text}
    """
    
    return generate_with_retry(model, prompt)
