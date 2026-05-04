import os
import sqlite3
import json
import uuid
from datetime import datetime
from functools import wraps
import requests
from io import BytesIO
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g, send_file
)

app = Flask(__name__)
app.secret_key = "elearn_demo_secret_key_not_for_prod"
EXAM_CACHE = {}

DATABASE = os.path.join(os.path.dirname(__file__), "elearn.db")

GEMINI_API_KEY = "AIzaSyCQXW0Ncj821t7qlsgb_5gMrq2fBUBezIY"

# ─────────────────────────────────────────────
#  COURSES & LESSONS DATA
# ─────────────────────────────────────────────
STATIC_COURSES = [
    {"id": "course1", "title": "Web Development Fundamentals", "desc": "Start your web journey with HTML, CSS, and JavaScript. Build real projects from day one.", "emoji": "globe", "color": "#0e4a7a", "level": "beginner", "lessons_count": 3, "hours": 6, "rating": 4.9, "reviews": 320, "free": True, "category": "development",
     "lessons": [
         {"id": "l1", "title": "Introduction to HTML", "desc": "HTML (HyperText Markup Language) is the foundation of every web page. In this lesson you will learn:\n\n• What HTML is and why it matters\n• The basic structure of an HTML document: <!DOCTYPE>, <html>, <head>, <body>\n• Common HTML tags: headings (h1-h6), paragraphs (p), links (a), images (img)\n• Lists: ordered (ol) and unordered (ul)\n• Forms and inputs: <form>, <input>, <button>\n• Semantic HTML: <header>, <nav>, <main>, <section>, <article>, <footer>\n• HTML attributes: id, class, href, src, alt\n• Nesting elements correctly\n• Comments in HTML <!-- like this -->\n\nKey concept: HTML describes the structure and content of a web page. It is NOT a programming language — it is a markup language."},
         {"id": "l2", "title": "CSS Styling Basics", "desc": "CSS (Cascading Style Sheets) controls the visual presentation of your HTML.\n\n• Selectors: element, class (.), id (#), attribute\n• The box model: margin, border, padding, content\n• Colors: hex, rgb, hsl, named colors\n• Typography: font-family, font-size, font-weight, line-height\n• Flexbox: display:flex, justify-content, align-items, gap\n• CSS Grid: grid-template-columns, grid-template-rows\n• Responsive design with media queries\n• CSS Variables: --my-color: #ff0000\n• Transitions and basic animations\n• Pseudo-classes: :hover, :focus, :nth-child\n\nKey concept: CSS cascades — later rules override earlier ones. Specificity determines which rule wins."},
         {"id": "l3", "title": "JavaScript Basics", "desc": "JavaScript adds interactivity and logic to your web pages.\n\n• Variables: var, let, const\n• Data types: string, number, boolean, null, undefined, object, array\n• Operators: arithmetic (+,-,*,/), comparison (===,!==,<,>), logical (&&,||,!)\n• Control flow: if/else, switch, ternary operator\n• Loops: for, while, forEach, for...of\n• Functions: declaration, expression, arrow functions\n• DOM manipulation: querySelector, getElementById, addEventListener\n• Events: click, input, submit, keydown\n• Fetch API for HTTP requests\n• Async/Await and Promises\n\nKey concept: JavaScript runs in the browser and can modify the page dynamically without reloading."},
     ]},
    {"id": "course2", "title": "Python for Data Science", "desc": "Learn Python programming and apply it to real-world data analysis and visualization tasks.", "emoji": "terminal", "color": "#3a1a6a", "level": "intermediate", "lessons_count": 2, "hours": 10, "rating": 4.8, "reviews": 218, "free": False, "category": "data",
     "lessons": [
         {"id": "l1", "title": "Python Fundamentals", "desc": "Python is a high-level, interpreted programming language known for its clear syntax.\n\n• Installing Python and setting up a virtual environment\n• Variables and data types: int, float, str, bool, list, dict, tuple, set\n• Operators and expressions\n• String formatting: f-strings, .format()\n• Conditional statements: if, elif, else\n• Loops: for, while, list comprehensions\n• Functions: def, parameters, return, *args, **kwargs\n• Modules and imports\n• File I/O: open(), read(), write()\n• Exception handling: try/except/finally\n\nKey concept: Python uses indentation (whitespace) to define code blocks — there are no curly braces."},
         {"id": "l2", "title": "NumPy & Pandas", "desc": "NumPy and Pandas are the core libraries for data science in Python.\n\nNumPy:\n• Arrays: np.array(), shape, dtype\n• Array operations: slicing, indexing, broadcasting\n• Math functions: np.sum(), np.mean(), np.std()\n\nPandas:\n• Series and DataFrame\n• Reading data: pd.read_csv(), pd.read_excel()\n• Exploring data: .head(), .info(), .describe()\n• Selecting data: loc, iloc, boolean indexing\n• Handling missing data: .isnull(), .dropna(), .fillna()\n• Grouping and aggregating: .groupby(), .agg()\n\nKey concept: A DataFrame is like a spreadsheet in Python — rows are observations, columns are variables."},
     ]},
    {"id": "course3", "title": "UI/UX Design Essentials", "desc": "Master design principles, wireframing, prototyping, and user research methodologies.", "emoji": "palette", "color": "#0e5a3a", "level": "beginner", "lessons_count": 1, "hours": 8, "rating": 4.7, "reviews": 195, "free": True, "category": "design",
     "lessons": [
         {"id": "l1", "title": "Design Principles", "desc": "Great UI/UX is built on timeless design principles.\n\n• Visual Hierarchy: Guide the user's eye using size, weight, color\n• Contrast: Ensure readability — WCAG AA requires 4.5:1 ratio for text\n• Alignment: Create order and structure\n• Proximity: Group related elements\n• Repetition: Establish consistency\n• White space (negative space): Give elements room to breathe\n• Color theory: Primary/secondary/tertiary, complementary, analogous, triadic\n• Typography rules: Never use more than 2-3 typefaces\n• Gestalt principles: Similarity, continuity, closure\n\nKey concept: Good design is invisible — users accomplish their goals without noticing the interface."},
     ]},
    {"id": "course4", "title": "React & Modern JavaScript", "desc": "Build powerful single-page applications with React, hooks, and the modern JS ecosystem.", "emoji": "code-2", "color": "#1a3a5a", "level": "intermediate", "lessons_count": 2, "hours": 12, "rating": 4.9, "reviews": 410, "free": False, "category": "development",
     "lessons": [
         {"id": "l1", "title": "React Fundamentals", "desc": "React is a JavaScript library for building user interfaces.\n\n• JSX syntax and Babel transpilation\n• Creating and nesting components\n• Props: passing data down to child components\n• State with useState hook\n• Rendering lists with .map() and key prop\n• Handling events in React\n• Conditional rendering\n• Component lifecycle and useEffect\n• Basic form handling with controlled inputs\n\nKey concept: React uses a virtual DOM to efficiently update only the parts of the UI that change."},
         {"id": "l2", "title": "Hooks & State Management", "desc": "React hooks make it easy to add state and side effects to function components.\n\n• useState for local component state\n• useEffect for side effects (data fetching, subscriptions)\n• useContext for sharing state without prop drilling\n• useReducer for complex state logic\n• Custom hooks: extracting reusable logic\n• React Context API for global state\n• Introduction to Zustand / Redux Toolkit\n\nKey concept: Hooks let you use state and React features in functional components without writing a class."},
     ]},
    {"id": "course5", "title": "Machine Learning Basics", "desc": "An introduction to ML concepts, algorithms, and model training with scikit-learn.", "emoji": "cpu", "color": "#2a1a4a", "level": "advanced", "lessons_count": 1, "hours": 15, "rating": 4.6, "reviews": 140, "free": False, "category": "data",
     "lessons": [
         {"id": "l1", "title": "Introduction to Machine Learning", "desc": "Machine learning enables computers to learn from data without explicit programming.\n\n• Supervised vs. unsupervised vs. reinforcement learning\n• Classification vs. regression problems\n• Training set, validation set, test set\n• Overfitting and underfitting\n• Common algorithms: Linear Regression, Logistic Regression, Decision Trees, KNN, SVM\n• Feature engineering and scaling\n• Model evaluation: accuracy, precision, recall, F1, ROC-AUC\n• scikit-learn pipeline: fit, transform, predict\n\nKey concept: The goal of machine learning is to find patterns in data that generalize well to new, unseen data."},
     ]},
    {"id": "course6", "title": "Digital Marketing 101", "desc": "From SEO and social media to email campaigns and analytics — learn modern marketing.", "emoji": "megaphone", "color": "#4a2a0a", "level": "beginner", "lessons_count": 1, "hours": 7, "rating": 4.5, "reviews": 162, "free": True, "category": "marketing",
     "lessons": [
         {"id": "l1", "title": "Digital Marketing Fundamentals", "desc": "Digital marketing encompasses all marketing efforts that use an electronic device or the internet.\n\n• SEO: on-page and off-page optimization, keywords, backlinks\n• Content marketing: blogging, video, podcasts\n• Social media marketing: organic vs. paid, platform differences\n• Email marketing: list building, open rates, CTR, automation\n• Pay-per-click (PPC): Google Ads, Meta Ads, bidding strategies\n• Analytics: Google Analytics 4, key metrics (bounce rate, session duration, conversions)\n• Conversion Rate Optimization (CRO)\n• Marketing funnel: awareness → interest → desire → action\n\nKey concept: In digital marketing, everything is measurable. Data drives decisions."},
     ]},
]

COURSES_BY_ID = {c["id"]: c for c in STATIC_COURSES}

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        );
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            color TEXT DEFAULT 'cyan',
            date TEXT
        );
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            emoji TEXT DEFAULT 'book',
            color TEXT DEFAULT '#1a2a4a',
            level TEXT DEFAULT 'beginner',
            hours INTEGER DEFAULT 0,
            category TEXT DEFAULT 'general',
            created_by INTEGER,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            lesson_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            visited_at TEXT NOT NULL,
            UNIQUE(user_id, lesson_id)
        );
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            taken_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            quiz_score REAL NOT NULL,
            certificate_id TEXT UNIQUE NOT NULL,
            completed_at TEXT NOT NULL,
            UNIQUE(user_id, course_id)
        );
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id TEXT,
            score INTEGER,
            total INTEGER,
            percentage REAL,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS exam_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id TEXT,
            percentage REAL,
            certificate_id TEXT UNIQUE,
            created_at TEXT,
            UNIQUE(user_id, course_id)
        );
    """)
    # Seed demo users
    users = [
        ("student@elearn.com", "student123", "Alex Johnson",  "student"),
        ("demo@elearn.com",    "demo123",    "Demo User",     "student"),
        ("admin@elearn.com",   "admin123",   "Admin Account", "admin"),
    ]
    for email, pw, name, role in users:
        try:
            db.execute("INSERT INTO users (email,password,name,role) VALUES (?,?,?,?)", (email, pw, name, role))
        except sqlite3.IntegrityError:
            pass  # already seeded
            
    # Seed static courses into DB
    course1 = db.execute("SELECT id FROM courses WHERE id='course1'").fetchone()
    if not course1:
        for c in STATIC_COURSES:
            db.execute("INSERT INTO courses (id, title, description, emoji, color, level, hours, category, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (c["id"], c["title"], c.get("desc", ""), c.get("emoji", "book"), c.get("color", "#0e4a7a"), c.get("level", "beginner"), c.get("hours", 0), c.get("category", "general"), 1, datetime.now().isoformat()))
            for idx, l in enumerate(c.get("lessons", [])):
                unique_lesson_id = f"{c['id']}_{l['id']}"
                db.execute("INSERT INTO lessons (id, course_id, title, content, lesson_order) VALUES (?, ?, ?, ?, ?)",
                           (unique_lesson_id, c["id"], l["title"], l.get("desc", ""), idx))

    db.commit()
    db.close()

# ─────────────────────────────────────────────
#  AUTH HELPERS
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

def current_user():
    return {
        "id":    session.get("user_id"),
        "name":  session.get("name"),
        "email": session.get("email"),
        "role":  session.get("role"),
    }

def format_date(value, fallback=""):
    if not value:
        return fallback
    try:
        return datetime.fromisoformat(value).strftime("%B %-d, %Y")
    except ValueError:
        try:
            return datetime.fromisoformat(value).strftime("%B %#d, %Y")
        except ValueError:
            return fallback or value

app.jinja_env.filters["pretty_date"] = format_date

def get_course_progress(user_id, course_id):
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,)).fetchone()[0]
    if total == 0:
        return 0
    visited = db.execute(
        """
        SELECT COUNT(DISTINCT p.lesson_id)
        FROM progress p
        JOIN lessons l ON l.id = p.lesson_id
        WHERE p.user_id=? AND l.course_id=?
        """,
        (user_id, course_id),
    ).fetchone()[0]
    return int(round((visited / total) * 100))

def get_user_stats(user_id):
    db = get_db()
    total_lessons_completed = db.execute(
        "SELECT COUNT(DISTINCT lesson_id) FROM progress WHERE user_id=?",
        (user_id,),
    ).fetchone()[0]
    total_courses_started = db.execute(
        "SELECT COUNT(DISTINCT course_id) FROM progress WHERE user_id=?",
        (user_id,),
    ).fetchone()[0]
    rows = db.execute("SELECT id FROM courses").fetchall()
    courses_with_full_progress = sum(1 for row in rows if get_course_progress(user_id, row["id"]) == 100)
    quizzes_passed = db.execute(
        "SELECT COUNT(*) FROM quiz_results WHERE user_id=? AND percentage>=70",
        (user_id,),
    ).fetchone()[0]
    certificates = db.execute(
        "SELECT COUNT(*) FROM completions WHERE user_id=?",
        (user_id,),
    ).fetchone()[0]
    return {
        "total_lessons_completed": total_lessons_completed,
        "total_courses_started": total_courses_started,
        "courses_with_full_progress": courses_with_full_progress,
        "quizzes_passed": quizzes_passed,
        "certificates": certificates,
    }

def all_lessons_visited(user_id, course_id):
    return get_course_progress(user_id, course_id) == 100

def mark_course_lessons_completed(user_id, course_id):
    db = get_db()
    lessons = db.execute("SELECT id FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    now = datetime.utcnow().isoformat()
    for lesson_row in lessons:
        db.execute(
            "INSERT OR IGNORE INTO progress (user_id, course_id, lesson_id, visited_at) VALUES (?,?,?,?)",
            (user_id, course_id, lesson_row["id"], now),
        )
    return len(lessons)

def ensure_certificates_for_user(user_id):
    db = get_db()
    passed_courses = db.execute(
        """
        SELECT course_id, MAX(percentage) AS best_score
        FROM quiz_results
        WHERE user_id=? AND percentage>=70
        GROUP BY course_id
        """,
        (user_id,),
    ).fetchall()
    created = 0
    for row in passed_courses:
        existing = db.execute(
            "SELECT id FROM completions WHERE user_id=? AND course_id=?",
            (user_id, row["course_id"]),
        ).fetchone()
        if existing:
            continue
        mark_course_lessons_completed(user_id, row["course_id"])
        if get_course_progress(user_id, row["course_id"]) == 100:
            db.execute(
                "INSERT OR IGNORE INTO completions (user_id, course_id, quiz_score, certificate_id, completed_at) VALUES (?,?,?,?,?)",
                (user_id, row["course_id"], row["best_score"], str(uuid.uuid4()), datetime.utcnow().isoformat()),
            )
            created += 1
    if created:
        db.commit()
    return created

def anonymize_name(name):
    parts = (name or "Student").split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0].upper()}."

def extract_json_object(text):
    if not text:
        return None
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None

def get_course_with_lessons(course_id):
    db = get_db()
    c = db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not c:
        return None
    lessons_rows = db.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_order", (course_id,)).fetchall()
    return {
        "id": c["id"],
        "title": c["title"],
        "emoji": c["emoji"],
        "lessons": [{"id": l["id"], "title": l["title"], "content": l["content"]} for l in lessons_rows],
    }

def fallback_exam_questions(topic, lesson_text):
    base = [
        ("What is the main purpose of studying this course?", ["To build practical knowledge", "To avoid practice", "To memorize random facts", "To skip examples"], 0),
        ("Which learning habit is most useful for this course?", ["Practicing with examples", "Ignoring feedback", "Reading titles only", "Avoiding review"], 0),
        ("What should a student do after learning a new concept?", ["Apply it in a small exercise", "Forget the definition", "Close the lesson", "Skip the summary"], 0),
        ("Why are key concepts important?", ["They help connect theory to practice", "They remove the need to learn", "They replace exercises", "They are only decorative"], 0),
    ]
    questions = []
    for i in range(20):
        template = base[i % len(base)]
        questions.append({
            "question": f"{template[0]} ({topic}, item {i + 1})",
            "options": template[1],
            "correct": template[2],
        })
    return questions

def normalize_exam_questions(raw_questions, topic, lesson_text):
    questions = []
    if isinstance(raw_questions, list):
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            options = item.get("options", [])
            correct = item.get("correct", None)
            if not question or not isinstance(options, list) or len(options) != 4:
                continue
            try:
                correct = int(correct)
            except (TypeError, ValueError):
                continue
            if correct < 0 or correct > 3:
                continue
            questions.append({
                "question": question,
                "options": [str(opt).strip() for opt in options],
                "correct": correct,
            })
            if len(questions) == 20:
                break
    if len(questions) < 20:
        questions = fallback_exam_questions(topic, lesson_text)
    return questions[:20]

def public_exam_questions(questions):
    return [{"question": q["question"], "options": q["options"]} for q in questions]

# ─────────────────────────────────────────────
#  GEMINI BACKEND HELPERS
# ─────────────────────────────────────────────
def call_gemini(prompt, api_key=None, temperature=0.4, max_tokens=600):
    key_to_use = api_key if api_key else GEMINI_API_KEY
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key_to_use}"
    try:
        print(f"DEBUG: sending request to Gemini API (URL length: {len(gemini_url)})")
        resp = requests.post(
            gemini_url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            },
            timeout=30,
        )
        print("DEBUG: Gemini API response status:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("DEBUG: Exception in call_gemini:", str(e))
        if 'resp' in locals() and hasattr(resp, 'text'):
            print("DEBUG: Gemini API response text:", resp.text)
        return None

# ─────────────────────────────────────────────
#  ROUTES — PUBLIC
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("landing"))

@app.route("/landing")
def landing():
    db = get_db()
    featured = db.execute("SELECT * FROM courses ORDER BY created_at ASC LIMIT 3").fetchall()
    return render_template("landing.html", courses=featured)

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["name"]    = user["name"]
            session["email"]   = user["email"]
            session["role"]    = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))
            
        db = get_db()
        # Check if email exists
        existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("register"))
            
        # Create user
        db.execute("INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, 'student')", (email, password, name))
        db.commit()
        
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["name"]    = user["name"]
            session["email"]   = user["email"]
            session["role"]    = user["role"]
        
        flash("Account created successfully! Welcome to E-Learn Pro.", "success")
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─────────────────────────────────────────────
#  ROUTES — STUDENT
# ─────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user_id = session["user_id"]
    ensure_certificates_for_user(user_id)
    notes_count = db.execute("SELECT COUNT(*) FROM notes WHERE user_id=?", (user_id,)).fetchone()[0]
    stats = get_user_stats(user_id)
    courses_rows = db.execute("SELECT * FROM courses ORDER BY created_at ASC").fetchall()
    courses = []
    for c in courses_rows:
        lessons_rows = db.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_order", (c["id"],)).fetchall()
        courses.append({
            "id": c["id"], "title": c["title"], "desc": c["description"],
            "emoji": c["emoji"], "color": c["color"], "level": c["level"],
            "lessons_count": len(lessons_rows), "hours": c["hours"],
            "category": c["category"], "progress": get_course_progress(user_id, c["id"]),
            "lessons": [{"id": l["id"], "title": l["title"], "desc": l["content"]} for l in lessons_rows],
        })
    recently_visited = db.execute(
        """
        SELECT p.course_id, p.lesson_id, p.visited_at, c.title AS course_title,
               c.emoji AS course_emoji, l.title AS lesson_title
        FROM progress p
        JOIN courses c ON c.id = p.course_id
        JOIN lessons l ON l.id = p.lesson_id
        WHERE p.user_id=?
        ORDER BY p.visited_at DESC
        LIMIT 3
        """,
        (user_id,),
    ).fetchall()
    recommended = [c for c in courses if c["progress"] == 0][:3]
    continue_course = next((c for c in courses if c["id"] == recently_visited[0]["course_id"]), None) if recently_visited else None
    if continue_course is None and courses:
        continue_course = courses[0]
    return render_template(
        "dashboard.html", user=current_user(), notes_count=notes_count, courses=courses[:6],
        stats=stats, real_lessons_completed=stats["total_lessons_completed"],
        real_quizzes_passed=stats["quizzes_passed"], real_certificates=stats["certificates"],
        recently_visited=recently_visited, recommended=recommended, continue_course=continue_course,
    )

@app.route("/courses")
@login_required
def courses():
    level  = request.args.get("level", "all")
    search = request.args.get("q", "").lower()
    
    db = get_db()
    user_id = session["user_id"]
    db_courses = db.execute("SELECT * FROM courses ORDER BY created_at DESC").fetchall()
    all_courses = []
    for c in db_courses:
        lessons_rows = db.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_order", (c["id"],)).fetchall()
        all_courses.append({
            "id": c["id"], "title": c["title"], "desc": c["description"],
            "emoji": c["emoji"], "color": c["color"], "level": c["level"],
            "lessons_count": len(lessons_rows), "hours": c["hours"],
            "rating": 5.0, "reviews": 0, "free": True,
            "category": c["category"], "progress": get_course_progress(user_id, c["id"]), "lessons": [
                {"id": l["id"], "title": l["title"], "desc": l["content"]}
                for l in lessons_rows
            ],
        })
    if level != "all":
        all_courses = [c for c in all_courses if c["level"] == level]
    if search:
        all_courses = [c for c in all_courses if search in c["title"].lower() or search in c["desc"].lower()]
    return render_template("courses.html", user=current_user(), courses=all_courses, level=level, search=search)

@app.route("/lesson/<course_id>")
@login_required
def lesson(course_id):
    lesson_idx = int(request.args.get("lesson", 0))
    db = get_db()
    c = db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not c:
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))
    lessons_rows = db.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_order", (course_id,)).fetchall()
    course = {
        "id": c["id"], "title": c["title"], "desc": c["description"],
        "emoji": c["emoji"], "color": c["color"], "level": c["level"],
        "category": c["category"], "lessons": [
            {"id": l["id"], "title": l["title"], "desc": l["content"]}
            for l in lessons_rows
        ],
    }
    lessons = course.get("lessons", [])
    if not lessons:
        flash("This course has no lessons yet.", "info")
        return redirect(url_for("courses"))
    lesson_idx = min(lesson_idx, len(lessons) - 1)
    current_lesson = lessons[lesson_idx]
    db.execute(
        "INSERT OR IGNORE INTO progress (user_id, course_id, lesson_id, visited_at) VALUES (?,?,?,?)",
        (session["user_id"], course_id, current_lesson["id"], datetime.utcnow().isoformat()),
    )
    db.commit()
    visited_rows = db.execute(
        "SELECT lesson_id FROM progress WHERE user_id=? AND course_id=?",
        (session["user_id"], course_id),
    ).fetchall()
    visited_lessons = {row["lesson_id"] for row in visited_rows}
    course_progress = get_course_progress(session["user_id"], course_id)
    completion = db.execute(
        "SELECT * FROM completions WHERE user_id=? AND course_id=?",
        (session["user_id"], course_id),
    ).fetchone()
    pdf_path = os.path.join(app.root_path, "static", "pdfs", f"{course_id}.pdf")
    has_pdf = os.path.exists(pdf_path)

    return render_template("lesson.html", user=current_user(), course=course, lesson=current_lesson,
                           lesson_idx=lesson_idx, total_lessons=len(lessons), has_pdf=has_pdf,
                           visited_lessons=visited_lessons, course_progress=course_progress,
                           completion=completion)

@app.route("/quiz/<course_id>")
@login_required
def quiz(course_id):
    db = get_db()
    c = db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if c:
        course = {"id": c["id"], "title": c["title"], "emoji": c["emoji"]}
    else:
        course = {"id": course_id, "title": "General Knowledge", "emoji": "book"}
    return render_template("quiz.html", user=current_user(), course=course)

@app.route("/exam/<course_id>")
@login_required
def exam(course_id):
    course = get_course_with_lessons(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))
    return render_template("exam.html", user=current_user(), course=course)

@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "delete":
            note_id = request.form.get("note_id")
            db.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, session["user_id"]))
            db.commit()
            flash("Note deleted.", "info")
        else:
            title   = request.form.get("title", "").strip() or "Untitled"
            content = request.form.get("content", "").strip()
            color   = request.form.get("color", "cyan")
            if content:
                note_id = str(uuid.uuid4())
                db.execute(
                    "INSERT INTO notes (id, user_id, title, content, color, date) VALUES (?,?,?,?,?,?)",
                    (note_id, session["user_id"], title, content, color, datetime.utcnow().isoformat())
                )
                db.commit()
                flash("Note saved successfully.", "success")
            else:
                flash("Please write something before saving.", "info")
        return redirect(url_for("notes"))
    search = request.args.get("q", "").lower()
    rows = db.execute("SELECT * FROM notes WHERE user_id=? ORDER BY date DESC", (session["user_id"],)).fetchall()
    all_notes = [dict(r) for r in rows]
    if search:
        all_notes = [n for n in all_notes if search in n["title"].lower() or search in n["content"].lower()]
    return render_template("notes.html", user=current_user(), notes=all_notes, search=search)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    ensure_certificates_for_user(session["user_id"])
    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        if new_name:
            db.execute("UPDATE users SET name=? WHERE id=?", (new_name, session["user_id"]))
            db.commit()
            session["name"] = new_name
            flash("Profile updated successfully.", "success")
        else:
            flash("Name cannot be empty.", "danger")
        return redirect(url_for("profile"))
    notes_count = db.execute("SELECT COUNT(*) FROM notes WHERE user_id=?", (session["user_id"],)).fetchone()[0]
    stats = get_user_stats(session["user_id"])
    quiz_count = db.execute("SELECT COUNT(*) FROM quiz_results WHERE user_id=?", (session["user_id"],)).fetchone()[0]
    certificates = db.execute(
        """
        SELECT ec.course_id, ec.percentage AS quiz_score, ec.certificate_id,
               ec.created_at AS completed_at, c.title AS course_title
        FROM exam_completions ec
        JOIN courses c ON c.id = ec.course_id
        WHERE ec.user_id=?
        UNION ALL
        SELECT cp.course_id, cp.quiz_score AS quiz_score, cp.certificate_id,
               cp.completed_at AS completed_at, c.title AS course_title
        FROM completions cp
        JOIN courses c ON c.id = cp.course_id
        WHERE cp.user_id=?
          AND NOT EXISTS (
            SELECT 1 FROM exam_completions ec
            WHERE ec.user_id=cp.user_id AND ec.course_id=cp.course_id
          )
        ORDER BY completed_at DESC
        LIMIT 3
        """,
        (session["user_id"], session["user_id"]),
    ).fetchall()
    return render_template(
        "profile.html", user=current_user(), notes_count=notes_count, stats=stats,
        quiz_count=quiz_count, certificates=certificates,
    )

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        flash("Settings saved successfully.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", user=current_user())

@app.route("/certificates")
@login_required
def certificates():
    db = get_db()
    ensure_certificates_for_user(session["user_id"])
    rows = db.execute(
        """
        SELECT ec.course_id, ec.percentage AS quiz_score, ec.certificate_id,
               ec.created_at AS completed_at, c.title AS course_title, c.emoji AS course_emoji
        FROM exam_completions ec
        JOIN courses c ON c.id = ec.course_id
        WHERE ec.user_id=?
        UNION ALL
        SELECT cp.course_id, cp.quiz_score AS quiz_score, cp.certificate_id,
               cp.completed_at AS completed_at, c.title AS course_title, c.emoji AS course_emoji
        FROM completions cp
        JOIN courses c ON c.id = cp.course_id
        WHERE cp.user_id=?
          AND NOT EXISTS (
            SELECT 1 FROM exam_completions ec
            WHERE ec.user_id=cp.user_id AND ec.course_id=cp.course_id
          )
        ORDER BY completed_at DESC
        """,
        (session["user_id"], session["user_id"]),
    ).fetchall()
    return render_template("certificates.html", user=current_user(), certificates=rows)

@app.route("/certificate/<course_id>")
@login_required
def certificate(course_id):
    db = get_db()
    ensure_certificates_for_user(session["user_id"])
    completion = db.execute(
        """
        SELECT ec.percentage AS score, ec.certificate_id AS certificate_id,
               ec.created_at AS completed_at, c.title AS course_title
        FROM exam_completions ec
        JOIN courses c ON c.id = ec.course_id
        WHERE ec.user_id=? AND ec.course_id=?
        """,
        (session["user_id"], course_id),
    ).fetchone()
    if not completion:
        completion = db.execute(
        """
        SELECT cp.quiz_score AS score, cp.certificate_id AS certificate_id,
               cp.completed_at AS completed_at, c.title AS course_title
        FROM completions cp
        JOIN courses c ON c.id = cp.course_id
        WHERE cp.user_id=? AND cp.course_id=?
        """,
        (session["user_id"], course_id),
        ).fetchone()
    if not completion:
        flash("Complete all lessons and pass the final exam to unlock this certificate.", "info")
        return redirect(url_for("courses"))

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    pdf.setFillColor(colors.HexColor("#0a0c12"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setStrokeColor(colors.HexColor("#00d4ff"))
    pdf.setLineWidth(3)
    pdf.roundRect(1.1 * cm, 1.1 * cm, width - 2.2 * cm, height - 2.2 * cm, 18, fill=0, stroke=1)
    pdf.setStrokeColor(colors.HexColor("#7c6bff"))
    pdf.setLineWidth(1)
    pdf.roundRect(1.55 * cm, 1.55 * cm, width - 3.1 * cm, height - 3.1 * cm, 14, fill=0, stroke=1)
    pdf.setFillColor(colors.Color(0, 0.83, 1, alpha=0.08))
    pdf.setFont("Helvetica-Bold", 74)
    pdf.drawCentredString(width / 2, height / 2 - 24, "E-Learn Pro")
    pdf.setFillColor(colors.HexColor("#00d4ff"))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 3.2 * cm, "E-Learn Pro")
    pdf.setFillColor(colors.HexColor("#f8fcff"))
    pdf.setFont("Helvetica-Bold", 36)
    pdf.drawCentredString(width / 2, height - 5.1 * cm, "Certificate of Completion")
    pdf.setFillColor(colors.HexColor("#b7c6d8"))
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(width / 2, height - 6.55 * cm, "This certifies that")
    pdf.setFillColor(colors.HexColor("#ffffff"))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 8.2 * cm, session.get("name", "Student"))
    pdf.setFillColor(colors.HexColor("#b7c6d8"))
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(width / 2, height - 9.55 * cm, "has successfully completed")
    pdf.setFillColor(colors.HexColor("#00d4ff"))
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 11.05 * cm, completion["course_title"])
    pdf.setFillColor(colors.HexColor("#f8fcff"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 12.55 * cm, f"Score: {completion['score']:.0f}%")
    pdf.drawCentredString(width / 2, height - 13.45 * cm, f"Completed on {format_date(completion['completed_at'], completion['completed_at'])}")
    pdf.setFillColor(colors.HexColor("#b7c6d8"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(width / 2, 3.35 * cm, "Farhat Abbas University - Setif 1")
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, 2.25 * cm, f"Certificate ID: {completion['certificate_id']}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    filename = f"certificate-{course_id}.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)

@app.route("/leaderboard")
@login_required
def leaderboard():
    db = get_db()
    students = db.execute("SELECT id, name FROM users WHERE role='student' ORDER BY name").fetchall()
    ranked = []
    for s in students:
        lessons_completed = db.execute(
            "SELECT COUNT(DISTINCT lesson_id) FROM progress WHERE user_id=?",
            (s["id"],),
        ).fetchone()[0]
        courses_completed = db.execute(
            "SELECT COUNT(*) FROM completions WHERE user_id=?",
            (s["id"],),
        ).fetchone()[0]
        best_quiz_score = db.execute(
            "SELECT COALESCE(MAX(percentage), 0) FROM quiz_results WHERE user_id=?",
            (s["id"],),
        ).fetchone()[0] or 0
        avg_quiz_score = db.execute(
            "SELECT COALESCE(AVG(percentage), 0) FROM quiz_results WHERE user_id=?",
            (s["id"],),
        ).fetchone()[0] or 0
        total_score = (lessons_completed * 10) + (courses_completed * 50) + (avg_quiz_score * 2)
        ranked.append({
            "id": s["id"], "name": anonymize_name(s["name"]), "lessons_completed": lessons_completed,
            "courses_completed": courses_completed, "best_quiz_score": best_quiz_score,
            "avg_quiz_score": avg_quiz_score, "total_score": round(total_score, 1),
            "is_current": s["id"] == session["user_id"],
        })
    ranked.sort(key=lambda item: item["total_score"], reverse=True)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = idx
    return render_template("leaderboard.html", user=current_user(), ranked=ranked, top_three=ranked[:3])

# ─────────────────────────────────────────────
#  ROUTES — ADMIN
# ─────────────────────────────────────────────
@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    db_courses = db.execute("SELECT * FROM courses ORDER BY created_at DESC").fetchall()
    extra_courses = []
    for c in db_courses:
        count = db.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (c["id"],)).fetchone()[0]
        extra_courses.append({"id": c["id"], "title": c["title"], "level": c["level"],
                               "category": c["category"], "emoji": c["emoji"], "lessons_count": count})
    all_users = db.execute("SELECT id, name, email, role FROM users ORDER BY id").fetchall()
    return render_template("admin.html", user=current_user(), courses=extra_courses, all_users=all_users,
                           total_courses=len(extra_courses), total_users=len(all_users))

@app.route("/admin/course/new", methods=["GET", "POST"])
@admin_required
def admin_new_course():
    if request.method == "POST":
        db = get_db()
        course_id  = "c_" + str(uuid.uuid4())[:8]
        title      = request.form.get("title", "").strip()
        desc       = request.form.get("description", "").strip()
        emoji      = request.form.get("emoji", "book").strip() or "book"
        color      = request.form.get("color", "#1a2a4a").strip()
        level      = request.form.get("level", "beginner")
        hours      = int(request.form.get("hours", 0) or 0)
        category   = request.form.get("category", "general")
        if not title:
            flash("Course title is required.", "danger")
            return redirect(url_for("admin_new_course"))
        db.execute(
            "INSERT INTO courses (id, title, description, emoji, color, level, hours, category, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (course_id, title, desc, emoji, color, level, hours, category, session["user_id"], datetime.utcnow().isoformat())
        )
        lesson_titles   = request.form.getlist("lesson_title[]")
        lesson_contents = request.form.getlist("lesson_content[]")
        for i, (lt, lc) in enumerate(zip(lesson_titles, lesson_contents)):
            lt = lt.strip()
            if not lt:
                continue
            lid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO lessons (id, course_id, title, content, lesson_order) VALUES (?,?,?,?,?)",
                (lid, course_id, lt, lc.strip(), i)
            )
        db.commit()
        
        pdf_file = request.files.get("course_pdf")
        if pdf_file and pdf_file.filename:
            os.makedirs(os.path.join(app.root_path, "static", "pdfs"), exist_ok=True)
            pdf_file.save(os.path.join(app.root_path, "static", "pdfs", f"{course_id}.pdf"))
            
        flash(f'Course "{title}" created successfully.', "success")
        return redirect(url_for("admin"))
    return render_template("admin_course_form.html", user=current_user(), editing=False)

@app.route("/admin/ai-generate", methods=["GET", "POST"])
@admin_required
def admin_ai_generate():
    if request.method == "POST":
        topic = request.form.get("topic", "").strip()
        level = request.form.get("level", "beginner")
        category = request.form.get("category", "general")
        num_lessons = int(request.form.get("num_lessons", 3) or 3)
        hours = int(request.form.get("hours", 4) or 4)
        emoji = request.form.get("emoji", "book-open").strip() or "book-open"
        color = request.form.get("color", "#00d4ff").strip() or "#00d4ff"
        if not topic:
            flash("Topic is required to generate a course.", "danger")
            return redirect(url_for("admin_ai_generate"))
        num_lessons = max(1, min(num_lessons, 5))
        prompt = f"""Generate a complete online course about "{topic}" for
{level} level students.
Return ONLY valid JSON, no markdown, no backticks:
{{
  "title": "Course title here",
  "description": "2-sentence course description",
  "lessons": [
    {{
      "title": "Lesson title",
      "content": "Detailed lesson content with bullet
                  points, explanations and key concepts.
                  At least 200 words."
    }}
  ]
}}
Generate exactly {num_lessons} lessons.
Make content educational, structured and practical."""
        text = call_gemini(prompt, temperature=0.6, max_tokens=3000)
        generated = extract_json_object(text)
        if not generated or not generated.get("lessons"):
            generated = {
                "title": f"{topic} Essentials",
                "description": f"A practical introduction to {topic}. Learn the core concepts, workflows, and real examples needed to keep studying independently.",
                "lessons": [
                    {
                        "title": f"{topic} Lesson {i + 1}",
                        "content": f"{topic} is an important skill area. This lesson introduces key vocabulary, practical examples, common mistakes, and short exercises. Review the ideas, write notes, and apply them to a small project so the knowledge becomes useful."
                    }
                    for i in range(num_lessons)
                ],
            }
            flash("Gemini was unavailable, so a structured fallback course was created.", "info")
        lessons = generated.get("lessons", [])[:num_lessons]
        db = get_db()
        course_id = "ai_" + str(uuid.uuid4())[:8]
        db.execute(
            "INSERT INTO courses (id, title, description, emoji, color, level, hours, category, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                course_id, generated.get("title", f"{topic} Essentials"),
                generated.get("description", f"A complete course about {topic}."),
                emoji, color, level, hours, category, session["user_id"], datetime.utcnow().isoformat(),
            ),
        )
        for idx, lesson_data in enumerate(lessons):
            db.execute(
                "INSERT INTO lessons (id, course_id, title, content, lesson_order) VALUES (?,?,?,?,?)",
                (
                    str(uuid.uuid4()), course_id,
                    lesson_data.get("title", f"Lesson {idx + 1}"),
                    lesson_data.get("content", "Lesson content will be expanded by the instructor."),
                    idx,
                ),
            )
        db.commit()
        flash(f'AI course "{generated.get("title", topic)}" created successfully.', "success")
        return redirect(url_for("admin"))
    return render_template("admin_ai_generate.html", user=current_user())

@app.route("/admin/course/<course_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_course(course_id):
    db = get_db()
    course = db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("admin"))
    lessons = db.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_order", (course_id,)).fetchall()
    if request.method == "POST":
        title      = request.form.get("title", "").strip()
        desc       = request.form.get("description", "").strip()
        emoji      = request.form.get("emoji", "book").strip() or "book"
        color      = request.form.get("color", "#1a2a4a").strip()
        level      = request.form.get("level", "beginner")
        hours      = int(request.form.get("hours", 0) or 0)
        category   = request.form.get("category", "general")
        db.execute("UPDATE courses SET title=?, description=?, emoji=?, color=?, level=?, hours=?, category=? WHERE id=?",
                   (title, desc, emoji, color, level, hours, category, course_id))
        db.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
        lesson_titles   = request.form.getlist("lesson_title[]")
        lesson_contents = request.form.getlist("lesson_content[]")
        for i, (lt, lc) in enumerate(zip(lesson_titles, lesson_contents)):
            lt = lt.strip()
            if not lt:
                continue
            lid = str(uuid.uuid4())
            db.execute("INSERT INTO lessons (id, course_id, title, content, lesson_order) VALUES (?,?,?,?,?)",
                       (lid, course_id, lt, lc.strip(), i))
        db.commit()
        
        pdf_file = request.files.get("course_pdf")
        if pdf_file and pdf_file.filename:
            os.makedirs(os.path.join(app.root_path, "static", "pdfs"), exist_ok=True)
            pdf_file.save(os.path.join(app.root_path, "static", "pdfs", f"{course_id}.pdf"))
            
        flash("Course updated successfully.", "success")
        return redirect(url_for("admin"))
    return render_template("admin_course_form.html", user=current_user(), editing=True, course=dict(course), lessons=[dict(l) for l in lessons])

@app.route("/admin/course/<course_id>/delete", methods=["POST"])
@admin_required
def admin_delete_course(course_id):
    db = get_db()
    db.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
    db.execute("DELETE FROM courses WHERE id=?", (course_id,))
    db.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin"))

@app.route("/admin/user/create", methods=["POST"])
@admin_required
def admin_create_user():
    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role     = request.form.get("role", "student")
    if role not in ("student", "admin"):
        role = "student"
    if not name or not email or not password:
        flash("All fields are required to create a user.", "danger")
        return redirect(url_for("admin"))
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        flash("A user with that email already exists.", "danger")
        return redirect(url_for("admin"))
    db.execute("INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
               (email, password, name, role))
    db.commit()
    flash(f'User "{name}" created successfully as {role}.', "success")
    return redirect(url_for("admin"))

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    if user_id == session.get("user_id"):
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin"))
    db = get_db()
    user = db.execute("SELECT name FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin"))
    db.execute("DELETE FROM notes WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    flash(f'User "{user["name"]}" deleted.', "info")
    return redirect(url_for("admin"))

# ─────────────────────────────────────────────
#  API — GEMINI PROXY ENDPOINTS
# ─────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data          = request.get_json()
    print("DEBUG: /api/chat received data:", data)
    question      = (data or {}).get("question", "").strip()
    print("DEBUG: /api/chat question:", question)
    lesson_content = (data or {}).get("lesson_content", "")
    api_key       = (data or {}).get("api_key", "").strip()
    print("DEBUG: /api/chat api_key present:", bool(api_key))
    if not question:
        print("DEBUG: /api/chat error: No question provided")
        return jsonify({"error": "No question provided"}), 400
    is_summary = "summarize" in question.lower() or "summary" in question.lower()
    if is_summary:
        prompt = f"""You are an educational assistant. The student wants a summary of the current lesson.

Lesson content:
{lesson_content}

Generate a clear, structured summary with:
- Main topic in one sentence
- 3-5 key bullet points
- One "remember this" takeaway

Keep it concise and educational."""
    else:
        prompt = f"""You are a helpful educational assistant for an e-learning platform.

You should answer the student's question clearly and concisely. If the question relates to the provided lesson content, use that information to help frame your answer. However, you are free to answer ANY question the student asks, even if it is outside the scope of the lesson.

Lesson content (for context if relevant):
{lesson_content}

Student question: {question}

Answer the student's question directly and helpfully."""
    print("DEBUG: /api/chat calling call_gemini")
    answer = call_gemini(prompt, api_key=api_key)
    print("DEBUG: /api/chat answer:", answer)
    if answer is None:
        print("DEBUG: /api/chat answer is None, returning 500 error")
        return jsonify({"error": "Failed to get response from AI. Check your API key."}), 500
    print("DEBUG: /api/chat returning success response")
    return jsonify({"answer": answer})

@app.route("/api/quiz/generate", methods=["POST"])
@login_required
def api_quiz_generate():
    data      = request.get_json()
    course_id = (data or {}).get("course_id", "")
    pdf_text  = (data or {}).get("pdf_text", "")
    api_key   = (data or {}).get("api_key", "").strip()
    
    db = get_db()
    c = db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if c:
        topic = c["title"]
        lessons_rows = db.execute("SELECT content FROM lessons WHERE course_id=? ORDER BY lesson_order", (course_id,)).fetchall()
        lesson_text = " ".join(l["content"] for l in lessons_rows)
    else:
        topic = course_id
        lesson_text = ""
            
    if pdf_text:
        lesson_text = pdf_text
        
    prompt = f"""Generate exactly 5 multiple choice quiz questions about: "{topic}"

Context: {lesson_text[:2000]}

Return ONLY a valid JSON array, no other text, no markdown, no backticks.
Format:
[
  {{
    "question": "A specific contextual question based on the text?",
    "options": ["Realistic incorrect answer 1", "Realistic incorrect answer 2", "Actual correct answer", "Realistic incorrect answer 3"],
    "correct": 2
  }}
]
"correct" is the index (0-3) of the correct answer.
Make questions clear, educational, and appropriate for the level."""
    text = call_gemini(prompt, api_key=api_key, temperature=0.7, max_tokens=1000)
    
    import random
    def get_fallback_questions():
        import re
        lt = lesson_text if lesson_text else f"{topic} is very important to learn."
        sentences = [s.strip() for s in re.split(r'[.!?]\s+', lt) if len(s.strip()) > 30]
        if len(sentences) < 5:
            sentences.extend([f"This is a key fact about {topic}.", f"Understanding {topic} is crucial.", f"Many professionals use {topic}.", f"You can master {topic} with practice.", f"The fundamentals of {topic} are essential."])
            
        fq = []
        fakes = ["Integration", "Deployment", "Algorithm", "Variables", "Design", "Optimization", "Function", "Process", "System", "Component", "Module", "Interface"]
        for i in range(5):
            s = sentences[i % len(sentences)]
            words = [w for w in s.split() if w.strip(',;:\'\"').isalpha() and len(w) > 4]
            if words:
                target = random.choice(words).strip(',;:\'\"')
                q_text = s.replace(target, "_____", 1) + f" (Topic: {topic})"
                opts = [target]
                while len(opts) < 4:
                    opt = random.choice(fakes)
                    if opt not in opts: opts.append(opt)
                random.shuffle(opts)
                fq.append({"question": q_text, "options": opts, "correct": opts.index(target)})
            else:
                fq.append({"question": f"What is essential for {topic}?", "options": ["Practice", "Sleep", "Food", "None"], "correct": 0})
        return fq

    if text is None:
        return jsonify({"questions": get_fallback_questions()})
    try:
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            clean = match.group(0)
            questions = json.loads(clean)
            return jsonify({"questions": questions})
        else:
            clean = text.replace("```json", "").replace("```", "").strip()
            questions = json.loads(clean)
            return jsonify({"questions": questions})
    except Exception:
        return jsonify({"questions": get_fallback_questions()})

@app.route("/api/quiz/save", methods=["POST"])
@login_required
def api_quiz_save():
    data = request.get_json() or {}
    course_id = str(data.get("course_id", "")).strip()
    try:
        score = int(data.get("score", 0))
        total = int(data.get("total", 0))
        percentage = float(data.get("percentage", 0))
    except (TypeError, ValueError):
        return jsonify({"saved": False, "error": "Invalid quiz result."}), 400
    if not course_id or total <= 0:
        return jsonify({"saved": False, "error": "Missing course or total."}), 400
    percentage = max(0, min(100, percentage))
    db = get_db()
    db.execute(
        "INSERT INTO quiz_results (user_id, course_id, score, total, percentage, taken_at) VALUES (?,?,?,?,?,?)",
        (session["user_id"], course_id, score, total, percentage, datetime.utcnow().isoformat()),
    )
    certificate_earned = False
    course_progress = get_course_progress(session["user_id"], course_id)
    if percentage >= 70:
        mark_course_lessons_completed(session["user_id"], course_id)
        course_progress = get_course_progress(session["user_id"], course_id)
    if percentage >= 70 and course_progress == 100:
        existing = db.execute(
            "SELECT id FROM completions WHERE user_id=? AND course_id=?",
            (session["user_id"], course_id),
        ).fetchone()
        if existing:
            certificate_earned = True
        else:
            db.execute(
                "INSERT OR IGNORE INTO completions (user_id, course_id, quiz_score, certificate_id, completed_at) VALUES (?,?,?,?,?)",
                (session["user_id"], course_id, percentage, str(uuid.uuid4()), datetime.utcnow().isoformat()),
            )
            certificate_earned = True
    db.commit()
    return jsonify({
        "saved": True,
        "certificate_earned": certificate_earned,
        "course_progress": course_progress,
        "passed": percentage >= 70,
    })

@app.route("/api/exam/generate", methods=["POST"])
@login_required
def api_exam_generate():
    data = request.get_json() or {}
    course_id = str(data.get("course_id", "")).strip()
    course = get_course_with_lessons(course_id)
    if not course:
        return jsonify({"error": "Course not found."}), 404
    lesson_text = "\n\n".join(
        f"{lesson['title']}\n{lesson['content'] or ''}"
        for lesson in course["lessons"]
    )
    prompt = f"""Generate exactly 20 multiple choice final exam questions for the course "{course['title']}".

Use all of this course material:
{lesson_text[:8000]}

Return ONLY a valid JSON array, no markdown, no backticks.
Each item must use this exact format:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 0
  }}
]
"correct" must be the zero-based index of the correct option.
Make the questions practical, fair, and based on the lessons."""
    text = call_gemini(prompt, temperature=0.5, max_tokens=3500)
    raw_questions = None
    if text:
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            start = clean.find("[")
            end = clean.rfind("]")
            raw_questions = json.loads(clean[start:end + 1] if start != -1 and end != -1 else clean)
        except Exception:
            raw_questions = None
    questions = normalize_exam_questions(raw_questions, course["title"], lesson_text)
    EXAM_CACHE[(session["user_id"], course_id)] = {
        "questions": questions,
        "created_at": datetime.utcnow().isoformat(),
    }
    return jsonify({"questions": public_exam_questions(questions), "total": 20})

@app.route("/api/exam/submit", methods=["POST"])
@login_required
def api_exam_submit():
    data = request.get_json() or {}
    course_id = str(data.get("course_id", "")).strip()
    if not course_id:
        return jsonify({"saved": False, "error": "Course is required."}), 400
    cached = EXAM_CACHE.get((session["user_id"], course_id))
    answers = data.get("answers")
    if cached and isinstance(answers, list):
        questions = cached["questions"]
        total = len(questions)
        score = 0
        for idx, question in enumerate(questions):
            try:
                selected = int(answers[idx])
            except (IndexError, TypeError, ValueError):
                selected = -1
            if selected == question["correct"]:
                score += 1
        percentage = round((score / total) * 100, 2) if total else 0
    else:
        try:
            score = int(data.get("score", 0))
            total = int(data.get("total", 0))
            percentage = float(data.get("percentage", 0))
        except (TypeError, ValueError):
            return jsonify({"saved": False, "error": "Invalid exam result."}), 400
        if total <= 0:
            return jsonify({"saved": False, "error": "Invalid exam total."}), 400
        percentage = max(0, min(100, percentage))
    db = get_db()
    db.execute(
        "INSERT INTO exam_results (user_id, course_id, score, total, percentage, created_at) VALUES (?,?,?,?,?,?)",
        (session["user_id"], course_id, score, total, percentage, datetime.utcnow().isoformat()),
    )
    certificate_earned = False
    if percentage >= 70 and all_lessons_visited(session["user_id"], course_id):
        existing = db.execute(
            "SELECT id FROM exam_completions WHERE user_id=? AND course_id=?",
            (session["user_id"], course_id),
        ).fetchone()
        if existing:
            certificate_earned = True
        else:
            db.execute(
                "INSERT OR IGNORE INTO exam_completions (user_id, course_id, percentage, certificate_id, created_at) VALUES (?,?,?,?,?)",
                (session["user_id"], course_id, percentage, str(uuid.uuid4()), datetime.utcnow().isoformat()),
            )
            certificate_earned = True
    db.commit()
    return jsonify({
        "saved": True,
        "score": score,
        "total": total,
        "percentage": percentage,
        "passed": percentage >= 70,
        "certificate_earned": certificate_earned,
        "lessons_completed": all_lessons_visited(session["user_id"], course_id),
    })

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
