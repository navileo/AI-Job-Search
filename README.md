# AI Job Search Agent

This is an AI-powered job search agent that helps you find jobs and optimize your resume.

## Features
- Job Search across LinkedIn, Indeed, Glassdoor, and Naukri via DuckDuckGo.
- Resume Optimization with Google Gemini: compares against JD, rewrites in ATS-friendly Markdown.
- LaTeX-style PDF layout using fpdf2: centered header, section rules, right-aligned dates.
- Clickable links: extracts hyperlinks from uploaded PDF and reuses them in the output.
- Export to PDF and DOCX with safe Latin‑1 sanitization (prevents “?” symbols).

## Setup

1.  **Install Python 3.11+**
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```
3.  **Activate the virtual environment:**
    - Windows: `venv\Scripts\activate`
    - Mac/Linux: `source venv/bin/activate`
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Configure API Key:**
    - Get a free API key from Google AI Studio.
    - Create a `.env` file in the project root with one of:
      - `GEMINI_API_KEY=your_key_here`  ← preferred
      - or `OPENAI_API_KEY=your_key_here`  ← fallback supported by the app

## Running the App

Double-click **`start.bat`** to launch the application.

Or run manually:
```bash
venv\Scripts\python run.py
```

The app will open in your browser at `http://localhost:8504`.

## Deploy for Free

### Option 1: Streamlit Community Cloud (recommended)
1. Push this folder to a public GitHub repository.
2. Go to streamlit.io → Sign in → New app.
3. Select your repo/branch. Main file: `app.py`.
4. Open “Settings → Secrets” and add:
   - `GEMINI_API_KEY=your_key_here`
5. Deploy. The app builds from `requirements.txt` and goes live on a streamlit.app URL.

### Option 2: Hugging Face Spaces (Streamlit)
1. On huggingface.co → Create Space → SDK = Streamlit.
2. Upload the code or connect the GitHub repo. App file: `app.py`.
3. Settings → Repo Secrets → add:
   - `GEMINI_API_KEY=your_key_here`
4. The Space auto-builds from `requirements.txt` and serves the app for free on a public URL.

Notes:
- You don’t need `run.py` on these platforms; they run Streamlit directly.
- Keep `app.py`, `requirements.txt`, and `.env` (local only). Put API keys in platform Secrets, not in the repo.

## Usage
- Upload your resume as a PDF. The app extracts text and embedded hyperlinks (LinkedIn, GitHub, portfolio).
- Paste a Job Description and click Analyze. The AI returns an ATS‑friendly Markdown resume.
- Download as PDF or DOCX.

## Formatting Guide (used by the AI)
- Use standard Markdown headers: `# Name`, `## EXPERIENCE`, `## EDUCATION`, etc.
- Use `-` for bullet points, single-line bullets preferred.
- Use pipes to split headers so the PDF aligns like LaTeX:
  - `**Company** | Jan 2020 - Present`
  - `*Role* | City, Country`
- Avoid horizontal rules (`---`).

## Troubleshooting
- “?” characters in PDF: input contained symbols outside Latin‑1; text is sanitized automatically. Replace unusual symbols with ASCII if needed.
- “Not enough horizontal space” errors: very long unbroken tokens can cause layout issues. Shorten or split long URLs/strings.
- Links missing in PDF: ensure your uploaded resume contains the correct links or include them in the contact line; the app reuses extracted links.
- Port already in use: edit `run.py` and change `--server.port` to a free port.
- If the browser doesn’t open, copy the URL from the terminal manually.
