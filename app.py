import streamlit as st
import os
import io
from pypdf import PdfReader
from job_search import search_jobs
from agent_logic import configure_gemini, analyze_and_optimize_resume, generate_cover_letter
from export_utils import markdown_to_docx
from html import escape

# Page Configuration
st.set_page_config(
    page_title="AI Job Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global styles
st.markdown(
    """
    <style>
      /* Keep default Streamlit header/menu visible; branding ribbon hidden below */

      .job-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow .2s ease, border-color .2s ease, transform .05s ease;
      }
      .job-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.10);
        border-color: #cbd5e1;
      }
      .job-title {
        font-weight: 700;
        font-size: 1.1rem;
        margin: 0 0 4px 0;
      }
      .job-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: .2px;
      }
      .badge-linkedin { background: #eef2ff; color: #3730a3; }
      .badge-indeed { background: #ecfeff; color: #155e75; }
      .badge-naukri, .badge-foundit { background: #f0f9ff; color: #075985; }
      .badge-glassdoor { background: #f0fdf4; color: #166534; }
      .badge-default { background: #f5f5f5; color: #374151; }
      .job-snippet {
        color: #475569;
        margin: 0 0 12px 0;
        line-height: 1.45;
      }
      .link-btn {
        display: inline-block;
        text-decoration: none;
        background: #2563eb;
        color: #ffffff !important;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 700;
        transition: background .15s ease;
      }
      .link-btn:hover { background: #1d4ed8; }
      .share-wrap { display:flex; gap:10px; flex-wrap: wrap; }
      .share-btn {
        display:inline-flex; align-items:center; gap:8px;
        padding:8px 12px; border-radius:999px; color:#fff !important; text-decoration:none; font-weight:700;
      }
      .share-tw { background:#1da1f2; }
      .share-li { background:#0a66c2; }
      .share-hn { background:#ff6600; color:#000 !important; }
      .copy-link { background:#334155; }

      /* No global UI elements are hidden; keeping Streamlit menu and sidebar visible */
    </style>
    """,
    unsafe_allow_html=True
)

 

# Initialize Session State
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""

def extract_text_from_uploaded_pdf(uploaded_file):
    """Helper to extract text and links from uploaded PDF file object"""
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        links = []
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
            # Extract links from annotations
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    try:
                        obj = annot.get_object()
                        if "/A" in obj:
                            action = obj["/A"]
                            if "/URI" in action:
                                links.append(action["/URI"])
                    except Exception:
                        continue
        
        # Clean up text: reduce excessive newlines
        import re
        # Replace 3 or more newlines with 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Append extracted links so the LLM can use them
        if links:
            text += "\n\n--- EXTRACTED HYPERLINKS ---\n"
            # Remove duplicates while preserving order
            seen_links = set()
            for link in links:
                if link not in seen_links:
                    text += f"{link}\n"
                    seen_links.add(link)
                    
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# Sidebar
with st.sidebar:
    st.title("🤖 AI Job Agent")
    st.markdown("Your personal assistant for job hunting and resume optimization.")
    
    st.divider()
    
    # API Key Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.warning("⚠️ GEMINI_API_KEY not found in environment.")
        user_key = st.text_input("Enter Gemini API Key:", type="password")
        if user_key:
            os.environ["GEMINI_API_KEY"] = user_key
            st.success("Key set temporarily!")
    else:
        st.success("✅ API Key Configured")

    # Share panel removed per request

# Main Content
tab1, tab2, tab3 = st.tabs(["🔍 Job Search", "📝 Resume Optimizer", "✉️ Cover Letter"])

# Tab 1: Job Search
with tab1:
    st.header("Find Your Next Opportunity")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Job Title / Keywords", placeholder="e.g. Python Developer, Data Scientist")
    with col2:
        location = st.text_input("Location", value="India", placeholder="e.g. Bangalore, India")
        remote_only = st.checkbox("Remote only", value=False)
    
    if st.button("Search Jobs", type="primary"):
        if query:
            with st.spinner(f"Searching for '{query}' in '{location}'..."):
                loc = (location or "").strip() or "India"
                jobs = search_jobs(query, loc, remote_only=remote_only)
                st.session_state.jobs = jobs
            
            if not jobs:
                st.warning("No jobs found. Try different keywords.")
        else:
            st.warning("Please enter a job title.")

    # Display Results
    if st.session_state.jobs:
        st.subheader(f"Found {len(st.session_state.jobs)} Jobs")
        
        for job in st.session_state.jobs:
            with st.container():
                title = escape(job.get('title', 'Untitled'))
                platform = (job.get('platform') or 'Other').strip()
                platform_key = platform.lower()
                badge_class = {
                    'linkedin': 'badge-linkedin',
                    'indeed': 'badge-indeed',
                    'naukri': 'badge-naukri',
                    'foundit': 'badge-foundit',
                    'glassdoor': 'badge-glassdoor',
                }.get(platform_key, 'badge-default')
                snippet = escape((job.get('snippet') or '')[:220]).rstrip()
                if snippet and not snippet.endswith('...'):
                    snippet += '...'
                link = job.get('link') or '#'
                
                st.markdown(
                    f"""
                    <div class="job-card">
                      <div class="job-title">{title}</div>
                      <div class="job-meta">
                        <span class="badge {badge_class}">{escape(platform.title())}</span>
                      </div>
                      <p class="job-snippet">{snippet}</p>
                      <a class="link-btn" href="{link}" target="_blank" rel="noopener noreferrer">View Job Posting ↗</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# Tab 2: Resume Optimizer
with tab2:
    st.header("Optimize Your Resume")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Resume")
        uploaded_resume = st.file_uploader("Upload PDF Resume", type="pdf", key="resume_opt")
        
    with col2:
        st.subheader("2. Job Description")
        jd_text = st.text_area("Paste Job Description here", height=200, key="jd_opt")

    if st.button("Analyze & Optimize", type="primary"):
        if not uploaded_resume:
            st.error("Please upload your resume.")
        elif not jd_text:
            st.error("Please paste the job description.")
        else:
            # Configure Model
            model = configure_gemini()
            if not model:
                st.error("Failed to configure Gemini AI. Please check your API key.")
            else:
                with st.spinner("Analyzing your resume against the job description..."):
                    # Extract text
                    resume_text = extract_text_from_uploaded_pdf(uploaded_resume)
                    
                    if resume_text:
                        # Store in session state for other tabs
                        st.session_state.resume_text = resume_text
                        
                        # Analyze
                        result = analyze_and_optimize_resume(model, resume_text, jd_text)
                        
                        if result.startswith("Error:"):
                            st.error(result)
                        else:
                            st.success("Analysis Complete!")
                            st.markdown("### Result")
                            st.markdown(result)
                            
                            # Download Buttons
                            col_d1, col_d2 = st.columns(2)
                            
                            with col_d1:
                                st.download_button(
                                    label="Download MD",
                                    data=result,
                                    file_name="optimized_resume.md",
                                    mime="text/markdown"
                                )
                            
                            with col_d2:
                                docx_file = markdown_to_docx(result)
                                st.download_button(
                                    label="Download DOCX",
                                    data=docx_file,
                                    file_name="optimized_resume.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                                
                            

# Tab 3: Cover Letter Generator
with tab3:
    st.header("Generate Cover Letter")
    
    st.markdown("Create a personalized cover letter for a specific job.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Resume Source")
        resume_source = st.radio("Choose Resume Source", ["Upload New", "Use Last Uploaded"])
        
        if resume_source == "Upload New":
            cl_uploaded_resume = st.file_uploader("Upload PDF Resume", type="pdf", key="resume_cl")
        else:
            if st.session_state.resume_text:
                st.success("Using resume from Resume Optimizer tab.")
            else:
                st.warning("No resume found in session. Please upload one.")
                cl_uploaded_resume = st.file_uploader("Upload PDF Resume", type="pdf", key="resume_cl_fallback")
    
    with col2:
        st.subheader("2. Job Description")
        cl_jd_text = st.text_area("Paste Job Description here", height=200, key="jd_cl")

    if st.button("Generate Cover Letter", type="primary"):
        # Determine resume text
        final_resume_text = ""
        if resume_source == "Upload New" and cl_uploaded_resume:
            final_resume_text = extract_text_from_uploaded_pdf(cl_uploaded_resume)
        elif resume_source == "Use Last Uploaded":
            if st.session_state.resume_text:
                final_resume_text = st.session_state.resume_text
            elif 'cl_uploaded_resume' in locals() and cl_uploaded_resume:
                final_resume_text = extract_text_from_uploaded_pdf(cl_uploaded_resume)
        
        if not final_resume_text:
            st.error("Please provide a resume.")
        elif not cl_jd_text:
            st.error("Please paste the job description.")
        else:
            # Configure Model
            model = configure_gemini()
            if not model:
                st.error("Failed to configure Gemini AI. Please check your API key.")
            else:
                with st.spinner("Drafting your cover letter..."):
                    result = generate_cover_letter(model, final_resume_text, cl_jd_text)
                    
                    if result.startswith("Error:"):
                        st.error(result)
                    else:
                        st.success("Cover Letter Generated!")
                        st.markdown("### Draft")
                        st.markdown(result)
                        
                        # Download Buttons
                        col_c1, col_c2 = st.columns(2)
                        
                        with col_c1:
                            st.download_button(
                                label="Download MD",
                                data=result,
                                file_name="cover_letter.md",
                                mime="text/markdown"
                            )
                            
                        with col_c2:
                            docx_file = markdown_to_docx(result)
                            st.download_button(
                                label="Download DOCX",
                                data=docx_file,
                                file_name="cover_letter.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                            
                        

# Footer
st.divider()
st.markdown("Built with ❤️ using Streamlit & Gemini")
