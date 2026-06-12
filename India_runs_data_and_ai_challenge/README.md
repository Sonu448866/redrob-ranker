# Redrob AI — Intelligent Candidate Ranking System

**Team:** AIRankers | Adithya Maurya & Sonu Kumar  
**Challenge:** Intelligent Candidate Discovery & Ranking  
**Role Ranked For:** Senior AI Engineer (Founding Team) at Redrob AI

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Rank all 100K candidates
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv

# Test on sample data
python rank.py --candidates ./data/sample_candidates.json --out ./test_output.csv

# Validate output
python data/validate_submission.py submission.csv
```

## 🏗️ Architecture

Our system is a **multi-stage hybrid ranker** that avoids keyword matching and instead reasons about the full candidate picture — exactly as the JD describes.

```
candidates.jsonl (100K)
       │
  ┌────▼────────────────────────────────────────────────┐
  │  Stage 1: Honeypot Detection                         │
  │  • Overlapping jobs • Expert skill / 0 months usage │
  │  • Career months >> years_of_experience             │
  └────┬────────────────────────────────────────────────┘
       │
  ┌────▼────────────────────────────────────────────────┐
  │  Stage 2: 5-Component Structured Scoring            │
  │  Skills (30%) + Career (25%) + Experience (20%)     │
  │  + Location (15%) + Education (10%)                 │
  └────┬────────────────────────────────────────────────┘
       │
  ┌────▼────────────────────────────────────────────────┐
  │  Stage 3: Behavioral Signal Modifier (×0.35–1.15)   │
  │  open_to_work, recency, response_rate, notice,      │
  │  interview_rate, github_activity, completeness…     │
  └────┬────────────────────────────────────────────────┘
       │
  ┌────▼────────────────────────────────────────────────┐
  │  Stage 4: TF-IDF Semantic Boost (+0–10%)            │
  │  Career text cosine similarity vs JD                │
  └────┬────────────────────────────────────────────────┘
       │
  ┌────▼────────────────────────────────────────────────┐
  │  Stage 5: Sort → Top 100 → Generate Reasoning       │
  └────────────────────────────────────────────────────┘
```

## 📊 Scoring Components

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| **Skills Match** | 30% | Alignment with JD-critical skills (embeddings, vector DBs, Python, ranking eval), weighted by proficiency × duration × endorsements |
| **Career Trajectory** | 25% | Title relevance, company type (product vs consulting), role description ML-density, career progression |
| **Experience Validity** | 20% | Optimal 6-8 yr range, penalises pure research and LangChain-only backgrounds |
| **Location/Availability** | 15% | Pune/Noida preferred, India cities acceptable, relocation bonus |
| **Education** | 10% | Institution tier (tier_1–tier_4), field relevance (CS/EE/Math/AI), degree level |

### Behavioral Modifier (Multiplicative)
Combines 10 platform signals: `open_to_work_flag`, `last_active_date`, `recruiter_response_rate`, `avg_response_time_hours`, `interview_completion_rate`, `notice_period_days`, `github_activity_score`, `profile_completeness_score`, `verified_email`, `verified_phone`.

## 🎯 Key Design Decisions

### Why Not Keyword Matching?
The JD explicitly warns: *"The right answer is not 'find candidates whose skills section contains the most AI keywords.'"* Our career trajectory scorer looks at **what candidates actually did** — their role descriptions, company types, and career arc — not just what skills they listed.

### Anti-Keyword-Stuffing
A candidate claiming "expert" proficiency in FAISS with `duration_months = 0` gets a 92% penalty on that skill. Skills must be backed by actual usage time.

### Consulting-Firm Detection
The JD explicitly disqualifies candidates whose entire career is at TCS, Infosys, Wipro, Accenture, Cognizant, etc. Our career scorer detects consulting-ratio and applies a heavy penalty for >85% consulting history.

### Honeypot Avoidance
We detect impossible profiles using logical consistency checks:
- Expert skills with zero usage months
- Overlapping full-time employment periods
- Career duration wildly exceeding stated years of experience

### Behavioral Signals as Availability Filter
A great profile that hasn't been active for 6+ months and has a 5% recruiter response rate is "not actually available" per the JD. Our behavioral modifier handles this correctly without making it the primary signal.

## 📁 Project Structure

```
├── rank.py                    # CLI entry point
├── ranker.py                  # Core Ranker class
├── jd_config.py               # All JD-derived constants
├── reasoning.py               # Profile-specific reasoning generator
├── scorer/
│   ├── skills.py              # Skills matching + anti-stuffing
│   ├── career.py              # Career trajectory + consulting detection
│   ├── experience.py          # Experience range + research-only check
│   ├── education.py           # Institution tier + field relevance
│   ├── location.py            # Location + work mode scoring
│   ├── behavioral.py          # 10-signal behavioral modifier
│   ├── semantic.py            # TF-IDF semantic boost
│   └── honeypot.py            # Impossible profile detection
├── app.py                     # Streamlit sandbox UI
├── requirements.txt
└── submission_metadata.yaml
```

## ⚡ Performance

- **100K candidates ranked in ~60–90 seconds** on CPU (16 GB RAM)
- No GPU required, no network calls during ranking
- Memory: ~2–3 GB peak for 100K candidates

## 🔗 Links

- **Sandbox:** [Streamlit App](https://YOUR_STREAMLIT_APP.streamlit.app) ← update this
- **Team:** Adithya Maurya (adithyamaurya@25spit.ac.in) & Sonu Kumar (sonukumar25@spit.ac.in)
