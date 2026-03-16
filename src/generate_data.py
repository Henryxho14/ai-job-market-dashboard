"""
Synthetic Bay Area tech job postings generator.
Produces realistic data mirroring what you would collect from
LinkedIn / Indeed / Glassdoor via scraping or API.
"""

import pandas as pd
import numpy as np
import random
import json
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ── Companies & weights ──────────────────────────────────────────────────────
COMPANIES = {
    "Salesforce":    {"weight": 0.10, "avg_sal": 112, "type": "tech"},
    "Cisco":         {"weight": 0.09, "avg_sal": 105, "type": "tech"},
    "Oracle":        {"weight": 0.08, "avg_sal": 108, "type": "tech"},
    "ServiceNow":    {"weight": 0.07, "avg_sal": 118, "type": "tech"},
    "Deloitte":      {"weight": 0.09, "avg_sal": 95,  "type": "consulting"},
    "Accenture":     {"weight": 0.08, "avg_sal": 92,  "type": "consulting"},
    "PwC":           {"weight": 0.06, "avg_sal": 90,  "type": "consulting"},
    "KPMG":          {"weight": 0.05, "avg_sal": 89,  "type": "consulting"},
    "Apple":         {"weight": 0.07, "avg_sal": 130, "type": "tech"},
    "Google":        {"weight": 0.06, "avg_sal": 140, "type": "tech"},
    "Meta":          {"weight": 0.05, "avg_sal": 138, "type": "tech"},
    "Adobe":         {"weight": 0.05, "avg_sal": 115, "type": "tech"},
    "Workday":       {"weight": 0.05, "avg_sal": 110, "type": "tech"},
    "Splunk":        {"weight": 0.04, "avg_sal": 108, "type": "tech"},
    "Palo Alto Networks": {"weight": 0.04, "avg_sal": 120, "type": "tech"},
    "Wells Fargo":   {"weight": 0.03, "avg_sal": 95,  "type": "finance"},
    "JPMorgan":      {"weight": 0.04, "avg_sal": 105, "type": "finance"},
    "Kaiser Permanente": {"weight": 0.03, "avg_sal": 98, "type": "healthcare"},
    "Levi Strauss":  {"weight": 0.02, "avg_sal": 90,  "type": "retail"},
    "Chevron":       {"weight": 0.01, "avg_sal": 100, "type": "energy"},
}

ROLE_CATEGORIES = {
    "Data Analyst":              {"weight": 0.22, "base": 85},
    "Business Analyst":          {"weight": 0.18, "base": 82},
    "Data Scientist":            {"weight": 0.15, "base": 110},
    "IT Consultant":             {"weight": 0.12, "base": 90},
    "Business Intelligence Analyst": {"weight": 0.10, "base": 88},
    "Machine Learning Engineer": {"weight": 0.08, "base": 125},
    "Data Engineer":             {"weight": 0.09, "base": 115},
    "AI/ML Analyst":             {"weight": 0.06, "base": 105},
}

LOCATIONS = ["San Jose, CA", "San Francisco, CA", "Sunnyvale, CA",
             "Santa Clara, CA", "Mountain View, CA", "Palo Alto, CA",
             "Redwood City, CA", "Oakland, CA", "Fremont, CA", "Remote (Bay Area)"]

WORK_MODES = {
    "Hybrid":    0.45,
    "Remote":    0.22,
    "On-site":   0.33,
}

# ── Skills with realistic mention probabilities ──────────────────────────────
# Each tuple: (skill_name, base_probability, monthly_growth_rate)
SKILLS = [
    ("Python",              0.76, 0.005),
    ("SQL",                 0.78, 0.002),
    ("Tableau",             0.55, -0.003),
    ("Power BI",            0.42, 0.010),
    ("Excel",               0.48, -0.005),
    ("Machine Learning",    0.38, 0.008),
    ("LLM / GenAI",         0.28, 0.040),
    ("Prompt Engineering",  0.18, 0.045),
    ("RAG / Vector DBs",    0.10, 0.060),
    ("AI Governance",       0.12, 0.050),
    ("AWS",                 0.48, 0.012),
    ("Azure",               0.35, 0.010),
    ("Google Cloud",        0.28, 0.008),
    ("Snowflake",           0.30, 0.022),
    ("dbt",                 0.18, 0.025),
    ("Spark / PySpark",     0.22, 0.010),
    ("R",                   0.25, -0.005),
    ("Agile / Scrum",       0.52, 0.003),
    ("Salesforce CRM",      0.28, 0.005),
    ("Business Analysis",   0.45, 0.003),
    ("Data Visualization",  0.50, 0.005),
    ("ETL / Data Pipeline", 0.32, 0.008),
    ("Statistics",          0.38, 0.002),
    ("Communication",       0.65, 0.001),
]

DESCRIPTION_TEMPLATES = [
    "We are seeking a {role} to join our {dept} team in {location}. "
    "The ideal candidate will leverage {skill1} and {skill2} to deliver actionable insights. "
    "Responsibilities include designing {skill3} pipelines, collaborating with stakeholders, "
    "and presenting findings to senior leadership. Experience with {skill4} is a strong plus. "
    "Knowledge of {skill5} and modern {skill6} tools preferred. "
    "Familiarity with {skill7} and ability to communicate complex data clearly is essential.",

    "As a {role} at {company}, you will analyze large datasets using {skill1} and {skill2}. "
    "You'll build dashboards in {skill3} and work closely with cross-functional teams. "
    "Must be comfortable with {skill4}, {skill5}, and have experience in {skill6}. "
    "A background in {skill7} or similar analytical tools is beneficial.",

    "Join {company}'s data team as a {role}. You will use {skill1}, {skill2}, and {skill3} "
    "to extract insights from complex datasets. This role requires strong {skill4} skills "
    "and familiarity with {skill5}. Bonus: experience with {skill6} and {skill7}.",
]


def skill_prob(skill_base, growth, months_ago):
    """Adjust skill probability based on how many months ago posting was."""
    return max(0.02, min(0.97, skill_base - growth * months_ago))


def generate_description(role, company, location, sampled_skills):
    tmpl = random.choice(DESCRIPTION_TEMPLATES)
    dept = random.choice(["Analytics", "Technology", "Strategy", "Operations", "Digital Transformation"])
    skills_shuffled = sampled_skills + random.sample([s[0] for s in SKILLS], k=max(0, 7 - len(sampled_skills)))
    return tmpl.format(
        role=role, company=company, location=location, dept=dept,
        skill1=skills_shuffled[0], skill2=skills_shuffled[1],
        skill3=skills_shuffled[2], skill4=skills_shuffled[3],
        skill5=skills_shuffled[4], skill6=skills_shuffled[5],
        skill7=skills_shuffled[6] if len(skills_shuffled) > 6 else "Excel",
    )


def generate_jobs(n=3847):
    rows = []
    company_names = list(COMPANIES.keys())
    company_weights = [COMPANIES[c]["weight"] for c in company_names]
    role_names = list(ROLE_CATEGORIES.keys())
    role_weights = [ROLE_CATEGORIES[r]["weight"] for r in role_names]
    mode_names = list(WORK_MODES.keys())
    mode_weights = list(WORK_MODES.values())

    end_date = datetime(2026, 3, 16)
    start_date = end_date - timedelta(days=180)

    for _ in range(n):
        company = random.choices(company_names, weights=company_weights)[0]
        role = random.choices(role_names, weights=role_weights)[0]
        location = random.choice(LOCATIONS)
        work_mode = random.choices(mode_names, weights=mode_weights)[0]

        post_date = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        months_ago = (end_date - post_date).days / 30

        # Sample skills based on time-adjusted probabilities
        sampled_skills = []
        for skill_name, base_prob, growth in SKILLS:
            p = skill_prob(base_prob, growth, months_ago)
            if random.random() < p:
                sampled_skills.append(skill_name)

        # Salary (varies by role, company, add noise)
        base_sal = ROLE_CATEGORIES[role]["base"]
        co_adj = COMPANIES[company]["avg_sal"] - 100
        salary = max(55, int(base_sal + co_adj * 0.4 + random.gauss(0, 8)))
        salary_text = f"${salary}K" if random.random() > 0.35 else None  # not all list salary

        description = generate_description(role, company, location, sampled_skills[:5])

        rows.append({
            "job_id":        f"JOB{_ + 1:05d}",
            "title":         role,
            "company":       company,
            "company_type":  COMPANIES[company]["type"],
            "location":      location,
            "work_mode":     work_mode,
            "date_posted":   post_date.strftime("%Y-%m-%d"),
            "salary_listed": salary_text,
            "salary_k":      salary,
            "description":   description,
            "skills_raw":    "|".join(sampled_skills),
            "skill_count":   len(sampled_skills),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("date_posted").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("Generating 3,847 synthetic Bay Area tech job postings...")
    df = generate_jobs(3847)
    df.to_csv("/home/claude/ai-job-market-dashboard/data/raw/job_postings_raw.csv", index=False)
    print(f"Saved {len(df)} rows to data/raw/job_postings_raw.csv")
    print(df[["title", "company", "location", "work_mode", "salary_listed", "date_posted"]].head(5).to_string())
