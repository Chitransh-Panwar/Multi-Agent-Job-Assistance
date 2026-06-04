import os
from crewai import Crew, Process
from agents import create_job_analyzer_agent, create_resume_agent ,create_messaging_agent
from tasks import create_job_analysis_task, create_resume_task ,create_messaging_task
from tools import load_cv

# ─────────────────────────────────────────
# SAMPLE JOB DESCRIPTION
# ─────────────────────────────────────────
sample_job = """
Job Title: Python Developer
Company: TechCorp India
Location: Bangalore, India

Requirements:
- 2-4 years of Python development experience
- Strong knowledge of Django or FastAPI
- Experience with PostgreSQL and Redis
- Familiarity with AWS services (EC2, S3, Lambda)
- REST API design principles
- Git and CI/CD pipelines
- Good communication skills

Nice to Have:
- Docker and Kubernetes
- Microservices architecture

Responsibilities:
- Design and develop backend APIs
- Optimize database queries
- Write unit and integration tests
- Participate in code reviews

Salary: 8-15 LPA
"""

# ─────────────────────────────────────────
# COMPILE LATEX TO PDF USING TINYTEX
# ─────────────────────────────────────────
def compile_latex_to_pdf(tex_path, pdf_dir="outputs/pdffiles"):
    """Compile .tex file to PDF using TinyTeX"""
    try:
        import subprocess
        import shutil

        # Make sure directories exist
        os.makedirs(pdf_dir, exist_ok=True)

        # Get filename without extension
        filename = os.path.basename(tex_path).replace(".tex", "")

        # Compile PDF — output goes to a temp folder first
        temp_dir = "outputs/temp_compile"
        os.makedirs(temp_dir, exist_ok=True)

        result = subprocess.run(
            ["pdflatex",
             "-output-directory", temp_dir,
             "-interaction=nonstopmode",
             tex_path],  # ← use original tex_path directly
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Move ONLY the PDF to pdffiles folder
            temp_pdf = os.path.join(temp_dir, f"{filename}.pdf")
            final_pdf = os.path.join(pdf_dir, f"{filename}.pdf")
            shutil.move(temp_pdf, final_pdf)

            # Delete temp folder with .log .aux .out files
            shutil.rmtree(temp_dir)

            print(f"✅ PDF saved: {final_pdf}")
            return final_pdf
        else:
            print(f"❌ LaTeX compilation failed!")
            print(result.stderr[:500])
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None

    except Exception as e:
        print(f"❌ Compilation error: {e}")
        return None

# ─────────────────────────────────────────
# EXTRACT LATEX FROM AGENT OUTPUT
# ─────────────────────────────────────────
def extract_latex_from_output(result_text):
    """Extract only the LaTeX code from agent output"""
    result_str = str(result_text)

    # Try to find LaTeX content between \documentclass and \end{document}
    if "\\documentclass" in result_str and "\\end{document}" in result_str:
        start = result_str.find("\\documentclass")
        end = result_str.find("\\end{document}") + len("\\end{document}")
        return result_str[start:end]

    return result_str


# ─────────────────────────────────────────
# RUN THE CREW
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Job Search Crew...")
    print("─" * 50)

    # ── Load CV ──────────────────────────
    cv_text, latex_content = load_cv(
        pdf_path="my_cv.pdf",
        tex_path="my_cv.tex"
    )

    # ── Create Agents ────────────────────
    analyzer_agent = create_job_analyzer_agent()
    resume_agent = create_resume_agent()
    messaging_agent=create_messaging_agent()

    # ── Create Tasks ─────────────────────
    analysis_task = create_job_analysis_task(
        sample_job,
        analyzer_agent
    )

    resume_task = create_resume_task(
        job_description=sample_job,
        cv_content=cv_text,
        latex_content=latex_content,
        agent=resume_agent,
        context_tasks=[analysis_task]  # ← passes analyzer output!
    )

    messaging_task=create_messaging_task(
        job_description=sample_job,
        candidate_name="Chitransh Panwar",
        agent=messaging_agent,
        context_tasks=[analysis_task,resume_task]
    )

    # ── Run Crew ─────────────────────────
    crew = Crew(
        agents=[analyzer_agent, resume_agent,messaging_agent],
        tasks=[analysis_task, resume_task,messaging_task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()

    # ── Save LaTeX Output ─────────────────
    # ── Save LaTeX Output ─────────────────
    os.makedirs("outputs/texfiles", exist_ok=True)
    os.makedirs("outputs/pdffiles", exist_ok=True)
    os.makedirs("outputs/messages",exist_ok=True)

    tex_path = "outputs/texfiles/optimized_cv.tex"

    latex_code = extract_latex_from_output(result.tasks_output[1].raw)
    with open(tex_path, "w") as f:
        f.write(latex_code)
    print(f"\n✅ LaTeX saved: {tex_path}")

    messages_path="outputs/messages/outreach_message.txt"
    with open(messages_path,"w") as f:
        f.write(str(result))
    print(f"\n✅ Messages  saved: {messages_path}")
    # ── Compile to PDF ────────────────────
    print("\n📄 Compiling to PDF...")
    pdf_path = compile_latex_to_pdf(tex_path)

    if pdf_path:
        print("\n" + "═" * 50)
        print("🎉 SUCCESS! Your optimized CV is ready!")
        print(f"📄 PDF: {pdf_path}")
        print(f"📝 LaTeX: {tex_path}")
        print(f"📝 Messages : {messages_path}")
        
        print("═" * 50)
    else:
        print("\n⚠️ PDF compilation failed but LaTeX is saved!")
        print("📝 You can manually compile in Overleaf!")