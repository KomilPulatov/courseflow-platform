import re
from datetime import UTC, datetime
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.students.models import Student, StudentAcademicProfile, StudentCompletedCourse


def _extract_profile_from_xml(
    client: httpx.Client,
    grades_url: str,
    grades_html: str,
) -> dict[str, str]:
    match = re.search(r"MarkView_xml\.aspx\?Value=[^'\"\s>]+", grades_html)
    if not match:
        return {}

    xml_url = urljoin(grades_url, match.group(0))
    xml_response = client.get(xml_url)
    if xml_response.status_code != 200:
        return {}

    xml_tree = HTMLParser(xml_response.text)

    def get_text(tag: str) -> str:
        node = xml_tree.css_first(tag)
        return node.text(strip=True) if node else ""

    return {
        "student_number": get_text("STNO"),
        "full_name": get_text("KNAME"),
        "department_name": get_text("DEPT_KNAME"),
        "major_name": get_text("MAJOR_NAME"),
        "academic_year": get_text("GRADE"),
    }


def run_sync_simple(db: Session, user_id: str, username: str, password: str) -> None:
    base_url = settings.PORTAL_BASE_URL.rstrip("/")
    login_url = base_url + settings.PORTAL_LOGIN_PATH
    grades_url = base_url + settings.PORTAL_GRADES_PATH

    headers = {"User-Agent": settings.PORTAL_USER_AGENT}

    # 1. Start a browser session
    with httpx.Client(
        follow_redirects=True,
        timeout=settings.HTTP_TIMEOUT,
        headers=headers,
    ) as client:
        # Go to the login page first
        login_page_response = client.get(login_url)
        tree = HTMLParser(login_page_response.text)
        form = tree.css_first("form")
        if form is None:
            raise Exception("Login form not found.")

        action = form.attributes.get("action") or settings.PORTAL_LOGIN_PATH
        login_post_url = urljoin(login_url, action)

        login_data: dict[str, str] = {}
        username_field = None
        password_field = None

        for input_tag in form.css("input"):
            name = input_tag.attributes.get("name")
            if not name:
                continue
            value = input_tag.attributes.get("value", "")
            login_data[name] = value

            input_type = input_tag.attributes.get("type", "").lower()
            if input_type == "password" and password_field is None:
                password_field = name
            elif input_type in {"text", "email"} and username_field is None:
                username_field = name

        login_data[username_field or "UserId"] = username
        login_data[password_field or "Password"] = password

        post_response = client.post(login_post_url, data=login_data)

        if post_response.status_code in {401, 403}:
            raise Exception("Login failed. Check your username and password.")
        if "Logout" not in post_response.text and "logout" not in post_response.text:
            raise Exception("Login failed. Check your username and password.")
        grades_response = client.get(grades_url)
        grades_html = grades_response.text

        profile_data = _extract_profile_from_xml(client, grades_url, grades_html)

    tree = HTMLParser(grades_html)
    try:
        user_id_int = int(user_id)
    except ValueError as exc:
        raise Exception("user_id must be a number.") from exc

    student = db.query(Student).filter(Student.user_id == user_id_int).first()
    if not student:
        raise Exception("Student not found in our database.")

    if profile_data.get("full_name"):
        student.full_name = profile_data["full_name"]

    current_semester = ""
    found_courses = []

    for row in tree.css("table tr"):
        text = row.text(strip=True)

        if "Semester" in text:
            if "Fall" in text:
                year = text.split(" ")[1]
                current_semester = f"{year}-Fall"
            elif "Spring" in text:
                year = text.split(" ")[1]
                current_semester = f"{year}-Spring"
            continue
        columns = row.css("td")
        if len(columns) == 5:
            course_code = columns[0].text(strip=True)
            course_title = columns[1].text(strip=True)
            grade = columns[2].text(strip=True)
            credits = columns[3].text(strip=True)
            if course_title == "Course Title":
                continue
            if not course_code or "CA:" in text:
                continue
            grade_points_map = {
                "A+": 4.5,
                "A0": 4.0,
                "B+": 3.5,
                "B0": 3.0,
                "C+": 2.5,
                "C0": 2.0,
                "D+": 1.5,
                "D0": 1.0,
            }
            grade_points = grade_points_map.get(grade, 0.0)

            found_courses.append(
                {
                    "semester": current_semester,
                    "code": course_code,
                    "title": course_title,
                    "grade": grade,
                    "credits": int(float(credits)),
                    "grade_points": grade_points,
                }
            )
    db.query(StudentCompletedCourse).filter(
        StudentCompletedCourse.student_id == student.id
    ).delete()

    total_credits = 0
    total_score = 0.0

    for course in found_courses:
        db.add(
            StudentCompletedCourse(
                student_id=student.id,
                source="ins_verified",
                course_code=course["code"],
                course_title=course["title"],
                credits=course["credits"],
                grade=course["grade"],
            )
        )

        total_credits += course["credits"]
        total_score += course["credits"] * course["grade_points"]

    profile = (
        db.query(StudentAcademicProfile)
        .filter(StudentAcademicProfile.student_id == student.id)
        .first()
    )
    if not profile:
        profile = StudentAcademicProfile(student_id=student.id, department_name="Unknown")
        db.add(profile)

    if profile_data.get("department_name"):
        profile.department_name = profile_data["department_name"]
    if profile_data.get("major_name"):
        profile.major_name = profile_data["major_name"]
    if profile_data.get("academic_year", "").isdigit():
        profile.academic_year = int(profile_data["academic_year"])

    if total_credits > 0:
        profile.current_gpa = round(total_score / total_credits, 2)
    else:
        profile.current_gpa = 0.0
    profile.gpa_is_verified = True
    profile.last_synced_at = datetime.now(UTC)
    db.commit()
