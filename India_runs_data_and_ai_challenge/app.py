"""
app.py
------
Streamlit sandbox UI for the Redrob Intelligent Candidate Ranking System.
Fulfils the submission requirement for a hosted sandbox (Section 10.5).

Features:
  - Upload a small candidate JSON/JSONL file (≤100 candidates)
  - Run the full ranker pipeline
  - Display ranked results with score breakdown
  - Download the submission CSV

Deploy to Streamlit Community Cloud (free):
  1. Push this repo to GitHub
  2. Go to share.streamlit.io → New app → select repo → app.py
  3. Done — free hosting, no GPU needed
"""

import json
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

# ---- Page config --------------------------------------------------------
st.set_page_config(
    page_title="Redrob AI Candidate Ranker",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }

    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #a78bfa, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .main-header p {
        color: #94a3b8;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }

    .metric-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border: 1px solid #4f46e5;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        color: white;
    }

    .score-badge-high {
        background: linear-gradient(135deg, #065f46, #059669);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .score-badge-mid {
        background: linear-gradient(135deg, #92400e, #d97706);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .score-badge-low {
        background: linear-gradient(135deg, #7f1d1d, #dc2626);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .stDataFrame {
        border-radius: 12px;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #4f46e5;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Header -------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>🤖 Redrob AI — Intelligent Candidate Ranker</h1>
        <p>Senior AI Engineer (Founding Team) · Semantic + Behavioral + Structural scoring</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- Sidebar ------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📋 About This System")
    st.markdown(
        """
        This ranker evaluates candidates for the **Senior AI Engineer** role
        using a 5-component hybrid scoring model:
        
        | Component | Weight |
        |-----------|--------|
        | 🛠️ Skills Match | 30% |
        | 📈 Career Trajectory | 25% |
        | ⏱️ Experience Validity | 20% |
        | 📍 Location/Availability | 15% |
        | 🎓 Education | 10% |
        
        Plus a **Behavioral Signal Modifier** (×0.35–1.15) based on
        platform activity, response rate, and notice period.
        """
    )
    st.divider()
    st.markdown("### ⚙️ Scoring Logic")
    st.markdown(
        """
        - **Anti-stuffing**: Expert skills with 0 months usage → penalised
        - **Honeypot detection**: Impossible profiles → score capped at ~0
        - **Consulting filter**: TCS/Infosys/Wipro-only careers → 92% penalty
        - **Semantic boost**: TF-IDF career text vs JD → up to +10%
        """
    )

# ---- Main content -------------------------------------------------------
st.markdown("### 📂 Upload Candidate Data")
st.info(
    "Upload a JSON or JSONL file containing up to 100 candidate profiles. "
    "The file must match the Redrob candidate schema. "
    "The bundled `sample_candidates.json` is a valid test file.",
    icon="ℹ️",
)

col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader(
        "Choose a candidate file",
        type=["json", "jsonl"],
        help="Upload sample_candidates.json or any valid JSONL file",
    )

with col2:
    top_k = st.number_input(
        "Top K candidates",
        min_value=1,
        max_value=100,
        value=10,
        help="Number of top candidates to show",
    )

# ---- Run ranking --------------------------------------------------------
if uploaded_file is not None:
    with st.spinner("Parsing candidate data…"):
        content = uploaded_file.read().decode("utf-8")
        if uploaded_file.name.endswith(".jsonl"):
            candidates = [json.loads(line) for line in content.splitlines() if line.strip()]
        else:
            data = json.loads(content)
            candidates = data if isinstance(data, list) else [data]

    st.success(f"✅ Loaded **{len(candidates)}** candidates from `{uploaded_file.name}`")

    if st.button("🚀 Run Ranking Pipeline", type="primary", use_container_width=True):
        with st.spinner("Running scoring pipeline… (this may take a few seconds)"):
            # Write to temp JSONL for the ranker
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
            ) as tmp:
                for c in candidates:
                    tmp.write(json.dumps(c) + "\n")
                tmp_path = tmp.name

            # Run ranker
            try:
                import sys, os
                sys.path.insert(0, os.path.dirname(__file__))
                from ranker import Ranker

                ranker = Ranker(top_k=min(top_k, len(candidates)), verbose=False)
                results = ranker.rank(tmp_path)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        st.markdown("---")
        st.markdown(f"## 🏆 Top {len(results)} Ranked Candidates")

        # ---- Summary metrics
        mcols = st.columns(4)
        with mcols[0]:
            st.metric("Total Candidates", len(candidates))
        with mcols[1]:
            honeypots = sum(1 for r in results if r.get("is_honeypot"))
            st.metric("Honeypots Detected", honeypots, delta="filtered out", delta_color="inverse")
        with mcols[2]:
            top_score = results[0]["final_score"] if results else 0
            st.metric("Top Score", f"{top_score:.4f}")
        with mcols[3]:
            avg_score = sum(r["final_score"] for r in results) / len(results) if results else 0
            st.metric("Avg Score (top-k)", f"{avg_score:.4f}")

        # ---- Results table
        table_data = []
        for r in results:
            p = r["candidate"].get("profile", {})
            sigs = r["candidate"].get("redrob_signals", {})
            table_data.append({
                "Rank": r["rank"],
                "Candidate ID": r["candidate_id"],
                "Title": p.get("current_title", "?"),
                "Location": p.get("location", "?"),
                "YoE": p.get("years_of_experience", 0),
                "Final Score": round(r["final_score"], 4),
                "Skills": round(r["skills_score"], 3),
                "Career": round(r["career_score"], 3),
                "Experience": round(r["experience_score"], 3),
                "Behavioral": round(r["behavioral_modifier"], 3),
                "Open to Work": "✅" if sigs.get("open_to_work_flag") else "❌",
            })

        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Final Score": st.column_config.ProgressColumn(
                    "Final Score", min_value=0, max_value=1, format="%.4f"
                ),
                "Skills": st.column_config.ProgressColumn(
                    "Skills", min_value=0, max_value=1, format="%.3f"
                ),
                "Career": st.column_config.ProgressColumn(
                    "Career", min_value=0, max_value=1, format="%.3f"
                ),
            },
        )

        # ---- Expandable candidate details
        st.markdown("### 🔍 Candidate Details")
        for r in results[:min(5, len(results))]:
            p = r["candidate"].get("profile", {})
            sigs = r["candidate"].get("redrob_signals", {})
            score_color = "🟢" if r["final_score"] > 0.6 else "🟡" if r["final_score"] > 0.4 else "🔴"

            with st.expander(
                f"{score_color} #{r['rank']} — {r['candidate_id']} | "
                f"{p.get('current_title','?')} | Score: {r['final_score']:.4f}"
            ):
                dcol1, dcol2 = st.columns(2)
                with dcol1:
                    st.markdown("**📋 Profile**")
                    st.markdown(f"- **Title:** {p.get('current_title', '?')}")
                    st.markdown(f"- **Company:** {p.get('current_company', '?')}")
                    st.markdown(f"- **Location:** {p.get('location', '?')}, {p.get('country', '?')}")
                    st.markdown(f"- **Experience:** {p.get('years_of_experience', 0)} years")
                    st.markdown(f"- **Industry:** {p.get('current_industry', '?')}")

                    st.markdown("**🛠️ Top Skills**")
                    skills = sorted(
                        r["candidate"].get("skills", []),
                        key=lambda s: s.get("endorsements", 0),
                        reverse=True,
                    )[:5]
                    for sk in skills:
                        st.markdown(
                            f"  - {sk['name']} ({sk.get('proficiency','?')}, "
                            f"{sk.get('endorsements',0)} endorsements)"
                        )

                with dcol2:
                    st.markdown("**📊 Scores**")
                    score_df = pd.DataFrame(
                        {
                            "Component": [
                                "Skills Match", "Career Trajectory",
                                "Experience", "Education", "Location",
                                "Behavioral Modifier", "FINAL SCORE",
                            ],
                            "Score": [
                                r["skills_score"], r["career_score"],
                                r["experience_score"], r["education_score"],
                                r["location_score"], r["behavioral_modifier"],
                                r["final_score"],
                            ],
                        }
                    )
                    st.dataframe(score_df, hide_index=True, use_container_width=True)

                    st.markdown("**💬 Behavioral Signals**")
                    st.markdown(f"- Open to Work: {'✅' if sigs.get('open_to_work_flag') else '❌'}")
                    st.markdown(f"- Response Rate: {sigs.get('recruiter_response_rate', 0):.0%}")
                    st.markdown(f"- Notice Period: {sigs.get('notice_period_days', '?')} days")
                    st.markdown(f"- GitHub Activity: {sigs.get('github_activity_score', -1)}")
                    st.markdown(f"- Last Active: {sigs.get('last_active_date', '?')}")

                st.markdown("**💡 Reasoning**")
                st.info(r.get("reasoning", "N/A"))

                if r.get("is_honeypot"):
                    st.error(f"⚠️ HONEYPOT DETECTED: {r.get('honeypot_reason', '')}")

        # ---- Download CSV
        st.markdown("---")
        st.markdown("### 📥 Download Submission CSV")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp:
            import csv
            writer = csv.writer(tmp)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for r in results:
                reasoning = r.get("reasoning", "").replace("\n", " ")
                writer.writerow([
                    r["candidate_id"],
                    r["rank"],
                    f"{r['final_score']:.4f}",
                    reasoning,
                ])
            tmp_csv_path = tmp.name

        with open(tmp_csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read()
        Path(tmp_csv_path).unlink(missing_ok=True)

        st.download_button(
            label="⬇️ Download submission.csv",
            data=csv_content,
            file_name="submission.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary",
        )

else:
    # Demo state
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; padding:3rem; color:#64748b;">
            <div style="font-size:4rem;">📋</div>
            <h3>Upload a candidate file to get started</h3>
            <p>Use the bundled <code>sample_candidates.json</code> (50 candidates) to test the system.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---- Footer -------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; color:#64748b; font-size:0.85rem;">
        <strong>Team AIRankers</strong> · Redrob Intelligent Candidate Discovery &amp; Ranking Challenge · 
        Built with Python + scikit-learn + Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
