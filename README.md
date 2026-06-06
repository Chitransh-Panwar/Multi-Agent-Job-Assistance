# 🤖 AI-Powered Multi-Agent Job Search System

A multi-agent AI system built with CrewAI and Streamlit that automates your job search — from fetching listings across 10 platforms to generating tailored CVs and outreach messages.

Live Demo-https://job-search-agent-production-ab74.up.railway.app/

---

## 📸 Screenshots

<img width="1456" height="877" alt="Screenshot 2026-06-06 at 11 45 33 AM" src="https://github.com/user-attachments/assets/8c6cb504-81d4-4d63-a1ae-8fdd265cbb32" />
<img width="1465" height="896" alt="Screenshot 2026-06-06 at 11 36 05 AM" src="https://github.com/user-attachments/assets/727a34b9-014f-4488-877f-316559e4d710" />
<img width="1055" height="863" alt="Screenshot 2026-06-06 at 1 51 52 PM" src="https://github.com/user-attachments/assets/34b6e41b-e31b-4324-8146-7a8535ba27c1" /><img width="1689" height="631" alt="Screenshot 2026-06-06 at 1 52 45 PM" src="https://github.com/user-attachments/assets/4d3bf2c0-85cb-4509-8cec-0c765b9f280d" />


---

## 🧠 How It Works

```
Upload Your CV (PDF or LaTeX)
          │
          ▼
  Select Job Sources
  (7 APIs + 3 Scrapers)
          │
          ▼
   Fetch Job Listings
          │
          ▼
  Score Jobs Against CV
  (Keyword Match %)
          │
          ▼
  Filter by Date & Score
          │
          ▼
  ┌───────────────────────┐
  │     CrewAI Pipeline   │
  │                       │
  │  Agent 1: Analyzer    │
  │  Agent 2: CV Optimizer│
  │  Agent 3: Messaging   │
  └───────────────────────┘
          │
          ▼
  Outputs per Job:
  ├── Optimized CV (LaTeX/PDF)
  ├── Outreach Messages
  └── Excel Tracker
```

---

## ✨ Features

- 🔍 **10 Job Sources** — 7 REST APIs + 3 web scrapers
- 🧠 **3 AI Agents** — Job Analyzer, CV Optimizer, Messaging Agent
- 📄 **Smart CV Optimization** — Updates only relevant sections, preserves original formatting
- 💬 **Outreach Messages** — LinkedIn message, cold email, follow-up per job
- 📊 **Excel Tracker** — Color-coded match scores, status dropdown
- 📅 **Date Filter** — Only show jobs posted within 1–30 days
- 🎯 **Match Score Filter** — Filter jobs by CV keyword match %
- 📦 **ZIP Download** — Download all CVs + messages + Excel in one click
- 🌐 **Streamlit UI** — Clean web interface with real-time progress

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **AI Framework** | CrewAI 0.41.1 |
| **LLM** | OpenRouter (GPT-4.1 mini) |
| **Web UI** | Streamlit |
| **Web Scraping** | Playwright |
| **PDF Parsing** | PyMuPDF |
| **PDF Compilation** | TinyTeX + pdflatex |
| **Data** | Pandas + OpenPyXL |
| **APIs** | LangChain + Groq |
| **Environment** | Python 3.11 |

---

## 📡 Job Sources

### APIs
| Platform | Coverage |
|----------|---------|
| Adzuna | India |
| JSearch (RapidAPI) | LinkedIn + Indeed |
| The Muse | Global + Remote |
| USAJobs | US Government |
| Arbeitnow | Europe + Remote |
| Findwork | Tech Jobs |
| Jooble | Global |

### Web Scrapers
| Platform | Method | Coverage |
|----------|--------|---------|
| Internshala | Playwright | India |
| WeWorkRemotely | RSS Feed | Remote |
| Remotive | Public API | Remote |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11
- TinyTeX (for PDF compilation)
- Git

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/job-search-agent
cd job-search-agent

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Install TinyTeX (for PDF compilation)
wget -qO- https://yihui.org/tinytex/install-bin-unix.sh | sh
```

### Configuration

Create a `.env` file in the project root:
```env
# LLM
OPENROUTER_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# Job APIs
ADZUNA_APP_ID=your_id_here
ADZUNA_APP_KEY=your_key_here
RAPIDAPI_KEY=your_key_here
MUSE_API_KEY=your_key_here
USAJOBS_API_KEY=your_key_here
USAJOBS_USER_AGENT=your_email_here
FINDWORK_API_KEY=your_key_here
JOOBLE_API_KEY=your_key_here
```

### Run

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
job_search_agent/
├── app.py          # Streamlit web interface
├── agents.py       # CrewAI agent definitions
├── tasks.py        # Agent task definitions
├── tools.py        # Job fetchers + CV parser
├── main.py         # CLI runner + PDF compiler
├── requirements.txt
├── .env            # API keys (never commit!)
└── outputs/
    ├── pdffiles/   # Compiled PDF CVs
    ├── texfiles/   # LaTeX source files
    ├── messages/   # Outreach messages
    └── tracker/    # Excel application log
```

---

## 🚀 How To Use

### Step 1 — Upload Your CV
Upload your CV in PDF or LaTeX format (Overleaf export recommended)

### Step 2 — Configure Settings
- Enter your name
- Set minimum match score (0–100%)
- Set maximum job age (1–30 days)
- Select job sources

### Step 3 — Search Jobs
Enter your target role and location, click **Search Jobs**

### Step 4 — Review Shortlisted Jobs
Review matched jobs, remove any you don't want

### Step 5 — Generate Applications
Click **Generate Applications** — AI agents will:
- Analyze each job description
- Optimize your CV for that specific role
- Write personalized outreach messages

### Step 6 — Download
- Download individual CVs and messages
- Download Excel tracker
- Download everything as ZIP

> _Add screenshots here_

---

## ⚠️ Limitations & Drawbacks

### Cloud Deployment
- **PDF compilation not available on cloud** — TinyTeX requires a local environment. On cloud deployments only LaTeX and messages are generated. PDF can be compiled locally or via Overleaf.

### Scraper Reliability
- **Wellfound** — blocked by CAPTCHA, not supported
- **Naukri** — HTML structure changes frequently, may break
- **Glassdoor** — bot detection, not supported
- **LinkedIn** — not supported due to strict bot detection and ToS

### AI Quality
- CV optimization quality depends on how detailed your original CV is
- Match scoring is keyword-based, not semantic — may miss contextually relevant jobs
- Outreach messages may need manual review before sending

### Rate Limits
- OpenRouter free tier has token limits — processing 50 jobs may hit limits
- Some APIs have daily request caps on free tier

### Performance
- Processing 50 jobs takes 30–60 minutes depending on LLM response time
- Playwright scrapers add 5–10 seconds per source

---

## 🔮 Future Improvements

- [ ] Semantic job matching using embeddings
- [ ] Auto form-filling with Selenium
- [ ] Email follow-up scheduler
- [ ] LinkedIn scraping with session cookies
- [ ] Application success rate tracker
- [ ] Support for multiple CV templates
- [ ] Docker deployment with TinyTeX

---

## 📄 License

MIT License — free to use and modify

---

## 🙏 Acknowledgements

- [CrewAI](https://crewai.com) — Multi-agent framework
- [OpenRouter](https://openrouter.ai) — LLM API gateway
- [Streamlit](https://streamlit.io) — Web interface
- [Playwright](https://playwright.dev) — Browser automation
- [TinyTeX](https://yihui.org/tinytex) — LaTeX compiler

---

> Built with ❤️ to automate the most tedious part of job hunting
