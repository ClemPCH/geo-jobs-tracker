# =============================
# GEO JOB INTELLIGENCE ENGINE (FR + GIS FOCUS)
# =============================

from datetime import datetime
import json
import requests

from utils.embedding import embedding_score

# -------- CONFIG --------

KEYWORDS = [
    "geospatial", "geo", "spatial", "mapping", "gis",
    "remote sensing", "satellite", "earth observation",
    "raster", "vector", "cartography",
    "postgis", "gdal", "qgis",
    "geodata", "location data"
]

REMOTE_KEYWORDS = ["remote", "anywhere", "work from home"]

FRANCE_HINTS = ["france", "paris", "lyon", "toulouse", "bordeaux", "nantes"]
EU_HINTS = ["europe", "germany", "spain", "italy", "netherlands", "belgium"]

WEIGHTS = {
    "python": 10,
    "postgis": 10,
    "gdal": 8,
    "satellite": 10,
    "remote sensing": 10,
    "aws": 6,
    "api": 6,
    "docker": 5,
    "gis": 9,
    "geospatial": 10
}

COMPANY_BOOST = {
    "government": 10,
    "space": 10,
    "defense": 8,
    "mapping": 10,
    "startup": 6,
    "consulting": 5
}

# -------- NORMALIZE --------

def normalize(job):
    return {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "description": job.get("description", ""),
        "link": job.get("link", ""),
    }


# -------- FETCHERS --------

def fetch_remotive():
    out = []
    try:
        data = requests.get("https://remotive.com/api/remote-jobs", timeout=20).json()
        for j in data.get("jobs", []):
            text = (j["title"] + j["description"]).lower()
            if any(k in text for k in KEYWORDS):
                out.append(normalize({
                    "title": j["title"],
                    "company": j["company_name"],
                    "location": j.get("candidate_required_location", "Remote"),
                    "description": j["description"],
                    "link": j["url"]
                }, "remotive"))
    except Exception:
        pass
    return out


def fetch_remoteok():
    out = []
    try:
        data = requests.get("https://remoteok.com/api", headers={"User-Agent": "x"}, timeout=20).json()
        for j in data[1:]:
            if not isinstance(j, dict):
                continue
            text = (str(j.get("position","")) + str(j.get("description",""))).lower()
            if any(k in text for k in KEYWORDS):
                out.append(normalize({
                    "title": j.get("position"),
                    "company": j.get("company"),
                    "location": j.get("location"),
                    "description": j.get("description"),
                    "link": j.get("url")
                }, "remoteok"))
    except Exception:
        pass
    return out


def fetch_lever(company):
    out = []
    try:
        data = requests.get(f"https://api.lever.co/v0/postings/{company}", timeout=20).json()
        if not isinstance(data, list):
            return out

        for j in data:
            if not isinstance(j, dict):
                continue

            text = (j.get("text","") + j.get("descriptionPlain","")).lower()

            if any(k in text for k in KEYWORDS):
                out.append(normalize({
                    "title": j.get("text"),
                    "company": company,
                    "location": j.get("categories", {}).get("location", "Unknown"),
                    "description": j.get("descriptionPlain",""),
                    "link": j.get("hostedUrl")
                }, "lever"))
    except Exception:
        pass
    return out


def fetch_ashby(company):
    out = []
    try:
        data = requests.get(f"https://jobs.ashbyhq.com/api/non-user-boards/{company}", timeout=20).json()
        for j in data.get("jobs", []):
            text = (j.get("title","") + j.get("description","")).lower()
            if any(k in text for k in KEYWORDS):
                out.append(normalize({
                    "title": j.get("title"),
                    "company": company,
                    "location": j.get("location",""),
                    "description": j.get("description",""),
                    "link": j.get("jobUrl")
                }, "ashby"))
    except Exception:
        pass
    return out


# -------- SCORING --------

def score(job):
    base = embedding_score(job)

    location = (job["location"] or "").lower()

    # France boost (still useful even with embeddings)
    if "france" in location or "paris" in location:
        base += 10

    # Remote boost
    if "remote" in location:
        base += 5

    return min(base, 100)


# -------- TAGS --------

def tags(text):
    t = text.lower()
    out = []

    if "satellite" in t or "earth observation" in t:
        out.append("EO")
    if "api" in t:
        out.append("Backend")
    if "cloud" in t or "aws" in t:
        out.append("Cloud")
    if "machine learning" in t:
        out.append("ML")
    if "gis" in t:
        out.append("GIS")

    return out


# -------- PIPELINE --------

def dedupe(jobs):
    seen = set()
    out = []

    for j in jobs:
        key = (j["title"].lower(), j["company"].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(j)

    return out


def process(raw):
    out = []

    for j in raw:
        text = j["title"] + j["description"]

        out.append({
            **j,
            "score": score(j),
            "tags": tags(text),
            "isRemote": any(r in j["location"].lower() for r in REMOTE_KEYWORDS),
            "isFranceBoost": any(f in j["location"].lower() for f in FRANCE_HINTS)
        })

    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:30]


# -------- SAVE --------

def save(data):
    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved", len(data), "jobs", datetime.now())


# -------- MAIN --------

if __name__ == "__main__":
    raw = []

    raw += fetch_remotive()
    raw += fetch_remoteok()

    raw += fetch_lever("planetlabs")
    raw += fetch_lever("carto")
    raw += fetch_lever("spire")
    raw += fetch_lever("mapbox")

    raw += fetch_ashby("example")  # replace with real companies

    raw = dedupe(raw)

    processed = process(raw)
    save(processed)
