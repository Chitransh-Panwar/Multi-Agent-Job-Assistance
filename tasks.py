from crewai import Task

# ─────────────────────────────────────────
# TASK 1: ANALYZE JOB DESCRIPTION
# ─────────────────────────────────────────
def create_job_analysis_task(job_description, agent):
    return Task(
        description=f"""
        Analyze the following job description thoroughly and extract 
        all critical information:

        JOB DESCRIPTION:
        {job_description}

        Your analysis must include:
        1. REQUIRED SKILLS - List all technical and soft skills
        2. EXPERIENCE LEVEL - Junior/Mid/Senior and years required
        3. KEY RESPONSIBILITIES - Top 5 main duties
        4. COMPANY CULTURE - What kind of workplace is this?
        5. APPLICATION TIPS - 3 specific tips to stand out
        6. ATS KEYWORDS - Important keywords to include in CV
        """,
        expected_output="""
        A detailed structured report with:
        - Required Skills (technical and soft)
        - Experience Level
        - Key Responsibilities
        - Company Culture
        - Application Tips
        - ATS Keywords list
        """,
        agent=agent
    )


# ─────────────────────────────────────────
# TASK 2: CV OPTIMIZER
# ─────────────────────────────────────────
def create_resume_task(job_description, cv_content,
                       latex_content=None, agent=None,
                       context_tasks=None):
    from agents import create_resume_agent
    if agent is None:
        agent = create_resume_agent()

    cv_format = "LaTeX" if latex_content else "Plain Text"
    cv_to_use = latex_content if latex_content else cv_content

    task = Task(
        description=f"""
        Using the job analysis from the previous task, optimize 
        the candidate's existing CV for this specific job.

        STRICT RULES:
        ❌ Do NOT add fake experience or skills
        ❌ Do NOT change dates, company names, education
        ❌ Do NOT change LaTeX structure or formatting
        ✅ Only update Professional Summary
        ✅ Only reorder Skills by relevance
        ✅ Only strengthen experience bullets with keywords
        ✅ Output must be valid compilable LaTeX

        JOB DESCRIPTION:
        {job_description}

        CANDIDATE'S EXISTING CV ({cv_format}):
        {cv_to_use}

        OUTPUT FORMAT:
        1. CHANGES SUMMARY - What changed and why
        2. UPDATED CV - Complete LaTeX code only
        3. ATS KEYWORDS ADDED - List of keywords added
        4. MATCH SCORE - How well CV matches job (0-100%)
        """,
        expected_output="""
        Complete optimization containing:
        - Changes Summary
        - Full updated LaTeX CV code
        - ATS Keywords added
        - Match Score percentage
        """,
        agent=agent,
        context=context_tasks  # ← receives Job Analyzer output!
    )
    return task

def create_messaging_task(job_description,candidate_name,agent=None,context_tasks=None):
    from agents import create_messaging_agent
    if agent is None:
        agent=create_messaging_agent()

    return Task(
        description=f"""
        Using the job analysis and CV optimization from previous 
        tasks, create personalized outreach messages for this job.

        JOB DESCRIPTION:
        {job_description}

        CANDIDATE NAME: {candidate_name}

        Create these 3 messages:

        1. LINKEDIN CONNECTION REQUEST (300 chars max!)
           - Reference specific thing about the company/role
           - Mention one relevant skill or achievement
           - Clear reason for connecting
           - Must be under 300 characters!

        2. COLD EMAIL TO HIRING MANAGER
           - Subject line that gets opened
           - Opening that shows company research
           - 2-3 sentences connecting experience to role
           - Clear call to action
           - Professional sign off
           - Keep under 150 words!

        3. FOLLOW UP MESSAGE (send after 1 week)
           - Reference previous message
           - Add new value (recent achievement/project)
           - Gentle nudge for response
           - Keep under 100 words!
        """,
        expected_output="""
        3 ready to send messages:
        - LinkedIn Connection Request (under 300 chars)
        - Cold Email with subject line (under 150 words)
        - Follow Up Message (under 100 words)
        """,
        agent=agent,
        context=context_tasks
    )