# =============================
# EMBEDDING-BASED GEO JOB RANKER
# =============================

import numpy as np
from sentence_transformers import SentenceTransformer

# lightweight + strong model
model = SentenceTransformer("all-MiniLM-L6-v2")


# -------- USER PROFILE (TUNE THIS) --------

USER_PROFILE = """
geospatial engineer GIS developer
remote sensing satellite earth observation
python postgis gdal qgis
spatial data science mapping
cloud aws api docker
France Europe remote friendly
"""

profile_vec = model.encode(USER_PROFILE, normalize_embeddings=True)


# -------- EMBEDDING SCORE --------

def embedding_score(job):
    text = f"""
    {job['title']}
    {job['description']}
    {job['company']}
    {job['location']}
    """

    job_vec = model.encode(text, normalize_embeddings=True)

    sim = float(np.dot(profile_vec, job_vec))

    return max(0, min(int(sim * 100), 100))


def build_user_profile():
    return """
    GIS developer geospatial engineer
    satellite remote sensing earth observation
    python postgis gdal raster vector
    mapping spatial analysis
    France EU remote friendly
    """

profile_vec = model.encode(build_user_profile(), normalize_embeddings=True)