from flask import Blueprint, request, jsonify
from db import get_all_internships, get_student_skills, get_connection

match_bp = Blueprint('match', __name__)


def normalize_skills(skills_str):
    """Parse comma-separated skills into a normalized set."""
    if not skills_str:
        return set()
    return set(s.strip().lower() for s in skills_str.split(',') if s.strip())


def skill_overlap_score(student_skills_str, required_skills_str):
    """
    Returns what fraction of required skills the student has.
    Consistent, deterministic, corpus-independent.
    Partial match: 'spring boot' matches if student has 'spring' or 'boot'.
    """
    student_set = normalize_skills(student_skills_str)
    required_set = normalize_skills(required_skills_str)

    if not required_set:
        return 0.0
    if not student_set:
        return 0.0

    matched = 0
    for req_skill in required_set:
        # Exact match
        if req_skill in student_set:
            matched += 1
            continue
        # Partial match (e.g. "spring boot" contains "spring")
        req_words = set(req_skill.split())
        for student_skill in student_set:
            student_words = set(student_skill.split())
            if req_words & student_words:  # any word overlap
                matched += 0.5
                break

    return min(matched / len(required_set), 1.0)


def compute_matches(student_skills: str, internships: list) -> list:
    scored = []
    for internship in internships:
        req_str = internship.get('skills_required') or internship.get('domain') or ''
        score = skill_overlap_score(student_skills, req_str)
        scored.append({
            **internship,
            "matchScore": round(score, 4),
            "matchPercent": round(score * 100, 1)
        })
    scored.sort(key=lambda x: x["matchScore"], reverse=True)
    return scored


def compute_student_matches(required_skills: str, students: list) -> list:
    scored = []
    for student in students:
        student_skills = student.get('skills') or ''
        if isinstance(student_skills, bytes):
            student_skills = student_skills.decode('utf-8')
        score = skill_overlap_score(student_skills, required_skills)
        scored.append({**student, "matchScore": round(score, 4), "matchPercent": round(score * 100, 1)})
    scored.sort(key=lambda x: x["matchScore"], reverse=True)
    return scored


@match_bp.route('/api/match', methods=['POST'])
def match_internships():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId')
    skills = data.get('skills', '')

    if user_id and not skills:
        try:
            skills = get_student_skills(int(user_id))
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    if not skills:
        return jsonify({"success": False, "message": "No skills provided. Update your profile first."}), 400

    try:
        internships = get_all_internships()
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    ranked = compute_matches(skills, internships)
    return jsonify({"success": True, "studentSkills": skills, "totalMatches": len(ranked), "matches": ranked})


@match_bp.route('/api/match/students', methods=['POST'])
def match_students():
    data = request.get_json(silent=True) or {}
    required_skills = data.get('requiredSkills', '')

    if not required_skills:
        return jsonify({"success": False, "message": "requiredSkills is required"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id, u.name, u.email,
                       sp.skills, sp.college, sp.degree,
                       sp.cgpa, sp.linkedin, sp.github,
                       sp.resume_url, sp.bio
                FROM users u
                JOIN student_profiles sp ON sp.user_id = u.id
                WHERE u.role = 'student' AND u.is_active = 1
                AND sp.skills IS NOT NULL AND sp.skills != ''
            """)
            students = cursor.fetchall()
        conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    if not students:
        return jsonify({"success": True, "matches": [], "totalMatches": 0})

    # Clean bytes fields
    clean_students = []
    for s in students:
        clean = {}
        for k, v in s.items():
            if isinstance(v, bytes):
                clean[k] = bool(v[0]) if v else False
            elif hasattr(v, 'isoformat'):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        clean_students.append(clean)

    results = compute_student_matches(required_skills, clean_students)

    # Format output
    formatted = []
    for r in results:
        formatted.append({
            "id": r.get('id'),
            "name": r.get('name'),
            "email": r.get('email'),
            "skills": r.get('skills'),
            "college": r.get('college'),
            "degree": r.get('degree'),
            "cgpa": str(r['cgpa']) if r.get('cgpa') else None,
            "linkedin": r.get('linkedin'),
            "github": r.get('github'),
            "bio": r.get('bio'),
            "resumeUrl": r.get('resume_url'),
            "matchScore": r.get('matchScore'),
            "matchPercent": r.get('matchPercent'),
        })

    return jsonify({
        "success": True,
        "requiredSkills": required_skills,
        "totalMatches": len(formatted),
        "matches": formatted
    })
