"""
jd_config.py
------------
All constants extracted from the Job Description for
"Senior AI Engineer — Founding Team" at Redrob AI.

The goal is to centralise every JD-derived signal here so that
changes to the JD (or tuning experiments) only require edits in
one place.
"""

# ---------------------------------------------------------------------------
# Role metadata
# ---------------------------------------------------------------------------
JD_TITLE = "Senior AI Engineer"
COMPANY = "Redrob AI"
PREFERRED_LOCATIONS = {"pune", "noida"}
ACCEPTABLE_LOCATIONS = {
    "hyderabad", "mumbai", "delhi", "delhi ncr", "gurugram", "gurgaon",
    "bengaluru", "bangalore", "chennai", "kolkata", "ahmedabad",
}
EXP_MIN = 5
EXP_MAX = 9
EXP_SWEET_SPOT_MIN = 6
EXP_SWEET_SPOT_MAX = 8

# ---------------------------------------------------------------------------
# JD full text — used for TF-IDF semantic matching
# ---------------------------------------------------------------------------
JD_TEXT = """
Senior AI Engineer Founding Team Redrob AI Series A AI-native talent intelligence platform.
Pune Noida India Hybrid.

The high-level mandate: own the intelligence layer of Redrob's product.
Ranking retrieval matching systems embedding hybrid search vector database candidate job matching.

Weeks 1-3: Audit BM25 rule-based scoring. Identify highest-leverage improvements.
Weeks 4-8: Ship v2 ranking system with embeddings hybrid retrieval LLM-based re-ranking.
Weeks 9-12: Evaluation infrastructure offline benchmarks online A/B testing recruiter-feedback loops.

Things you absolutely need:
Production experience with embeddings-based retrieval systems sentence-transformers OpenAI embeddings BGE E5.
Embedding drift index refresh retrieval-quality regression in production.
Production experience with vector databases hybrid search infrastructure Pinecone Weaviate Qdrant Milvus 
OpenSearch Elasticsearch FAISS.
Strong Python code quality.
Hands-on experience designing evaluation frameworks for ranking systems NDCG MRR MAP 
offline-to-online correlation A/B test interpretation.

Things nice to have:
LLM fine-tuning LoRA QLoRA PEFT.
Learning-to-rank models XGBoost-based or neural.
HR-tech recruiting tech marketplace products.
Distributed systems large-scale inference optimization.
Open-source contributions AI ML space.

Ideal candidate profile:
6-8 years total experience 4-5 years applied ML AI roles product companies.
Shipped end-to-end ranking search recommendation system real users meaningful scale.
Strong opinions retrieval hybrid dense evaluation offline online LLM integration fine-tune prompt.
Located Noida Pune or willing to relocate.
Active platform job market.
NLP information retrieval search ranking recommendation systems production.
"""

# ---------------------------------------------------------------------------
# REQUIRED skills — mapped to skill name patterns (case-insensitive substrings)
# ---------------------------------------------------------------------------
# Format: { group_name: (weight, [keyword_patterns]) }
# Weight = how important this skill group is to the JD
REQUIRED_SKILL_GROUPS = {
    "embeddings_retrieval": (
        1.0,
        [
            "sentence-transformer", "sentence transformer", "sbert",
            "bge", "e5", "openai embedding", "text embedding",
            "dense retrieval", "bi-encoder", "cross-encoder",
            "semantic search", "semantic similarity", "embedding",
            "vector search", "vector retrieval", "neural retrieval",
            "faiss", "ann search", "approximate nearest neighbour",
            "approximate nearest neighbor",
        ],
    ),
    "vector_databases": (
        0.9,
        [
            "pinecone", "weaviate", "qdrant", "milvus", "chroma",
            "opensearch", "elasticsearch", "faiss", "annoy", "hnswlib",
            "vespa", "typesense", "vector database", "vector db",
            "hybrid search", "bm25", "inverted index",
        ],
    ),
    "python": (
        0.8,
        [
            "python", "pyspark", "pandas", "numpy", "scikit-learn",
            "sklearn", "fastapi", "flask", "django",
        ],
    ),
    "ranking_evaluation": (
        0.9,
        [
            "ndcg", "mrr", "map", "mean average precision",
            "learning to rank", "ltr", "ranking", "retrieval evaluation",
            "a/b test", "ab test", "offline evaluation", "online evaluation",
            "precision@k", "recall@k",
        ],
    ),
    "ml_production": (
        0.85,
        [
            "production ml", "mlops", "model serving", "model deployment",
            "ml pipeline", "feature store", "model monitoring",
            "recommendation system", "recommender", "search system",
            "information retrieval", "ir system", "nlp production",
            "pytorch", "tensorflow", "jax", "triton", "onnx",
            "kubeflow", "airflow", "mlflow", "ray",
        ],
    ),
    "nlp_ir": (
        0.8,
        [
            "nlp", "natural language processing", "information retrieval",
            "text classification", "named entity", "question answering",
            "transformers", "bert", "roberta", "gpt", "llm",
            "language model", "hugging face", "huggingface",
            "tokenizer", "text mining",
        ],
    ),
}

# ---------------------------------------------------------------------------
# NICE-TO-HAVE skills
# ---------------------------------------------------------------------------
NICE_TO_HAVE_SKILL_GROUPS = {
    "llm_finetuning": (
        0.6,
        [
            "lora", "qlora", "peft", "fine-tuning", "fine tuning",
            "finetuning", "instruction tuning", "rlhf", "dpo",
        ],
    ),
    "learning_to_rank": (
        0.55,
        [
            "xgboost", "lightgbm", "catboost", "learning to rank",
            "ranknet", "lambdamart", "listwise", "pairwise ranking",
        ],
    ),
    "open_source": (
        0.5,
        [
            "open source", "github", "contributor", "open-source",
            "hugging face contributor", "arxiv", "paper",
        ],
    ),
    "distributed_systems": (
        0.45,
        [
            "distributed", "spark", "kafka", "kubernetes", "docker",
            "microservices", "redis", "cassandra", "grpc",
        ],
    ),
    "hr_tech": (
        0.4,
        [
            "hr tech", "hrtech", "ats", "applicant tracking",
            "recruiting", "talent acquisition", "marketplace",
        ],
    ),
}

# ---------------------------------------------------------------------------
# DISQUALIFIER patterns — if these patterns dominate the career, apply penalty
# ---------------------------------------------------------------------------
CONSULTING_FIRMS = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl", "hcl technologies", "tech mahindra", "mphasis",
    "hexaware", "mindtree", "ltimindtree", "lti", "persistent", "niit",
    "zensar", "cyient", "mastech", "l&t infotech", "ltts",
}

DISQUALIFIER_TITLES = {
    "marketing manager", "hr manager", "content writer", "graphic designer",
    "accountant", "sales executive", "civil engineer", "mechanical engineer",
    "customer support", "project manager",  # non-AI project manager
}

# Titles that are explicitly relevant to the JD
RELEVANT_TITLES = {
    "ai engineer", "ml engineer", "machine learning engineer",
    "senior ai engineer", "senior ml engineer", "data scientist",
    "research scientist", "applied scientist", "nlp engineer",
    "search engineer", "recommendation engineer", "ranking engineer",
    "software engineer", "backend engineer", "full stack",
    "deep learning engineer", "computer vision engineer",
    "data engineer",  # adjacent, partial credit
    "llm engineer", "generative ai", "genai engineer",
}

# Career description keywords that indicate production ML/search work
PRODUCTION_ML_KEYWORDS = [
    "retrieval", "ranking", "search", "recommendation", "embedding",
    "vector", "similarity", "indexing", "deployed", "production",
    "real users", "serving", "inference", "model", "training",
    "pipeline", "nlp", "language model", "llm", "fine-tuning",
    "evaluation", "a/b test", "benchmark", "metrics",
]

# ---------------------------------------------------------------------------
# Field of study relevance for education
# ---------------------------------------------------------------------------
HIGH_RELEVANCE_FIELDS = {
    "computer science", "cs", "computer engineering", "ce",
    "artificial intelligence", "ai", "machine learning", "ml",
    "data science", "information technology", "it",
    "electrical engineering", "electronics", "ece",
    "mathematics", "statistics", "math", "applied math",
    "computational linguistics", "natural language processing",
    "information systems", "software engineering",
}

# ---------------------------------------------------------------------------
# Scoring weights (must sum to 1.0)
# ---------------------------------------------------------------------------
COMPONENT_WEIGHTS = {
    "skills": 0.30,
    "career": 0.25,
    "experience": 0.20,
    "location": 0.15,
    "education": 0.10,
}

# Behavioral modifier range
BEHAVIORAL_MIN = 0.35
BEHAVIORAL_MAX = 1.15
