from flask import Blueprint, request, jsonify
from db import get_student_skills

skillgap_bp = Blueprint('skillgap', __name__)

# Free course recommendations per skill
COURSE_MAP = {
    "java":           { "course": "Java Programming Masterclass", "platform": "Udemy",    "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/" },
    "python":         { "course": "Python for Everybody",          "platform": "Coursera", "url": "https://www.coursera.org/specializations/python" },
    "react":          { "course": "React - The Complete Guide",    "platform": "Udemy",    "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/" },
    "node.js":        { "course": "Node.js Developer Course",      "platform": "Udemy",    "url": "https://www.udemy.com/course/the-complete-nodejs-developer-course-2/" },
    "mysql":          { "course": "MySQL for Beginners",           "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=7S_tz1z_5bA" },
    "mongodb":        { "course": "MongoDB Basics",                "platform": "MongoDB",  "url": "https://learn.mongodb.com/learning-paths/mongodb-for-sql-experts" },
    "spring boot":    { "course": "Spring Boot Tutorial",          "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=9SGDpanrc8U" },
    "machine learning": { "course": "ML Crash Course",            "platform": "Google",   "url": "https://developers.google.com/machine-learning/crash-course" },
    "tensorflow":     { "course": "TensorFlow Developer Certificate","platform": "Coursera","url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice" },
    "pandas":         { "course": "Pandas Tutorial",               "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=vmEHCJofslg" },
    "numpy":          { "course": "NumPy for Beginners",           "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=QUT1VHiLmmI" },
    "figma":          { "course": "Figma UI Design Tutorial",      "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=FTFaQWZBqQ8" },
    "adobe xd":       { "course": "Adobe XD Full Course",          "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=3aOU9MbITlM" },
    "docker":         { "course": "Docker for Beginners",          "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=fqMOX6JJhGo" },
    "git":            { "course": "Git & GitHub Crash Course",     "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=RGOj5yH7evk" },
    "aws":            { "course": "AWS Cloud Practitioner",        "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=SOTamWNgDKc" },
    "seo":            { "course": "SEO Full Course",               "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=xsVTqzratPs" },
    "google ads":     { "course": "Google Ads Tutorial",           "platform": "YouTube",  "url": "https://www.youtube.com/watch?v=lD5C5OBpCDU" },
    "prototyping":    { "course": "UX Prototyping",                "platform": "Coursera", "url": "https://www.coursera.org/learn/wireframes-low-fidelity-prototypes" },
    "data science":   { "course": "Data Science Specialization",   "platform": "Coursera", "url": "https://www.coursera.org/specializations/jhu-data-science" },
    "sql":            { "course": "SQL for Data Science",          "platform": "Coursera", "url": "https://www.coursera.org/learn/sql-for-data-science" },
}

def normalize(skill: str) -> str:
    return skill.strip().lower()

def parse_skills(skills_str: str) -> set:
    if not skills_str:
        return set()
    return {normalize(s) for s in skills_str.split(',') if s.strip()}

def get_course(skill: str) -> dict:
    key = normalize(skill)
    # exact match
    if key in COURSE_MAP:
        return COURSE_MAP[key]
    # partial match
    for k, v in COURSE_MAP.items():
        if k in key or key in k:
            return v
    # generic fallback
    return {
        "course": f"Learn {skill.title()}",
        "platform": "YouTube",
        "url": f"https://www.youtube.com/results?search_query={skill.replace(' ', '+')}+tutorial"
    }


@skillgap_bp.route('/api/skillgap', methods=['POST'])
def skill_gap():
    """
    POST /api/skillgap
    Body: {
        "userId": 1,                           -- OR --
        "studentSkills": "Java,React",
        "requiredSkills": "Java,React,Docker,AWS"
    }

    Returns:
    - matched skills (student has these)
    - missing skills (student needs these)
    - course recommendations for each missing skill
    - gap score (0-100, lower = bigger gap)
    """
    data = request.get_json(silent=True) or {}

    # Get student skills
    user_id = data.get('userId')
    student_skills_str = data.get('studentSkills', '')
    required_skills_str = data.get('requiredSkills', '')

    if user_id and not student_skills_str:
        try:
            student_skills_str = get_student_skills(int(user_id))
        except Exception as e:
            return jsonify({ "success": False, "message": str(e) }), 500

    if not required_skills_str:
        return jsonify({
            "success": False,
            "message": "requiredSkills is required"
        }), 400

    student_set = parse_skills(student_skills_str)
    required_set = parse_skills(required_skills_str)

    matched = sorted(student_set & required_set)
    missing = sorted(required_set - student_set)

    # Gap score: percentage of required skills the student already has
    gap_score = round((len(matched) / len(required_set)) * 100) if required_set else 100

    # Course recommendations for missing skills
    recommendations = []
    for skill in missing:
        course = get_course(skill)
        recommendations.append({
            "skill": skill.title(),
            "course": course["course"],
            "platform": course["platform"],
            "url": course["url"]
        })

    return jsonify({
        "success": True,
        "studentSkills": list(student_set),
        "requiredSkills": list(required_set),
        "matchedSkills": [s.title() for s in matched],
        "missingSkills": [s.title() for s in missing],
        "gapScore": gap_score,
        "gapLevel": "Low" if gap_score >= 70 else "Medium" if gap_score >= 40 else "High",
        "recommendations": recommendations
    })
