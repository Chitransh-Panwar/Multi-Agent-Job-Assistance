import streamlit as st
import os 
import tempfile
import pandas as pd 
from datetime import datetime
from crewai import Crew,Process
from agents import create_job_analyzer_agent,create_messaging_agent,create_resume_agent
from tasks import create_job_analysis_task,create_messaging_task,create_resume_task
from tools import fetch_all_jobs,load_cv ,filter_jobs_by_date
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
    "min_score":60,
    "max_days":7
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
    description = str(job.get("description") or "")
    title = str(job.get("title") or "")

    desc_lower = f"{description} {title}".lower()
    words=[w.strip(".,[]()") for w in desc_lower.split() if len(w)>4]
           
    if not words:
        return 50 
    
    matches=sum(1 for w in words if w in cv_lower)
    score=min(int((matches/len(words))*100*3),100)
    return max(score,10)


def save_excel_log(log):
    import openpyxl
    from openpyxl.styles import (PatternFill,Font,Alignment,Border,Side)
    os.makedirs("outputs/tracker",exist_ok=True)
    path="outputs/tracker/job_applications.xlsx"

    df=pd.DataFrame(log)
    df.to_excel(path,index=False)

    wb=openpyxl.load_workbook(path)
    ws=wb.active
    ws.title="Applications"

    header_fill=PatternFill(
        start_color="1E3A5F",
        end_color="1E3A5F",
        fill_type="solid"
    )

    header_font=Font(
        color="FFFFFF",
        bold=True,
        size=11
    )
    border=Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")

    )

    for cell in ws[1]:
        cell.fill=header_fill
        cell.font=header_font 
        cell.alignment=Alignment(horizontal="center",vertical="center")
        cell.border=border

    green_fill = PatternFill(
        start_color="D4EDDA",
        end_color="D4EDDA",
        fill_type="solid"
    )
    yellow_fill = PatternFill(
        start_color="FFF3CD",
        end_color="FFF3CD",
        fill_type="solid"
    )
    red_fill = PatternFill(
        start_color="F8D7DA",
        end_color="F8D7DA",
        fill_type="solid"
    )

    for row in ws.iter_rows(min_row=2):
        score_cell=row[5].value or "0%"
        score=int(str(score_cell).replace("%",""))


        if score>=70:
            fill=green_fill
        elif score >=50:
            fill=yellow_fill
        else:
            fill=red_fill 

        for cell in row:
            cell.fill=fill
            cell.border=border
            cell.alignment=Alignment(
                horizontal="left",
                vertical="center",
                wrap_text=True

            )

    for col in ws.columns:
        max_len=0
        col_letter=col[0].column_letter
        for cell in col:
            if cell.value:
                max_len=max(max_len,len(str(cell.value)))
        ws.column_dimensions[col_letter].width=min(max_len+4,40)

    ws.freeze_panes="A2"

    from openpyxl.worksheet.datavalidation import DataValidation

    dv=DataValidation(
        type="list",
        formula1='"Pending,Applied,Interview,Rejected,Offer"',
        allow_blank=True 
    )
    ws.add_data_validation(dv)

    for row_num in range(2,len(log)+2):
        dv.add(ws[f"J{row_num}"])

    wb.save(path)
    print(f"Excel Saved : {path}")
    return path

st.title("🤖 AI Job Search Assistant")
st.caption("Powered by CrewAI + OpenRouter — finds, matches & applies for jobs automatically")
st.divider()

sidebar,main=st.columns([1,3],gap="large")

with sidebar:
    st.subheader("⚙️ Setup")
    st.markdown("** Upload your CV **")
    uploaded = st.file_uploader(
        "PDF or LaTeX (.tex)",
        type=["pdf", "tex"],
        label_visibility="collapsed"
    )
    if uploaded:
        suffix=".tex" if uploaded.name.endswith(".tex") else ".pdf"
        with tempfile.NamedTemporaryFile(
            delete=False,suffix=suffix 
        ) as tmp:
            tmp.write(uploaded.read())
            tmp_path=tmp.name 

        cv_text,latex_content=load_cv(
            pdf_path=tmp_path if suffix == ".pdf" else None,
            tex_path=tmp_path if suffix == ".tex" else None 
        )
        st.session_state.cv_text=cv_text
        st.session_state.latex_content=latex_content
        st.success(f"✅ {uploaded.name}")

        with st.expander(" Preview"):
            preview=(latex_content or cv_text or "")[:400]
            st.text(preview + "...")

    st.divider()

    st.markdown("** Your Name **")
    name=st.text_input(
        "name",
        placeholder="e.g Chitransh Panwar",
        label_visibility="collapsed"
    )
    if name:
        st.session_state.candidate_name=name 

    st.divider()

    st.markdown("** Mode **")
    mode=st.radio(
        "mode",
        ["Manual","Auto Pilot"],
        label_visibility="collapsed",
        horizontal=True
    )
    st.markdown("**Min match Score")
    min_score=st.slider(
        "min_score",
        min_value=10,
        max_value=90,
        value=60,
        step=5,
        label_visibility="collapsed",
        format="%d%%" 
    )
    st.session_state.min_score=min_score
    st.divider()

    st.markdown("Max job age(days)")
    max_days=st.slider(
        "max_days",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
        label_visibility="collapsed",
        format="%d days"
    )
    st.session_state.max_days=max_days
    st.divider()

    st.markdown("**Session Stats**")
    c1,c2=st.columns(2)
    c1.metric("Job Found",len(st.session_state.jobs))
    c2.metric("Matched",len(st.session_state.matched_jobs))
    c1.metric("Processed",st.session_state.Processed_count)
    c2.metric("cvs Generated",len(st.session_state.log))


with main:
    tab1,tab2,tab3=st.tabs([
        "Search Jobs",
        "Shortlisted Jobs",
        "Results"
    ])

    with tab1:
        st.subheader("Find Jobs")
        col1,col2=st.columns(2)
        with col1:
            role=st.text_input(
                "Job Role",
                placeholder="e.g Python Developer"
            )
        with col2:
            location=st.text_input(
                "Location",
                placeholder="e.g. India ,Bangalore"
            )
        num_per_platform=st.slider(
            "Jobs per platform",
            min_value=1,
            max_value=30,
            value=50,
            step=1
        )

        if st.button("Search Jobs",use_container_width=True):
            if not role:
                st.warning("Please enter a role ")
            elif not st.session_state.cv_text and \
                not st.session_state.latex_content:
                st.warning("Please Upload your CV ")
            else:
                with st.spinner("fetching jobs from all platform..."):
                    jobs=fetch_all_jobs(
                        role=role,
                        location=location,
                        num_results=num_per_platform
                    )
                    jobs=filter_jobs_by_date(jobs,max_days=st.session_state.max_days)
                    st.session_state.jobs=jobs

                with st.spinner("Scoring Jobs against your CV..."):
                    scored_jobs=[]
                    for job in jobs:
                        score=estimate_match_score(
                            job,st.session_state.cv_text,st.session_state.latex_content
                        )
                        job["match_score"]=score
                        scored_jobs.append(job)

                    scored_jobs.sort(
                        key=lambda x : x["match_score"],
                        reverse=True
                    )

                    matched=[
                        j for j in scored_jobs
                        if j["match_score"] >= st.session_state.min_score
                    ][:50]

                    st.session_state.matched_jobs=matched
                    st.session_state.jobs=scored_jobs

                st.success(
                    f"Found {len(jobs)} jobs - "
                    f"{len(matched)} match your profile "
                )
        if st.session_state.jobs:
            st.divider()
            st.subheader(f" All Fetched Jobs ({len(st.session_state.jobs)})")
            for job in st.session_state.jobs:
                score=job.get("match_score",0)
                if score>=70:
                    score_color="match-High",
                    emoji="🟢"
                elif score>=50:
                    score_color="match-mid"
                    color="🟡"
                else:
                    score_color="match-low"
                    emoji="🔴"

                days_ago = job.get("days_ago", "Unknown")
                days_str = f"{days_ago}d ago" if isinstance(days_ago, int) \
                            else "Date unknown"

                with st.expander(
                    f"{emoji} {job['title']} @ {job['company']} "
                    f"— {score}% match | {job['source']} | 📅 {days_str}"
                ):
                    c1,c2,c3=st.columns(3)
                    c1.markdown(f"**Company:** {job['company']}")
                    c2.markdown(f"**Location:** {job['location']}")
                    c3.markdown(
                        f"**Match:**"
                        f"<span class='{score_color}'>{score}%</span>",
                        unsafe_allow_html=True
                    )

                    st.markdown(f"**Description:**")
                    st.caption(job.get("description","N/A")[:400])
                    st.markdown(f"[View Job]({job.get('url','#')})")
    with tab2:
        st.subheader(
            f"📋 Shortlisted Jobs ({len(st.session_state.matched_jobs)})"
        )

        if not st.session_state.matched_jobs:
            st.info("🔍 Search for jobs first to see shortlisted matches!")
        else:
            st.caption(
                f"These {len(st.session_state.matched_jobs)} jobs "
                f"match your CV with {st.session_state.min_score}%+ score"
            )

            # Remove jobs option
            st.markdown("**Remove any jobs you don't want:**")
            jobs_to_remove = []
            for i, job in enumerate(st.session_state.matched_jobs):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f"**{i+1}.** {job['title']} @ "
                        f"{job['company']} — "
                        f"🟢 {job['match_score']}%"
                    )
                with col2:
                    if st.button("❌ Remove", key=f"remove_{i}"):
                        jobs_to_remove.append(i)

            # Remove selected jobs
            if jobs_to_remove:
                st.session_state.matched_jobs = [
                    j for i, j in
                    enumerate(st.session_state.matched_jobs)
                    if i not in jobs_to_remove
                ]
                st.rerun()

            st.divider()

            # Generate Applications Button
            if not st.session_state.candidate_name:
                st.warning("⚠️ Please enter your name in the sidebar!")
            else:
                total = len(st.session_state.matched_jobs)
                st.markdown(
                    f"**Ready to generate {total} applications?**"
                )
                st.caption(
                    "This will create an optimized CV and "
                    "outreach messages for each job"
                )

                if st.button(
                    f"⚡ Generate {total} Applications",
                    use_container_width=True,
                    type="primary"
                ):
                    st.session_state.processing = True
                    st.session_state.log = []
                    st.session_state.results = {}
                    st.session_state.Processed_count = 0

                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_placeholder = st.empty()

                    for i, job in enumerate(
                        st.session_state.matched_jobs
                    ):
                        status_text.markdown(
                            f"⚙️ Processing **{job['title']}** "
                            f"@ **{job['company']}** "
                            f"({i+1}/{total})..."
                        )

                        try:
                            result = run_crew_for_jobs(
                                job=job,
                                cv_text=st.session_state.cv_text,
                                latex_content=st.session_state.latex_content,
                                candidate_name=st.session_state.candidate_name,
                                job_index=i+1
                            )

                            # Log entry
                            log_entry = {
                                "№": i+1,
                                "Company": job["company"],
                                "Role": job["title"],
                                "Location": job["location"],
                                "Source": job["source"],
                                "Match Score": f"{job['match_score']}%",
                                "URL": job.get("url", "N/A"),
                                "CV File": result["pdf_path"] or "Compile Failed",
                                "Messages File": result["msg_path"],
                                "Status": "Pending",
                                "Date": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                )
                            }
                            st.session_state.log.append(log_entry)
                            st.session_state.results[i] = result
                            st.session_state.Processed_count += 1

                        except Exception as e:
                            st.warning(
                                f"⚠️ Failed for {job['company']}: {e}"
                            )

                        # Update progress
                        progress_bar.progress((i+1) / total)

                    # Save Excel
                    save_excel_log(st.session_state.log)

                    status_text.markdown("✅ All applications generated!")
                    st.session_state.processing = False
                    st.success(
                        f"🎉 Done! Generated "
                        f"{st.session_state.Processed_count} applications!"
                    )
                    st.balloons()

    # ─────────────────────────────────────────
    # TAB 3: RESULTS
    # ─────────────────────────────────────────
    with tab3:
        st.subheader("📦 Generated Applications")

        if not st.session_state.log:
            st.info("⚡ Generate applications first to see results here!")
        else:
            # Summary metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Generated", len(st.session_state.log))
            c2.metric(
                "CVs Created",
                sum(
                    1 for r in st.session_state.results.values()
                    if r.get("pdf_path")
                )
            )
            c3.metric(
                "Messages Created",
                sum(
                    1 for r in st.session_state.results.values()
                    if r.get("msg_path")
                )
            )
            c4.metric("Status", "Ready to Apply! 🚀")

            st.divider()

            # Excel Download
            excel_path = "outputs/applications_log.xlsx"
            if os.path.exists(excel_path):
                with open(excel_path, "rb") as f:
                    st.download_button(
                        "📊 Download Excel Tracker",
                        data=f,
                        file_name="job_applications.xlsx",
                        mime="application/vnd.openxmlformats-"
                             "officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            # ZIP Download
            st.markdown("**Download All Files as ZIP:**")
            if st.button(
                "📦 Create & Download ZIP",
                use_container_width=True
            ):
                import zipfile
                zip_path = "outputs/all_applications.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for root, dirs, files in os.walk("outputs"):
                        for file in files:
                            if not file.endswith(".zip"):
                                filepath = os.path.join(root, file)
                                zipf.write(filepath)

                with open(zip_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download ZIP Now",
                        data=f,
                        file_name="all_applications.zip",
                        mime="application/zip",
                        use_container_width=True
                    )

            st.divider()

            # Individual Results
            st.subheader("📋 Individual Applications")
            for i, log in enumerate(st.session_state.log):
                result = st.session_state.results.get(i, {})
                with st.expander(
                    f"**{log['№']}.** {log['Role']} @ "
                    f"{log['Company']} — {log['Match Score']}"
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Location:** {log['Location']}")
                    c2.markdown(f"**Source:** {log['Source']}")
                    c3.markdown(f"**Date:** {log['Date']}")
                    st.markdown(f"🔗 [View Job]({log['URL']})")

                    # Show messages
                    if result.get("msg_path") and \
                       os.path.exists(result["msg_path"]):
                        with open(result["msg_path"]) as f:
                            messages = f.read()
                        st.markdown("**📬 Outreach Messages:**")
                        st.text_area(
                            "messages",
                            messages[:1000],
                            height=150,
                            label_visibility="collapsed",
                            key=f"msg_{i}"
                        )

                    # Download CV PDF
                    if result.get("pdf_path") and \
                       os.path.exists(result["pdf_path"]):
                        with open(result["pdf_path"], "rb") as f:
                            st.download_button(
                                f"📄 Download CV PDF",
                                data=f,
                                file_name=f"cv_{log['Company']}.pdf",
                                mime="application/pdf",
                                key=f"pdf_{i}"
                            )
                    else:
                        # Offer LaTeX if PDF failed
                        if result.get("tex_path") and \
                           os.path.exists(result["tex_path"]):
                            with open(result["tex_path"]) as f:
                                st.download_button(
                                    "📝 Download LaTeX (PDF failed)",
                                    data=f,
                                    file_name=f"cv_{log['Company']}.tex",
                                    key=f"tex_{i}"
                                )

