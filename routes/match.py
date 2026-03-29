from flask import Blueprint, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from db import get_all_internships, get_student_skills

match_bp = Blueprint('match', __name__)

def compute_matches(student_skills: str, internships: list) -> list:
    """
    Rank internships by cosine similarity between
    student skills and internship required skills.
    Returns internships sorted by match score (highest first).
    """
    if not student_skills or not internships:
        return []

    # Build corpus: student skills + all internship skill sets
    corpus = [student_skills.lower()]
    valid = []

    for i in internships:
        skills = i.get('skills_required') or i.get('domain') or ''
        if skills:
            corpus.append(skills.lower())
            valid.append(i)

    if len(corpus) < 2:
        # No internship has skills data — return all unranked
        return [{ **i, "matchScore": 0, "matchPercent": 0 } for i in internships]

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        analyzer='word',
        token_pattern=r'[a-zA-Z0-9\+\#\.]+',  # handles C++, C#, Node.js
        ngram_range=(1, 2)
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return [{ **i, "matchScore": 0, "matchPercent": 0 } for i in internships]

    # Similarity between student vector (index 0) and each internship
    student_vec = tfidf_matrix[0]
    internship_vecs = tfidf_matrix[1:]
    similarities = cosine_similarity(student_vec, internship_vecs)[0]

    # Attach scores
    scored = []
    for i, (internship, score) in enumerate(zip(valid, similarities)):
        scored.append({
            **internship,
            "matchScore": round(float(score), 4),
            "matchPercent": round(float(score) * 100, 1)
        })

    # Sort descending
    scored.sort(key=lambda x: x["matchScore"], reverse=True)
    return scored


@match_bp.route('/api/match', methods=['POST'])
def match_internships():
    """
    POST /api/match
    Body: { "userId": 1 }   OR   { "skills": "Java,React,MySQL" }

    Returns ranked list of internships by skill match.
    """
    data = request.get_json(silent=True) or {}

    # Get student skills
    user_id = data.get('userId')
    skills = data.get('skills', '')

    if user_id and not skills:
        try:
            skills = get_student_skills(int(user_id))
        except Exception as e:
            return jsonify({ "success": False, "message": str(e) }), 500

    if not skills:
        return jsonify({
            "success": False,
            "message": "No skills provided. Update your profile first."
        }), 400

    # Get all open internships
    try:
        internships = get_all_internships()
    except Exception as e:
        return jsonify({ "success": False, "message": str(e) }), 500

    # Compute matches
    ranked = compute_matches(skills, internships)

    return jsonify({
        "success": True,
        "studentSkills": skills,
        "totalMatches": len(ranked),
        "matches": ranked
    })
