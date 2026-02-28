import streamlit as st
import os
import io
from pypdf import PdfReader
from job_search import search_jobs
from agent_logic import configure_gemini, analyze_and_optimize_resume, generate_cover_letter
from export_utils import markdown_to_docx, markdown_to_pdf

# Page Configuration
st.set_page_config(
    page_title="AI Job Agent",
    page_icon="💼",
    layout="wide"
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

# Main Content
tab1, tab2, tab3 = st.tabs(["🔍 Job Search", "📝 Resume Optimizer", "✉️ Cover Letter"])

# Tab 1: Job Search
with tab1:
    st.header("Find Your Next Opportunity")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Job Title / Keywords", placeholder="e.g. Python Developer, Data Scientist")
    with col2:
        location = st.text_input("Location", value="India", placeholder="e.g. Remote, Bangalore")
    
    if st.button("Search Jobs", type="primary"):
        if query:
            with st.spinner(f"Searching for '{query}' in '{location}'..."):
                jobs = search_jobs(query, location)
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
                st.markdown(f"""
                <div style="padding: 1rem; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 1rem; background-color: #f9f9f9; color: #333333;">
                    <h3 style="margin-top: 0; color: #000000;">{job['title']}</h3>
                    <p style="color: #333333;"><strong>Platform:</strong> {job['platform']}</p>
                    <p style="color: #555555;">{job['snippet'][:200]}...</p>
                    <a href="{job['link']}" target="_blank" style="text-decoration: none; color: #007bff; font-weight: bold;">View Job Posting ↗</a>
                </div>
                """, unsafe_allow_html=True)

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
                            col_d1, col_d2, col_d3 = st.columns(3)
                            
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
                                
                            with col_d3:
                                try:
                                    pdf_file = markdown_to_pdf(result)
                                    st.download_button(
                                        label="Download PDF",
                                        data=pdf_file,
                                        file_name="optimized_resume.pdf",
                                        mime="application/pdf"
                                    )
                                except Exception as e:
                                    st.error(f"PDF generation failed: {e}")

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
                        col_c1, col_c2, col_c3 = st.columns(3)
                        
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
                            
                        with col_c3:
                            try:
                                pdf_file = markdown_to_pdf(result)
                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_file,
                                    file_name="cover_letter.pdf",
                                    mime="application/pdf"
                                )
                            except Exception as e:
                                st.error(f"PDF generation failed: {e}")

# Footer
st.divider()
st.markdown("Built with ❤️ using Streamlit & Gemini")
