from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)

# =========================================================
# APP CONFIGURATION
# =========================================================

app.secret_key = "placement_management_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "placement.db")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def create_database():

    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
                CHECK(role IN ('student', 'admin')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # PROFILES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            phone TEXT,
            dob TEXT,
            gender TEXT,
            address TEXT,
            resume TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # ACADEMICS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            ssc_percentage REAL DEFAULT 0,
            hsc_percentage REAL DEFAULT 0,
            graduation_percentage REAL DEFAULT 0,
            graduation_cgpa REAL DEFAULT 0,
            msc_cgpa REAL DEFAULT 0,
            backlogs INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # SKILLS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            skill_level TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # PROJECTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            technologies TEXT,
            project_link TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # CERTIFICATIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            certificate_name TEXT NOT NULL,
            organization TEXT,
            issue_date TEXT,
            certificate_link TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # INTERNSHIPS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            role TEXT,
            duration TEXT,
            technologies TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # COMPANIES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            location TEXT,
            website TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # JOBS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            skills TEXT,
            location TEXT,
            package TEXT,
            min_cgpa REAL DEFAULT 0,
            max_backlogs INTEGER DEFAULT 0,
            deadline TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(company_id) REFERENCES companies(id)
                ON DELETE SET NULL
        )
    """)

    # APPLICATIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            applied_date TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Applied',
            UNIQUE(student_id, job_id),
            FOREIGN KEY(student_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
                ON DELETE CASCADE
        )
    """)

    # INTERVIEWS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            interview_date TEXT,
            interview_time TEXT,
            interview_type TEXT,
            round TEXT,
            meeting_link TEXT,
            result TEXT DEFAULT 'Pending',
            feedback TEXT,
            FOREIGN KEY(application_id) REFERENCES applications(id)
                ON DELETE CASCADE
        )
    """)

    # PREPARATION
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preparation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            description TEXT,
            resource_link TEXT
        )
    """)

    # SKILL GAPS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            missing_skills TEXT,
            gap_percentage REAL DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES users(id)
                ON DELETE CASCADE,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
                ON DELETE CASCADE
        )
    """)

    # RECOMMENDATIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # NOTIFICATIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # PLACEMENT STATUS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS placement_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER UNIQUE NOT NULL,
            status TEXT DEFAULT 'Not Placed',
            company_name TEXT,
            job_title TEXT,
            package TEXT,
            FOREIGN KEY(student_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # DEFAULT ADMIN
    # =====================================================

    admin = cursor.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, ("admin@gmail.com",)).fetchone()

    if admin is None:

        admin_password = generate_password_hash("admin123")

        cursor.execute("""
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, 'admin')
        """, (
            "Administrator",
            "admin@gmail.com",
            admin_password
        ))

    conn.commit()
    conn.close()


# =========================================================
# AUTH DECORATORS
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("student_dashboard"))

        return function(*args, **kwargs)

    return wrapper


def student_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))

        if session.get("role") != "student":
            return redirect(url_for("admin_dashboard"))

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        conn = get_db()

        existing = conn.execute("""
            SELECT id
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if existing:
            conn.close()
            flash("Email already registered.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, 'student')
        """, (
            name,
            email,
            hashed_password
        ))

        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO profiles (user_id)
            VALUES (?)
        """, (user_id,))

        cursor.execute("""
            INSERT INTO academics (user_id)
            VALUES (?)
        """, (user_id,))

        cursor.execute("""
            INSERT INTO placement_status
            (student_id, status)
            VALUES (?, 'Not Placed')
        """, (user_id,))

        conn.commit()
        conn.close()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            # IMPORTANT:
            # ADMIN -> ADMIN DASHBOARD
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            # STUDENT -> STUDENT DASHBOARD
            return redirect(url_for("student_dashboard"))

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(url_for("login"))


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student_dashboard")
@student_required
def student_dashboard():

    user_id = session["user_id"]

    conn = get_db()

    applications = conn.execute("""
        SELECT COUNT(*) AS total
        FROM applications
        WHERE student_id = ?
    """, (user_id,)).fetchone()["total"]

    interviews = conn.execute("""
        SELECT COUNT(*) AS total
        FROM interviews i
        JOIN applications a
            ON i.application_id = a.id
        WHERE a.student_id = ?
    """, (user_id,)).fetchone()["total"]

    notifications = conn.execute("""
        SELECT COUNT(*) AS total
        FROM notifications
        WHERE user_id = ?
        AND is_read = 0
    """, (user_id,)).fetchone()["total"]

    placement = conn.execute("""
        SELECT status
        FROM placement_status
        WHERE student_id = ?
    """, (user_id,)).fetchone()

    conn.close()

    placement_status_value = "Not Placed"

    if placement:
        placement_status_value = placement["status"]

    return render_template(
        "student_dashboard.html",
        applications=applications,
        interviews=interviews,
        notifications=notifications,
        placement_status=placement_status_value
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/student/profile", methods=["GET", "POST"])
@student_required
def profile():

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        conn.execute("""
            UPDATE profiles
            SET phone = ?,
                dob = ?,
                gender = ?,
                address = ?,
                resume = ?
            WHERE user_id = ?
        """, (
            request.form.get("phone"),
            request.form.get("dob"),
            request.form.get("gender"),
            request.form.get("address"),
            request.form.get("resume"),
            user_id
        ))

        conn.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

    data = conn.execute("""
        SELECT *
        FROM profiles
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        profile=data
    )


# =========================================================
# ACADEMICS
# =========================================================

@app.route("/student/academics", methods=["GET", "POST"])
@student_required
def academics():

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        try:

            ssc = float(
                request.form.get("ssc_percentage") or 0
            )

            hsc = float(
                request.form.get("hsc_percentage") or 0
            )

            graduation_percentage = float(
                request.form.get("graduation_percentage") or 0
            )

            graduation_cgpa = float(
                request.form.get("graduation_cgpa") or 0
            )

            msc_cgpa = float(
                request.form.get("msc_cgpa") or 0
            )

            backlogs = int(
                request.form.get("backlogs") or 0
            )

        except ValueError:

            conn.close()

            flash(
                "Please enter valid academic values.",
                "error"
            )

            return redirect(url_for("academics"))

        conn.execute("""
            UPDATE academics
            SET ssc_percentage = ?,
                hsc_percentage = ?,
                graduation_percentage = ?,
                graduation_cgpa = ?,
                msc_cgpa = ?,
                backlogs = ?
            WHERE user_id = ?
        """, (
            ssc,
            hsc,
            graduation_percentage,
            graduation_cgpa,
            msc_cgpa,
            backlogs,
            user_id
        ))

        conn.commit()

        flash(
            "Academic details updated.",
            "success"
        )

    data = conn.execute("""
        SELECT *
        FROM academics
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    conn.close()

    return render_template(
        "academics.html",
        academics=data
    )


# =========================================================
# SKILLS
# =========================================================

@app.route("/student/skills", methods=["GET", "POST"])
@student_required
def skills():

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        skill_name = request.form.get(
            "skill_name",
            ""
        ).strip()

        skill_level = request.form.get(
            "skill_level",
            ""
        ).strip()

        if not skill_name:

            flash(
                "Skill name is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO skills
                (user_id, skill_name, skill_level)
                VALUES (?, ?, ?)
            """, (
                user_id,
                skill_name,
                skill_level
            ))

            conn.commit()

            flash(
                "Skill added successfully.",
                "success"
            )

    data = conn.execute("""
        SELECT *
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "skills.html",
        skills=data
    )


@app.route(
    "/student/skills/delete/<int:skill_id>",
    methods=["POST"]
)
@student_required
def delete_skill(skill_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM skills
        WHERE id = ?
        AND user_id = ?
    """, (
        skill_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    flash(
        "Skill deleted.",
        "success"
    )

    return redirect(url_for("skills"))


# =========================================================
# PROJECTS
# =========================================================

@app.route("/student/projects", methods=["GET", "POST"])
@student_required
def projects():

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        if not title:

            flash(
                "Project title is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO projects
                (
                    user_id,
                    title,
                    description,
                    technologies,
                    project_link
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                title,
                request.form.get("description"),
                request.form.get("technologies"),
                request.form.get("project_link")
            ))

            conn.commit()

            flash(
                "Project added successfully.",
                "success"
            )

    data = conn.execute("""
        SELECT *
        FROM projects
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "projects.html",
        projects=data
    )


@app.route(
    "/student/projects/delete/<int:project_id>",
    methods=["POST"]
)
@student_required
def delete_project(project_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM projects
        WHERE id = ?
        AND user_id = ?
    """, (
        project_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    flash(
        "Project deleted.",
        "success"
    )

    return redirect(url_for("projects"))


# =========================================================
# CERTIFICATIONS
# =========================================================

@app.route(
    "/student/certifications",
    methods=["GET", "POST"]
)
@student_required
def certifications():

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        certificate_name = request.form.get(
            "certificate_name",
            ""
        ).strip()

        if not certificate_name:

            flash(
                "Certificate name is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO certifications
                (
                    user_id,
                    certificate_name,
                    organization,
                    issue_date,
                    certificate_link
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                certificate_name,
                request.form.get("organization"),
                request.form.get("issue_date"),
                request.form.get("certificate_link")
            ))

            conn.commit()

            flash(
                "Certification added successfully.",
                "success"
            )

    data = conn.execute("""
        SELECT *
        FROM certifications
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "certifications.html",
        certifications=data
    )


# =========================================================
# INTERNSHIPS
# =========================================================

@app.route(
    "/student/internships",
    methods=["GET", "POST"]
)
@student_required
def internships():

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        company_name = request.form.get(
            "company_name",
            ""
        ).strip()

        if not company_name:

            flash(
                "Company name is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO internships
                (
                    user_id,
                    company_name,
                    role,
                    duration,
                    technologies
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                company_name,
                request.form.get("role"),
                request.form.get("duration"),
                request.form.get("technologies")
            ))

            conn.commit()

            flash(
                "Internship added successfully.",
                "success"
            )

    data = conn.execute("""
        SELECT *
        FROM internships
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "internships.html",
        internships=data
    )


# =========================================================
# STUDENT JOBS
# =========================================================

@app.route("/student/jobs")
@student_required
def jobs():

    conn = get_db()

    data = conn.execute("""
        SELECT
            jobs.*,
            companies.name AS company_name,
            companies.website AS company_website
        FROM jobs
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        ORDER BY jobs.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "jobs.html",
        jobs=data
    )


# =========================================================
# ELIGIBILITY
# =========================================================

@app.route("/student/eligibility")
@student_required
def eligibility():

    user_id = session["user_id"]

    conn = get_db()

    academic = conn.execute("""
        SELECT *
        FROM academics
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    jobs_data = conn.execute("""
        SELECT
            jobs.*,
            companies.name AS company_name
        FROM jobs
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        ORDER BY jobs.id DESC
    """).fetchall()

    conn.close()

    eligible_jobs = []

    if academic:

        for job in jobs_data:

            eligible = (
                academic["msc_cgpa"] >= job["min_cgpa"]
                and
                academic["backlogs"] <= job["max_backlogs"]
            )

            if job["deadline"]:

                try:

                    deadline = datetime.strptime(
                        job["deadline"],
                        "%Y-%m-%d"
                    ).date()

                    if deadline < datetime.now().date():
                        eligible = False

                except ValueError:
                    pass

            if eligible:
                eligible_jobs.append(job)

    return render_template(
        "eligibility.html",
        jobs=eligible_jobs
    )


# =========================================================
# APPLY JOB
# =========================================================

@app.route(
    "/student/apply/<int:job_id>",
    methods=["POST"]
)
@student_required
def apply_job(job_id):

    student_id = session["user_id"]

    conn = get_db()

    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id = ?
    """, (job_id,)).fetchone()

    if not job:

        conn.close()

        flash(
            "Job not found.",
            "error"
        )

        return redirect(url_for("jobs"))

    academic = conn.execute("""
        SELECT *
        FROM academics
        WHERE user_id = ?
    """, (student_id,)).fetchone()

    if academic:

        if (
            academic["msc_cgpa"] < job["min_cgpa"]
            or
            academic["backlogs"] > job["max_backlogs"]
        ):

            conn.close()

            flash(
                "You are not eligible for this job.",
                "error"
            )

            return redirect(url_for("jobs"))

    existing = conn.execute("""
        SELECT id
        FROM applications
        WHERE student_id = ?
        AND job_id = ?
    """, (
        student_id,
        job_id
    )).fetchone()

    if existing:

        conn.close()

        flash(
            "You have already applied for this job.",
            "error"
        )

        return redirect(url_for("jobs"))

    try:

        conn.execute("""
            INSERT INTO applications
            (student_id, job_id, status)
            VALUES (?, ?, 'Applied')
        """, (
            student_id,
            job_id
        ))

        conn.commit()

        flash(
            "Application submitted successfully.",
            "success"
        )

    except sqlite3.IntegrityError:

        flash(
            "You have already applied for this job.",
            "error"
        )

    conn.close()

    return redirect(url_for("jobs"))


# =========================================================
# STUDENT APPLICATIONS
# =========================================================

@app.route("/student/applications")
@student_required
def applications():

    user_id = session["user_id"]

    conn = get_db()

    data = conn.execute("""
        SELECT
            applications.*,
            jobs.title AS job_title,
            jobs.location AS job_location,
            jobs.package AS job_package,
            companies.name AS company_name
        FROM applications
        JOIN jobs
            ON applications.job_id = jobs.id
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        WHERE applications.student_id = ?
        ORDER BY applications.id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "applications.html",
        applications=data
    )


# =========================================================
# WITHDRAW APPLICATION
# =========================================================

@app.route(
    "/student/application/<int:application_id>/withdraw",
    methods=["POST"]
)
@student_required
def withdraw_application(application_id):

    conn = get_db()

    application = conn.execute("""
        SELECT id, status
        FROM applications
        WHERE id = ?
        AND student_id = ?
    """, (
        application_id,
        session["user_id"]
    )).fetchone()

    if not application:

        conn.close()

        flash(
            "Application not found.",
            "error"
        )

        return redirect(url_for("applications"))

    conn.execute("""
        UPDATE applications
        SET status = 'Withdrawn'
        WHERE id = ?
    """, (application_id,))

    conn.commit()
    conn.close()

    flash(
        "Application withdrawn.",
        "success"
    )

    return redirect(url_for("applications"))


# =========================================================
# STUDENT INTERVIEWS
# =========================================================

@app.route("/student/interviews")
@student_required
def interviews():

    user_id = session["user_id"]

    conn = get_db()

    data = conn.execute("""
        SELECT
            interviews.*,
            jobs.title AS job_title,
            companies.name AS company_name
        FROM interviews
        JOIN applications
            ON interviews.application_id = applications.id
        JOIN jobs
            ON applications.job_id = jobs.id
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        WHERE applications.student_id = ?
        ORDER BY interviews.interview_date,
                 interviews.interview_time
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "interviews.html",
        interviews=data
    )


# =========================================================
# STUDENT PREPARATION
# =========================================================

@app.route("/student/preparation")
@student_required
def preparation():

    conn = get_db()

    data = conn.execute("""
        SELECT *
        FROM preparation
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "preparation.html",
        preparation=data
    )


# =========================================================
# STUDENT SKILL GAP
# =========================================================

@app.route("/student/skill-gap")
@student_required
def skill_gap():

    user_id = session["user_id"]

    conn = get_db()

    data = conn.execute("""
        SELECT
            skill_gaps.*,
            jobs.title AS job_title,
            companies.name AS company_name
        FROM skill_gaps
        LEFT JOIN jobs
            ON skill_gaps.job_id = jobs.id
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        WHERE skill_gaps.student_id = ?
        ORDER BY skill_gaps.id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "skill_gap.html",
        skill_gaps=data
    )


# =========================================================
# STUDENT RECOMMENDATIONS
# =========================================================

@app.route("/student/recommendations")
@student_required
def recommendations():

    user_id = session["user_id"]

    conn = get_db()

    data = conn.execute("""
        SELECT *
        FROM recommendations
        WHERE student_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "recommendations.html",
        recommendations=data
    )


# =========================================================
# STUDENT NOTIFICATIONS
# =========================================================

@app.route("/student/notifications")
@student_required
def notifications():

    user_id = session["user_id"]

    conn = get_db()

    data = conn.execute("""
        SELECT *
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    return render_template(
        "notifications.html",
        notifications=data
    )


# =========================================================
# STUDENT PLACEMENT STATUS
# =========================================================

@app.route("/student/placement-status")
@student_required
def placement_status():

    user_id = session["user_id"]

    conn = get_db()

    data = conn.execute("""
        SELECT *
        FROM placement_status
        WHERE student_id = ?
    """, (user_id,)).fetchone()

    conn.close()

    return render_template(
        "placement_status.html",
        status=data
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    conn = get_db()

    students = conn.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role = 'student'
    """).fetchone()["total"]

    companies = conn.execute("""
        SELECT COUNT(*) AS total
        FROM companies
    """).fetchone()["total"]

    jobs = conn.execute("""
        SELECT COUNT(*) AS total
        FROM jobs
    """).fetchone()["total"]

    applications = conn.execute("""
        SELECT COUNT(*) AS total
        FROM applications
    """).fetchone()["total"]

    interviews = conn.execute("""
        SELECT COUNT(*) AS total
        FROM interviews
    """).fetchone()["total"]

    placed = conn.execute("""
        SELECT COUNT(*) AS total
        FROM placement_status
        WHERE status = 'Placed'
    """).fetchone()["total"]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        jobs=jobs,
        applications=applications,
        interviews=interviews,
        placed=placed
    )


# =========================================================
# ADMIN STUDENTS
# =========================================================

@app.route("/admin/students")
@admin_required
def admin_students():

    conn = get_db()

    data = conn.execute("""
        SELECT
            users.id,
            users.name,
            users.email,
            placement_status.status,
            placement_status.company_name,
            placement_status.job_title,
            placement_status.package
        FROM users
        LEFT JOIN placement_status
            ON users.id = placement_status.student_id
        WHERE users.role = 'student'
        ORDER BY users.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin_students.html"
        if os.path.exists(
            os.path.join(BASE_DIR, "templates", "admin_students.html")
        )
        else "admin_dashboard.html",
        students=data
    )


# =========================================================
# ADMIN COMPANIES
# =========================================================

@app.route(
    "/admin/companies",
    methods=["GET", "POST"]
)
@admin_required
def admin_companies():

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        location = request.form.get("location", "").strip()
        website = request.form.get("website", "").strip()
        description = request.form.get("description", "").strip()

        if not name:

            flash(
                "Company name is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO companies
                (
                    name,
                    email,
                    location,
                    website,
                    description
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                email,
                location,
                website,
                description
            ))

            conn.commit()

            flash(
                "Company added successfully.",
                "success"
            )

    data = conn.execute("""
        SELECT *
        FROM companies
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    template = (
        "admin_companies.html"
        if os.path.exists(
            os.path.join(BASE_DIR, "templates", "admin_companies.html")
        )
        else "companies.html"
    )

    return render_template(
        template,
        companies=data
    )


# =========================================================
# DELETE COMPANY
# =========================================================

@app.route(
    "/admin/company/<int:company_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_company(company_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM companies
        WHERE id = ?
    """, (company_id,))

    conn.commit()
    conn.close()

    flash(
        "Company deleted.",
        "success"
    )

    return redirect(url_for("admin_companies"))


# =========================================================
# ADMIN JOBS
# =========================================================

@app.route(
    "/admin/jobs",
    methods=["GET", "POST"]
)
@admin_required
def admin_jobs():

    conn = get_db()

    if request.method == "POST":

        company_id = request.form.get("company_id")

        if not company_id:
            company_id = None

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        skills_value = request.form.get("skills", "").strip()
        location = request.form.get("location", "").strip()
        package = request.form.get("package", "").strip()
        deadline = request.form.get("deadline", "").strip()

        try:
            min_cgpa = float(
                request.form.get("min_cgpa") or 0
            )
            max_backlogs = int(
                request.form.get("max_backlogs") or 0
            )
        except ValueError:
            min_cgpa = 0
            max_backlogs = 0

        if not title:

            flash(
                "Job title is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO jobs
                (
                    company_id,
                    title,
                    description,
                    skills,
                    location,
                    package,
                    min_cgpa,
                    max_backlogs,
                    deadline
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                title,
                description,
                skills_value,
                location,
                package,
                min_cgpa,
                max_backlogs,
                deadline
            ))

            conn.commit()

            flash(
                "Job added successfully.",
                "success"
            )

    jobs_data = conn.execute("""
        SELECT
            jobs.*,
            companies.name AS company_name
        FROM jobs
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        ORDER BY jobs.id DESC
    """).fetchall()

    companies = conn.execute("""
        SELECT *
        FROM companies
        ORDER BY name
    """).fetchall()

    conn.close()

    template = (
        "admin_jobs.html"
        if os.path.exists(
            os.path.join(BASE_DIR, "templates", "admin_jobs.html")
        )
        else "jobs.html"
    )

    return render_template(
        template,
        jobs=jobs_data,
        companies=companies
    )


# =========================================================
# DELETE JOB
# =========================================================

@app.route(
    "/admin/job/<int:job_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_job(job_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM jobs
        WHERE id = ?
    """, (job_id,))

    conn.commit()
    conn.close()

    flash(
        "Job deleted.",
        "success"
    )

    return redirect(url_for("admin_jobs"))


# =========================================================
# ADMIN APPLICATIONS
# =========================================================

@app.route("/admin/applications")
@admin_required
def admin_applications():

    conn = get_db()

    data = conn.execute("""
        SELECT
            applications.*,
            users.name AS student_name,
            users.email AS student_email,
            jobs.title AS job_title,
            companies.name AS company_name
        FROM applications
        JOIN users
            ON applications.student_id = users.id
        JOIN jobs
            ON applications.job_id = jobs.id
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        ORDER BY applications.id DESC
    """).fetchall()

    conn.close()

    template = (
        "admin_applications.html"
        if os.path.exists(
            os.path.join(BASE_DIR, "templates", "admin_applications.html")
        )
        else "applications.html"
    )

    return render_template(
        template,
        applications=data
    )


# =========================================================
# ADMIN APPLICATION STATUS
# =========================================================

@app.route(
    "/admin/application/<int:application_id>/status",
    methods=["POST"]
)
@admin_required
def update_application_status(application_id):

    status = request.form.get(
        "status",
        "Applied"
    ).strip()

    allowed_statuses = [
        "Applied",
        "Shortlisted",
        "Rejected",
        "Selected",
        "Withdrawn"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid application status.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )

    conn = get_db()

    application = conn.execute("""
        SELECT
            student_id
        FROM applications
        WHERE id = ?
    """, (application_id,)).fetchone()

    if not application:

        conn.close()

        flash(
            "Application not found.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )

    conn.execute("""
        UPDATE applications
        SET status = ?
        WHERE id = ?
    """, (
        status,
        application_id
    ))

    conn.execute("""
        INSERT INTO notifications
        (
            user_id,
            title,
            message
        )
        VALUES (?, ?, ?)
    """, (
        application["student_id"],
        "Application Update",
        "Your application status is now: " + status
    ))

    conn.commit()
    conn.close()

    flash(
        "Application status updated.",
        "success"
    )

    return redirect(
        url_for("admin_applications")
    )


# =========================================================
# ADMIN INTERVIEWS
# =========================================================

@app.route(
    "/admin/interviews",
    methods=["GET", "POST"]
)
@admin_required
def admin_interviews():

    conn = get_db()

    if request.method == "POST":

        application_id = request.form.get("application_id")
        interview_date = request.form.get("interview_date")
        interview_time = request.form.get("interview_time")
        interview_type = request.form.get("interview_type")
        round_name = request.form.get("round")
        meeting_link = request.form.get("meeting_link")

        if not application_id:

            flash(
                "Application is required.",
                "error"
            )

        else:

            application = conn.execute("""
                SELECT student_id
                FROM applications
                WHERE id = ?
            """, (application_id,)).fetchone()

            if not application:

                flash(
                    "Application not found.",
                    "error"
                )

            else:

                conn.execute("""
                    INSERT INTO interviews
                    (
                        application_id,
                        interview_date,
                        interview_time,
                        interview_type,
                        round,
                        meeting_link
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    application_id,
                    interview_date,
                    interview_time,
                    interview_type,
                    round_name,
                    meeting_link
                ))

                conn.execute("""
                    INSERT INTO notifications
                    (
                        user_id,
                        title,
                        message
                    )
                    VALUES (?, ?, ?)
                """, (
                    application["student_id"],
                    "Interview Scheduled",
                    "Your interview has been scheduled."
                ))

                conn.commit()

                flash(
                    "Interview scheduled successfully.",
                    "success"
                )

    interviews_data = conn.execute("""
        SELECT
            interviews.*,
            users.name AS student_name,
            jobs.title AS job_title,
            companies.name AS company_name
        FROM interviews
        JOIN applications
            ON interviews.application_id = applications.id
        JOIN users
            ON applications.student_id = users.id
        JOIN jobs
            ON applications.job_id = jobs.id
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        ORDER BY interviews.interview_date,
                 interviews.interview_time
    """).fetchall()

    applications_data = conn.execute("""
        SELECT
            applications.id,
            users.name AS student_name,
            jobs.title AS job_title,
            companies.name AS company_name
        FROM applications
        JOIN users
            ON applications.student_id = users.id
        JOIN jobs
            ON applications.job_id = jobs.id
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        WHERE applications.status IN
            ('Applied', 'Shortlisted', 'Selected')
        ORDER BY applications.id DESC
    """).fetchall()

    conn.close()

    template = (
        "admin_interviews.html"
        if os.path.exists(
            os.path.join(BASE_DIR, "templates", "admin_interviews.html")
        )
        else "interviews.html"
    )

    return render_template(
        template,
        interviews=interviews_data,
        applications=applications_data
    )


# =========================================================
# ADMIN INTERVIEW RESULT
# =========================================================

@app.route(
    "/admin/interview/<int:interview_id>/result",
    methods=["POST"]
)
@admin_required
def update_interview_result(interview_id):

    result = request.form.get(
        "result",
        "Pending"
    )

    feedback = request.form.get(
        "feedback",
        ""
    )

    conn = get_db()

    interview = conn.execute("""
        SELECT application_id
        FROM interviews
        WHERE id = ?
    """, (interview_id,)).fetchone()

    if not interview:

        conn.close()

        flash(
            "Interview not found.",
            "error"
        )

        return redirect(url_for("admin_interviews"))

    conn.execute("""
        UPDATE interviews
        SET result = ?,
            feedback = ?
        WHERE id = ?
    """, (
        result,
        feedback,
        interview_id
    ))

    application = conn.execute("""
        SELECT student_id
        FROM applications
        WHERE id = ?
    """, (
        interview["application_id"],
    )).fetchone()

    if application:

        conn.execute("""
            INSERT INTO notifications
            (
                user_id,
                title,
                message
            )
            VALUES (?, ?, ?)
        """, (
            application["student_id"],
            "Interview Result Updated",
            "Your interview result is: " + result
        ))

    conn.commit()
    conn.close()

    flash(
        "Interview result updated.",
        "success"
    )

    return redirect(url_for("admin_interviews"))


# =========================================================
# ADMIN PREPARATION
# =========================================================

@app.route(
    "/admin/preparation",
    methods=["GET", "POST"]
)
@admin_required
def admin_preparation():

    conn = get_db()

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        resource_link = request.form.get("resource_link", "").strip()

        if not title:

            flash(
                "Preparation title is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO preparation
                (
                    title,
                    category,
                    description,
                    resource_link
                )
                VALUES (?, ?, ?, ?)
            """, (
                title,
                category,
                description,
                resource_link
            ))

            conn.commit()

            flash(
                "Preparation resource added.",
                "success"
            )

    data = conn.execute("""
        SELECT *
        FROM preparation
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    template = (
        "admin_preparation.html"
        if os.path.exists(
            os.path.join(BASE_DIR, "templates", "admin_preparation.html")
        )
        else "preparation.html"
    )

    return render_template(
        template,
        preparation=data
    )


@app.route(
    "/admin/preparation/<int:item_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_preparation(item_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM preparation
        WHERE id = ?
    """, (item_id,))

    conn.commit()
    conn.close()

    flash(
        "Preparation resource deleted.",
        "success"
    )

    return redirect(
        url_for("admin_preparation")
    )


# =========================================================
# ADMIN PLACEMENT STATUS
# =========================================================

@app.route(
    "/admin/placement-status",
    methods=["GET", "POST"]
)
@admin_required
def admin_placement_status():

    conn = get_db()

    if request.method == "POST":

        student_id = request.form.get("student_id")
        status = request.form.get(
            "status",
            "Not Placed"
        )

        company_name = request.form.get("company_name")
        job_title = request.form.get("job_title")
        package = request.form.get("package")

        student = conn.execute("""
            SELECT id
            FROM users
            WHERE id = ?
            AND role = 'student'
        """, (student_id,)).fetchone()

        if not student:

            flash(
                "Student not found.",
                "error"
            )

        else:

            existing = conn.execute("""
                SELECT id
                FROM placement_status
                WHERE student_id = ?
            """, (student_id,)).fetchone()

            if existing:

                conn.execute("""
                    UPDATE placement_status
                    SET status = ?,
                        company_name = ?,
                        job_title = ?,
                        package = ?
                    WHERE student_id = ?
                """, (
                    status,
                    company_name,
                    job_title,
                    package,
                    student_id
                ))

            else:

                conn.execute("""
                    INSERT INTO placement_status
                    (
                        student_id,
                        status,
                        company_name,
                        job_title,
                        package
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    student_id,
                    status,
                    company_name,
                    job_title,
                    package
                ))

            conn.execute("""
                INSERT INTO notifications
                (
                    user_id,
                    title,
                    message
                )
                VALUES (?, ?, ?)
            """, (
                student_id,
                "Placement Status Updated",
                "Your placement status is now: " + status
            ))

            conn.commit()

            flash(
                "Placement status updated.",
                "success"
            )

    students = conn.execute("""
        SELECT
            users.id,
            users.name,
            users.email,
            placement_status.status,
            placement_status.company_name,
            placement_status.job_title,
            placement_status.package
        FROM users
        LEFT JOIN placement_status
            ON users.id = placement_status.student_id
        WHERE users.role = 'student'
        ORDER BY users.name
    """).fetchall()

    conn.close()

    template = (
        "admin_placement_status.html"
        if os.path.exists(
            os.path.join(
                BASE_DIR,
                "templates",
                "admin_placement_status.html"
            )
        )
        else "placement_status.html"
    )

    return render_template(
        template,
        students=students
    )


# =========================================================
# ADMIN SKILL GAP
# =========================================================

@app.route(
    "/admin/skill-gap",
    methods=["GET", "POST"]
)
@admin_required
def admin_skill_gap():

    conn = get_db()

    if request.method == "POST":

        student_id = request.form.get("student_id")
        job_id = request.form.get("job_id")
        missing_skills = request.form.get("missing_skills")

        try:
            gap_percentage = float(
                request.form.get("gap_percentage") or 0
            )
        except ValueError:
            gap_percentage = 0

        conn.execute("""
            INSERT INTO skill_gaps
            (
                student_id,
                job_id,
                missing_skills,
                gap_percentage
            )
            VALUES (?, ?, ?, ?)
        """, (
            student_id,
            job_id,
            missing_skills,
            gap_percentage
        ))

        conn.commit()

        flash(
            "Skill gap added.",
            "success"
        )

    students = conn.execute("""
        SELECT id, name
        FROM users
        WHERE role = 'student'
        ORDER BY name
    """).fetchall()

    jobs_data = conn.execute("""
        SELECT
            jobs.id,
            jobs.title,
            companies.name AS company_name
        FROM jobs
        LEFT JOIN companies
            ON jobs.company_id = companies.id
        ORDER BY jobs.title
    """).fetchall()

    gaps = conn.execute("""
        SELECT
            skill_gaps.*,
            users.name AS student_name,
            jobs.title AS job_title
        FROM skill_gaps
        JOIN users
            ON skill_gaps.student_id = users.id
        JOIN jobs
            ON skill_gaps.job_id = jobs.id
        ORDER BY skill_gaps.id DESC
    """).fetchall()

    conn.close()

    template = (
        "admin_skill_gap.html"
        if os.path.exists(
            os.path.join(BASE_DIR, "templates", "admin_skill_gap.html")
        )
        else "skill_gap.html"
    )

    return render_template(
        template,
        students=students,
        jobs=jobs_data,
        skill_gaps=gaps
    )


# =========================================================
# ADMIN RECOMMENDATIONS
# =========================================================

@app.route(
    "/admin/recommendations",
    methods=["GET", "POST"]
)
@admin_required
def admin_recommendations():

    conn = get_db()

    if request.method == "POST":

        student_id = request.form.get("student_id")
        title = request.form.get("title", "").strip()
        description = request.form.get(
            "description",
            ""
        ).strip()

        if not title:

            flash(
                "Recommendation title is required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO recommendations
                (
                    student_id,
                    title,
                    description
                )
                VALUES (?, ?, ?)
            """, (
                student_id,
                title,
                description
            ))

            conn.execute("""
                INSERT INTO notifications
                (
                    user_id,
                    title,
                    message
                )
                VALUES (?, ?, ?)
            """, (
                student_id,
                "New Recommendation",
                title
            ))

            conn.commit()

            flash(
                "Recommendation added.",
                "success"
            )

    students = conn.execute("""
        SELECT id, name
        FROM users
        WHERE role = 'student'
        ORDER BY name
    """).fetchall()

    recommendations_data = conn.execute("""
        SELECT
            recommendations.*,
            users.name AS student_name
        FROM recommendations
        JOIN users
            ON recommendations.student_id = users.id
        ORDER BY recommendations.id DESC
    """).fetchall()

    conn.close()

    template = (
        "admin_recommendations.html"
        if os.path.exists(
            os.path.join(
                BASE_DIR,
                "templates",
                "admin_recommendations.html"
            )
        )
        else "recommendations.html"
    )

    return render_template(
        template,
        students=students,
        recommendations=recommendations_data
    )


# =========================================================
# ADMIN NOTIFICATIONS
# =========================================================

@app.route(
    "/admin/notifications",
    methods=["GET", "POST"]
)
@admin_required
def admin_notifications():

    conn = get_db()

    if request.method == "POST":

        user_id = request.form.get("user_id")
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()

        if not title or not message:

            flash(
                "Title and message are required.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO notifications
                (
                    user_id,
                    title,
                    message
                )
                VALUES (?, ?, ?)
            """, (
                user_id,
                title,
                message
            ))

            conn.commit()

            flash(
                "Notification sent.",
                "success"
            )

    students = conn.execute("""
        SELECT id, name, email
        FROM users
        WHERE role = 'student'
        ORDER BY name
    """).fetchall()

    conn.close()

    template = (
        "admin_notifications.html"
        if os.path.exists(
            os.path.join(
                BASE_DIR,
                "templates",
                "admin_notifications.html"
            )
        )
        else "notifications.html"
    )

    return render_template(
        template,
        students=students
    )


# =========================================================
# ADMIN DELETE STUDENT
# =========================================================

@app.route(
    "/admin/student/<int:student_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_student(student_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM users
        WHERE id = ?
        AND role = 'student'
    """, (student_id,))

    conn.commit()
    conn.close()

    flash(
        "Student deleted.",
        "success"
    )

    return redirect(
        url_for("admin_students")
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "application": "Placement Management System"
    }


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):

    return render_template(
        "500.html"
    ), 500


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    create_database()

    print("=" * 60)
    print("PLACEMENT MANAGEMENT SYSTEM")
    print("=" * 60)
    print()
    print("ADMIN LOGIN")
    print("Email    : admin@gmail.com")
    print("Password : admin123")
    print()
    print("Register : http://127.0.0.1:5000/register")
    print("Login    : http://127.0.0.1:5000/login")
    print()
    print("Application:")
    print("http://127.0.0.1:5000")
    print("=" * 60)

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
