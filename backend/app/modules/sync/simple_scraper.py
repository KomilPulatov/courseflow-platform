from datetime import UTC, datetime
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.students.models import Student, StudentAcademicProfile, StudentCompletedCourse


GRADE_POINTS_MAP = {
    "A+": 4.5,
    "A0": 4.0,
    "B+": 3.5,
    "B0": 3.0,
    "C+": 2.5,
    "C0": 2.0,
    "D+": 1.5,
    "D0": 1.0,
    "F": 0.0,
}


def _looks_like_login_page(html: str) -> bool:
    return bool(
        HTMLParser(html).css_first("input[name='txtInhaID'], input[name='txtPW']")
    )


def _get_first_tag_text(tree: HTMLParser, tags: list[str]) -> str:
    for tag in tags:
        for candidate in {tag, tag.lower(), tag.upper()}:
            nodes = tree.css(candidate)
            if nodes:
                value = nodes[0].text(strip=True)
                if value:
                    return value
    return ""


def _split_paren(value: str) -> tuple[str, str]:
    if "(" not in value or ")" not in value:
        return "", ""
    left, right = value.split("(", 1)
    return left.strip(), right.split(")", 1)[0].strip()


def _normalize_department_major(profile: dict[str, str]) -> None:
    department = profile.get("department_name", "")
    major = profile.get("major_name", "")

    dep_from_dept, maj_from_dept = _split_paren(department)
    dep_from_major, maj_from_major = _split_paren(major)

    if dep_from_dept:
        department = dep_from_dept
    elif dep_from_major:
        department = dep_from_major

    if maj_from_major:
        major = maj_from_major
    elif maj_from_dept:
        major = maj_from_dept

    if department:
        profile["department_name"] = department
    if major:
        profile["major_name"] = major


def _parse_profile_from_text(text: str) -> dict[str, str]:
    tokens = HTMLParser(text).text().split()
    if len(tokens) < 3:
        return {}

    student_number = tokens[0]
    full_name = " ".join(tokens[1:3]).strip()
    department_name = ""
    major_name = ""

    for index in range(min(10, len(tokens))):
        department_name, major_name = _split_paren(tokens[index])
        if department_name or major_name:
            break
        if index + 1 < len(tokens):
            next_token = tokens[index + 1]
            if next_token.startswith("(") and next_token.endswith(")"):
                department_name = tokens[index].strip()
                major_name = next_token.strip("()").strip()
                break

    return {
        "student_number": student_number,
        "full_name": full_name,
        "department_name": department_name,
        "major_name": major_name,
        "academic_year": "",
    }


def _parse_profile_from_xml(xml_text: str) -> dict[str, str]:
    xml_tree = HTMLParser(xml_text)
    profile = {
        "student_number": _get_first_tag_text(
            xml_tree,
            ["STNO", "ST_NO", "STD_NO", "STUDENT_NO", "STUDENT_NUMBER"],
        ),
        "full_name": _get_first_tag_text(
            xml_tree,
            ["KNAME", "K_NAME", "STUDENT_NAME", "FULL_NAME", "NAME"],
        ),
        "department_name": _get_first_tag_text(
            xml_tree,
            ["DEPT_KNAME", "DEPT_NAME", "DEPARTMENT_NAME", "DEPT"],
        ),
        "major_name": _get_first_tag_text(
            xml_tree,
            ["MAJOR_NAME", "MAJOR", "MAJOR_KNAME"],
        ),
        "academic_year": _get_first_tag_text(
            xml_tree,
            ["GRADE", "ACADEMIC_YEAR", "YEAR_STANDING"],
        ),
    }

    text_profile = _parse_profile_from_text(xml_text)
    for key, value in text_profile.items():
        if not profile.get(key) and value:
            profile[key] = value

    _normalize_department_major(profile)

    return profile


def _safe_int(value: str) -> int | None:
    try:
        return int(float(value))
    except ValueError:
        return None


def _grade_points_for(grade: str) -> float:
    return GRADE_POINTS_MAP.get(grade.upper(), 0.0)


def _parse_courses_from_rows(tree: HTMLParser) -> list[dict[str, object]]:
    courses: list[dict[str, object]] = []
    for row in tree.css("ROW, row, TR, tr"):
        code = _get_first_tag_text(
            row,
            ["COURSE_CODE", "SUBJECT_CODE", "CODE", "SUBJ_CODE", "COURSE"],
        )
        title = _get_first_tag_text(
            row,
            ["COURSE_TITLE", "SUBJECT_NAME", "TITLE", "SUBJ_NAME"],
        )
        grade = _get_first_tag_text(
            row,
            ["GRADE", "SCORE", "MARK"],
        )
        credits_text = _get_first_tag_text(
            row,
            ["CREDITS", "CREDIT", "CRD", "CREDIT_HOUR"],
        )
        semester = _get_first_tag_text(
            row,
            ["SEMESTER", "TERM", "YEAR_TERM", "YEAR_SEMESTER"],
        )

        if not code or not grade or not credits_text:
            continue

        credits = _safe_int(credits_text)
        if credits is None:
            continue

        courses.append(
            {
                "semester": semester,
                "code": code,
                "title": title,
                "grade": grade,
                "credits": credits,
                "grade_points": _grade_points_for(grade),
            }
        )
    return courses


def _parse_courses_from_table(tree: HTMLParser) -> list[dict[str, object]]:
    current_semester = ""
    courses: list[dict[str, object]] = []

    for row in tree.css("table tr"):
        text = row.text(strip=True)
        if not text:
            continue

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

            credits_value = _safe_int(credits)
            if credits_value is None:
                continue

            courses.append(
                {
                    "semester": current_semester,
                    "code": course_code,
                    "title": course_title,
                    "grade": grade,
                    "credits": credits_value,
                    "grade_points": _grade_points_for(grade),
                }
            )

    return courses


def _parse_courses_from_text(text: str, student_number: str) -> list[dict[str, object]]:
    if not student_number:
        return []

    tokens = HTMLParser(text).text().split()
    if not tokens:
        return []

    standings = {"Freshman", "Sophomore", "Junior", "Senior"}
    seasons = {"Fall", "Spring"}
    grade_tokens = set(GRADE_POINTS_MAP.keys())

    courses: list[dict[str, object]] = []
    i = 0

    while i < len(tokens):
        if tokens[i] != student_number:
            i += 1
            continue

        if i + 6 >= len(tokens) or tokens[i + 1] not in standings:
            i += 1
            continue

        year = tokens[i + 3]
        season = tokens[i + 4]
        if season not in seasons or tokens[i + 5].lower() != "semester":
            i += 1
            continue

        course_code = tokens[i + 6]
        title_parts: list[str] = []
        j = i + 7

        while j + 1 < len(tokens):
            credits_value = _safe_int(tokens[j])
            if credits_value is not None and tokens[j + 1] in grade_tokens:
                grade = tokens[j + 1]
                course_title = " ".join(title_parts).strip()
                if course_title:
                    courses.append(
                        {
                            "semester": f"{year}-{season}",
                            "code": course_code,
                            "title": course_title,
                            "grade": grade,
                            "credits": credits_value,
                            "grade_points": _grade_points_for(grade),
                        }
                    )
                i = j + 2
                break

            title_parts.append(tokens[j])
            j += 1
        else:
            i += 1

    return courses


def _parse_courses_from_xml(xml_text: str, student_number: str) -> list[dict[str, object]]:
    tree = HTMLParser(xml_text)
    courses = _parse_courses_from_rows(tree)
    if courses:
        return courses

    courses = _parse_courses_from_table(tree)
    if courses:
        return courses

    return _parse_courses_from_text(xml_text, student_number)


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
        if _looks_like_login_page(post_response.text):
            raise Exception("Login failed. Check your username and password.")
        grades_response = client.get(grades_url)
        if grades_response.status_code != 200:
            raise Exception("Grades XML unavailable.")
        xml_text = grades_response.text
        if _looks_like_login_page(xml_text):
            raise Exception("Login failed. Check your username and password.")

        profile_data = _parse_profile_from_xml(xml_text)
        found_courses = _parse_courses_from_xml(
            xml_text, profile_data.get("student_number", "")
        )
    try:
        user_id_int = int(user_id)
    except ValueError as exc:
        raise Exception("user_id must be a number.") from exc

    student = db.query(Student).filter(Student.user_id == user_id_int).first()
    if not student:
        raise Exception("Student not found in our database.")

    if profile_data.get("full_name"):
        student.full_name = profile_data["full_name"]

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
                completed_semester=course.get("semester") or None,
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
