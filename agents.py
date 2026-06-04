import os 
from dotenv import load_dotenv
from crewai import Agent 

load_dotenv()

from langchain_openai import ChatOpenAI
import os

def get_llm():
    return ChatOpenAI(
        model="openrouter/owl-alpha",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.3,
        max_tokens=500
    )

# ─────────────────────────────────────────
# AGENT 1: JOB ANALYZER
# ─────────────────────────────────────────

def create_job_analyzer_agent():
    """Agent that analyzes job descriptions"""
    return Agent(
        role="Expert Job Description Analyzer",
        goal="""Analyze job descriptions thoroughly and extract 
                all critical information that a job seeker needs 
                to tailor their application perfectly.""",
        backstory="""You are a seasoned HR professional with 10+ years 
                of experience in talent acquisition across top tech companies. 
                You have reviewed thousands of job descriptions and know 
                exactly what employers are looking for. You have a sharp eye 
                for identifying must-have skills vs nice-to-have skills, 
                understanding company culture from job postings, and spotting 
                red flags in job descriptions.""",
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


# ─────────────────────────────────────────
# AGENT 2: RESUME OPTIMIZER
# ─────────────────────────────────────────
def create_resume_agent():
    """Agent that optimizes existing CV for specific jobs"""
    return Agent(
        role="Expert ATS Resume Optimizer and LaTeX Specialist",
        goal="""Optimize the candidate's existing CV for specific job 
                requirements while preserving the original format and 
                structure. Only modify what is absolutely necessary to 
                better match the job description.
                key points :
                1. the summary must not exceed more than 60 words .
                2. 1st 2 projects must have 3 pointers  and other projects with 2 pointers with  impactful topics about project (do not edit core technologies used in projects).
                3. experience can have only 2 bullet points only relevant to the job  .
                4. No word should be repeated in the resume content .
                5.use more numbers in projects bullet points 
                6.there can only be maximum 5 pointers in skills section with maximum 13 words in each (including headers of pointers ) .
                """,
        backstory="""You are an elite ATS optimization specialist and 
                LaTeX expert with 15+ years of experience. Your golden 
                rule is: NEVER change what doesn't need changing. You 
                only update the summary, reorder skills by relevance, 
                and strengthen experience bullets with job-specific 
                keywords. You always output valid LaTeX code that can 
                be directly pasted into Overleaf and compiled into a 
                professional PDF.""",
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )

def create_messaging_agent():
    return Agent(
        role="Professional Networking and Outreach Specialist",
        goal="""Write highly personalized, professional outreach 
                messages that get responses from recruiters and 
                hiring managers. Messages should feel human, 
                genuine and compelling — never generic or spammy.""",
        backstory="""You are a networking expert and career coach 
                who has helped thousands of candidates land interviews 
                through strategic outreach. You know exactly how to 
                craft LinkedIn messages that get responses, cold emails 
                that stand out in crowded inboxes, and follow-up s
                messages that are persistent without being annoying. 
                You understand that personalization is the key to 
                getting responses and always tailor messages to the 
                specific company, role and candidate background.""",
        llm=get_llm(),
        verbose=True,
        allow_delegations=False
    )

