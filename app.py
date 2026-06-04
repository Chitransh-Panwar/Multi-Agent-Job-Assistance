import streamlit as st
import os 
import tempfile
import pandas as pd 
from datetime import datetime
from crewai import Crew,Process
from agents import create_job_analyzer_agent,create_messaging_agent,create_resume_agent
from tasks import create_job_analysis_task,create_messaging_task,create_resume_task
from tools import fetch_all_jobs,load_cv 
from main import compile_latex_to_pdf,extract_latex_from_output

st.set_page_config(
    page_title="Ai Job Assistant",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding: 1.5rem 2rem; }
    .stButton button { width: 100%; }
    .match-high { color: #22c55e; font-weight: 500; }
    .match-mid  { color: #f59e0b; font-weight: 500; }
    .match-low  { color: #ef4444; font-weight: 500; }
    div[data-testid="metric-container"] {
        background: var(--background-color);
        border: 1px solid rgba(128,128,128,0.2);
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

defaults={
    "jobs":[],
    "matched_jobs":[],
    "cv_text":None,
    "latex_content":None,
    "candidate_name":"",
    "results":{},
    "log":[],
    "processing":False,
    "Processed_count":0,
    "min_score":60
}

for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v 

def run_crew_for_jobs(job,cv_text,latex_content,candidate_name,job_index):
    job_description=f"""
    Title:{job['title']}
    Company:{job['company']}
    Location:{job['location']}
    Source:{job['source']}
    Description:{job['description']}
    URL:{job['url']}
    """

    analyzer_agent=create_job_analyzer_agent()
    resume_agent=create_resume_agent()
    messaging_agent=create_messaging_agent()

    analysis_task=create_job_analysis_task(
        job_description,analyzer_agent
    )
    resume_task=create_resume_task(
        job_description=job_description,
        cv_content=cv_text,
        latex_content=latex_content,
        agent=resume_agent,
        context_tasks=[analysis_task]
    )

    messaging_task=create_messaging_task(
        job_description=job_description,
        candidate_name=candidate_name,
        agent=messaging_agent,
        context_tasks=[analysis_task,resume_task]
    )

    crew=Crew(
        agents=[analyzer_agent,resume_agent,messaging_agent],
        tasks=[analysis_task,resume_task,messaging_task],
        process=Process.sequential,
        verbose=False 
    )
    result = crew.kickoff()

    safe_company=job['company'].replace(" ","_").replace("/","_")
    safe_title=job['title'].replace(" ","_").replace("/","_")
    folder_name=f"{job_index}_{safe_company}_{safe_title}"

    tex_dir = f"outputs/texfiles/{folder_name}"
    pdf_dir = f"outputs/pdffiles/{folder_name}"
    msg_dir = f"outputs/messages/{folder_name}"

    os.makedirs(tex_dir,exist_ok=True)
    os.makedirs(pdf_dir,exist_ok=True)
    os.makedirs(msg_dir,exist_ok=True)

    tex_path=f"{tex_dir}/optimized_cv.tex"
    latex_code=extract_latex_from_output(result.tasks_output[1].raw)
    with open(tex_path,"w") as f:
        f.write(latex_code)

    msg_path=f"{msg_dir}/messages.txt"
    with open(msg_path,"w") as f:
        f.write(str(result))

    pdf_path=compile_latex_to_pdf(tex_path,pdf_dir)

    return {
        "job" : job,
        "latex_code":latex_code,
        "message":str(result),
        "tex_path":tex_path,
        "pdf_path":pdf_path,
        "msg_path":msg_path,
        "folder":folder_name
    }

def estimate_match_score(job,cv_text,latex_content):
    cv=(cv_text or "" ) + (latex_content or "")
    cv_lower=cv.lower()
    desc_lower=(job.get("description","") + job.get("title","")).lower()

    words=[w.strip(".,[]()") for w in desc_lower.strip()
           if len(w)>4]
    if not words:
        return 50 
    
    matches=sum(1 for w in words if w in cv_lower)
    score=min(int((matches/len(words))*100*3),100)
    return max(score,10)

