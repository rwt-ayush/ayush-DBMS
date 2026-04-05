from django.shortcuts import render, redirect
from django.http import Http404
from django.db import connection
from .models import Student, Job, Application, Company, PlacementSection
from .forms import StudentForm, CompanyForm, JobForm, ApplicationForm, StudentLoginForm, CompanyLoginForm

T_STUDENT     = Student._meta.db_table
T_COMPANY     = Company._meta.db_table
T_JOB         = Job._meta.db_table
T_APPLICATION = Application._meta.db_table
T_SECTION     = PlacementSection._meta.db_table

_query_log = []

def _log_reset():
    global _query_log
    _query_log = []

def _fmt_query(sql, params=None):
    clean = ' '.join(sql.split())
    if params:
        display = clean
        for p in (params or []):
            display = display.replace('%s', repr(p), 1)
        return display
    return clean

def _log(sql, params=None):
    _query_log.append(_fmt_query(sql, params))

def _ctx(extra):
    extra['sql_queries'] = list(_query_log)
    return extra

def get_count(query, params=None):
    _log(query, params)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchone()[0]

def raw_fetchall(query, params=None):
    _log(query, params)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def raw_fetchone(query, params=None):
    _log(query, params)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

def raw_execute(query, params=None):
    _log(query, params)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])

class DictObj:
    def __init__(self, d):
        self.__dict__.update(d)
    def __getattr__(self, name):
        return None

class QueryList(list):
    def count(self):
        return len(self)

def _rows_to_querylist(rows):
    return QueryList(DictObj(r) for r in rows)

def home(request):
    _log_reset()
    companies = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_COMPANY}"))
    company_job_summary, company_data = [], []
    for company in companies:
        jobs = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_JOB} WHERE company_id = %s", [company.company_id]))
        apps = _rows_to_querylist(raw_fetchall(f"SELECT a.* FROM {T_APPLICATION} a INNER JOIN {T_JOB} j ON a.job_id = j.job_id WHERE j.company_id = %s", [company.company_id]))
        company_job_summary.append({'company': company, 'jobs': jobs, 'job_count': len(jobs)})
        company_data.append({'company': company, 'jobs': jobs, 'applications': apps})
    selected_company_id = request.GET.get('company_id')
    selected_company_id = int(selected_company_id) if selected_company_id and selected_company_id.isdigit() else None
    if selected_company_id is None and company_data:
        selected_company_id = company_data[0]['company'].company_id
    student_count     = get_count(f"SELECT COUNT(*) FROM {T_STUDENT}")
    job_count         = get_count(f"SELECT COUNT(*) FROM {T_JOB}")
    application_count = get_count(f"SELECT COUNT(*) FROM {T_APPLICATION}")
    return render(request, 'placement/home.html', _ctx({'student_count': student_count, 'job_count': job_count, 'application_count': application_count, 'company_job_summary': company_job_summary, 'company_data': company_data, 'selected_company_id': selected_company_id}))

def companies(request, company_id=None):
    _log_reset()
    companies = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_COMPANY}"))
    selected_company_id = company_id or request.GET.get('company_id')
    selected_company_id = int(selected_company_id) if selected_company_id and str(selected_company_id).isdigit() else None
    if selected_company_id is None and companies:
        selected_company_id = companies[0].company_id
    selected = next((c for c in companies if c.company_id == selected_company_id), None)
    applications = _rows_to_querylist(raw_fetchall(f"SELECT a.* FROM {T_APPLICATION} a INNER JOIN {T_JOB} j ON a.job_id = j.job_id WHERE j.company_id = %s", [selected.company_id])) if selected else QueryList()
    return render(request, 'placement/companies.html', _ctx({'companies': companies, 'selected_company': selected, 'applications': applications, 'selected_company_id': selected_company_id}))

def student_register(request):
    _log_reset()
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            raw_execute(f"INSERT INTO {T_STUDENT} (name, roll_no, email, phone, password, profile_pic, github, linkedin, resume, skills) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [d['name'], d['roll_no'], d['email'], d['phone'], d['password'], d['profile_pic'], d['github'], d['linkedin'], d['resume'], d['skills']])
            return redirect('placement:student_login')
    else:
        form = StudentForm()
    return render(request, 'placement/student_register.html', _ctx({'form': form}))

def student_login(request):
    _log_reset()
    msg = None
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            row = raw_fetchone(f"SELECT * FROM {T_STUDENT} WHERE email = %s AND password = %s LIMIT 1", [form.cleaned_data['email'], form.cleaned_data['password']])
            if row:
                request.session['student_id'] = row['student_id']
                return redirect('placement:student_dashboard')
            msg = 'Invalid credentials'
    else:
        form = StudentLoginForm()
    return render(request, 'placement/student_login.html', _ctx({'form': form, 'msg': msg}))

def company_register(request):
    _log_reset()
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            raw_execute(f"INSERT INTO {T_COMPANY} (name, description, website_link, location, password) VALUES (%s, %s, %s, %s, %s)", [d['name'], d['description'], d['website_link'], d['location'], d['password']])
            return redirect('placement:company_login')
    else:
        form = CompanyForm()
    return render(request, 'placement/company_register.html', _ctx({'form': form}))

def company_login(request):
    _log_reset()
    msg = None
    if request.method == 'POST':
        form = CompanyLoginForm(request.POST)
        if form.is_valid():
            row = raw_fetchone(f"SELECT * FROM {T_COMPANY} WHERE name = %s AND password = %s LIMIT 1", [form.cleaned_data['name'], form.cleaned_data['password']])
            if row:
                request.session['company_id'] = row['company_id']
                return redirect('placement:company_dashboard')
            msg = 'Invalid credentials'
    else:
        form = CompanyLoginForm()
    return render(request, 'placement/company_login.html', _ctx({'form': form, 'msg': msg}))

def student_dashboard(request):
    _log_reset()
    sid = request.session.get('student_id')
    if not sid:
        return redirect('placement:student_login')
    student_row = raw_fetchone(f"SELECT * FROM {T_STUDENT} WHERE student_id = %s", [sid])
    if not student_row:
        raise Http404("Student not found")
    student = DictObj(student_row)
    jobs         = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_JOB}"))
    applications = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_APPLICATION} WHERE student_id = %s", [student.student_id]))
    return render(request, 'placement/student_dashboard.html', _ctx({'student': student, 'jobs': jobs, 'applications': applications, 'total_applied': len(applications), 'accepted_count': sum(1 for a in applications if a.status == 'accepted'), 'pending_count': sum(1 for a in applications if a.status == 'pending'), 'rejected_count': sum(1 for a in applications if a.status == 'rejected')}))

def company_dashboard(request):
    _log_reset()
    cid = request.session.get('company_id')
    if not cid:
        return redirect('placement:company_login')
    company_row = raw_fetchone(f"SELECT * FROM {T_COMPANY} WHERE company_id = %s", [cid])
    if not company_row:
        raise Http404("Company not found")
    company = DictObj(company_row)
    jobs = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_JOB} WHERE company_id = %s", [company.company_id]))
    applications = _rows_to_querylist(raw_fetchall(f"SELECT a.* FROM {T_APPLICATION} a INNER JOIN {T_JOB} j ON a.job_id = j.job_id WHERE j.company_id = %s", [company.company_id]))
    apps_by_status = {'pending': sum(1 for a in applications if a.status == 'pending'), 'accepted': sum(1 for a in applications if a.status == 'accepted'), 'rejected': sum(1 for a in applications if a.status == 'rejected')}
    job_stats = []
    for job in jobs:
        job_apps = [a for a in applications if a.job_id == job.job_id]
        selected = sum(1 for a in job_apps if a.status == 'accepted')
        max_app  = job.max_applicants or 1
        job_stats.append({'job': job, 'applied': len(job_apps), 'selected': selected, 'ratio': f"{selected}/{job.max_applicants}", 'fill_percent': int(min(100, (selected / max_app) * 100))})
    return render(request, 'placement/company_dashboard.html', _ctx({'company': company, 'jobs': jobs, 'applications': applications, 'apps_by_status': apps_by_status, 'job_stats': job_stats}))

def logout_view(request):
    request.session.flush()
    return redirect('placement:home')

def student_list(request):
    _log_reset()
    students = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_STUDENT} ORDER BY student_id DESC"))
    return render(request, 'placement/student_list.html', _ctx({'students': students}))

def student_create(request):
    _log_reset()
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            raw_execute(f"INSERT INTO {T_STUDENT} (name, roll_no, email, phone, password, profile_pic, github, linkedin, resume, skills) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [d['name'], d['roll_no'], d['email'], d['phone'], d['password'], d['profile_pic'], d['github'], d['linkedin'], d['resume'], d['skills']])
            return redirect('placement:student_list')
    else:
        form = StudentForm()
    return render(request, 'placement/student_form.html', _ctx({'form': form}))

def job_list(request):
    _log_reset()
    jobs = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_JOB} ORDER BY job_id DESC"))
    return render(request, 'placement/job_list.html', _ctx({'jobs': jobs}))

def job_create(request):
    _log_reset()
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            raw_execute(f"INSERT INTO {T_JOB} (company_id, section_id, position, description, max_applicants, pay_rate, post_date) VALUES (%s, %s, %s, %s, %s, %s, DATE('now'))", [d['company'].company_id, d['section'].section_id if d.get('section') else None, d['position'], d['description'], d['max_applicants'], d['pay_rate']])
            return redirect('placement:job_list')
    else:
        form = JobForm()
    return render(request, 'placement/job_form.html', _ctx({'form': form}))

def application_list(request):
    _log_reset()
    applications = _rows_to_querylist(raw_fetchall(f"SELECT * FROM {T_APPLICATION} ORDER BY applied_at DESC"))
    return render(request, 'placement/application_list.html', _ctx({'applications': applications}))

def application_create(request, job_id=None):
    _log_reset()
    sid = request.session.get('student_id')
    if not sid:
        return redirect('placement:student_login')
    student_row = raw_fetchone(f"SELECT * FROM {T_STUDENT} WHERE student_id = %s", [sid])
    if not student_row:
        raise Http404("Student not found")
    student = DictObj(student_row)
    if job_id:
        job_row = raw_fetchone(f"SELECT * FROM {T_JOB} WHERE job_id = %s", [job_id])
        if not job_row:
            raise Http404("Job not found")
        job = DictObj(job_row)
        existing = raw_fetchone(f"SELECT * FROM {T_APPLICATION} WHERE student_id = %s AND job_id = %s LIMIT 1", [student.student_id, job.job_id])
        if existing:
            return render(request, 'placement/application_form.html', _ctx({'error': 'You already applied for this job.', 'job': job, 'student': student}))
        job_app_count = get_count(f"SELECT COUNT(*) FROM {T_APPLICATION} WHERE job_id = %s", [job.job_id])
        if job_app_count >= job.max_applicants:
            return render(request, 'placement/application_form.html', _ctx({'error': 'This job has reached the maximum applicants.', 'job': job, 'student': student}))
        if request.method == 'POST':
            raw_execute(f"INSERT INTO {T_APPLICATION} (student_id, job_id, status, applied_at) VALUES (%s, %s, 'pending', CURRENT_TIMESTAMP)", [student.student_id, job.job_id])
            return redirect('placement:student_dashboard')
        return render(request, 'placement/application_form.html', _ctx({'job': job, 'student': student}))
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            s_id, j_id = d['student'].student_id, d['job'].job_id
            existing = raw_fetchone(f"SELECT * FROM {T_APPLICATION} WHERE student_id = %s AND job_id = %s LIMIT 1", [s_id, j_id])
            if existing:
                form.add_error(None, 'Duplicate application already exists.')
            else:
                raw_execute(f"INSERT INTO {T_APPLICATION} (student_id, job_id, status, applied_at) VALUES (%s, %s, 'pending', CURRENT_TIMESTAMP)", [s_id, j_id])
                return redirect('placement:application_list')
    else:
        form = ApplicationForm()
    return render(request, 'placement/application_form.html', _ctx({'form': form}))

def company_application_action(request, app_id, action):
    _log_reset()
    cid = request.session.get('company_id')
    if not cid:
        return redirect('placement:company_login')
    company_row = raw_fetchone(f"SELECT * FROM {T_COMPANY} WHERE company_id = %s", [cid])
    if not company_row:
        raise Http404("Company not found")
    app_row = raw_fetchone(f"SELECT a.* FROM {T_APPLICATION} a INNER JOIN {T_JOB} j ON a.job_id = j.job_id WHERE a.app_id = %s AND j.company_id = %s LIMIT 1", [app_id, company_row['company_id']])
    if not app_row:
        raise Http404("Application not found")
    if action in ('accept', 'reject'):
        raw_execute(f"UPDATE {T_APPLICATION} SET status = %s WHERE app_id = %s", ['accepted' if action == 'accept' else 'rejected', app_row['app_id']])
    return redirect('placement:company_dashboard')


# ---------------------------------------------------------------------------
# SQL Explorer
# ---------------------------------------------------------------------------

PRESET_QUERIES = [
    {"label": "All Students",         "sql": "SELECT * FROM placement_student;"},
    {"label": "All Companies",        "sql": "SELECT * FROM placement_company;"},
    {"label": "All Jobs",             "sql": "SELECT * FROM placement_job;"},
    {"label": "All Applications",     "sql": "SELECT * FROM placement_application;"},
    {"label": "Accepted Apps",        "sql": "SELECT * FROM placement_application WHERE status = 'accepted';"},
    {"label": "Pending Apps",         "sql": "SELECT * FROM placement_application WHERE status = 'pending';"},
    {"label": "Jobs + Company Name",  "sql": "SELECT j.job_id, j.position, j.pay_rate, c.name AS company FROM placement_job j INNER JOIN placement_company c ON j.company_id = c.company_id ORDER BY j.job_id DESC;"},
    {"label": "Student App Count",    "sql": "SELECT s.name, s.roll_no, COUNT(a.app_id) AS applications FROM placement_student s LEFT JOIN placement_application a ON s.student_id = a.student_id GROUP BY s.student_id ORDER BY applications DESC;"},
    {"label": "High Pay Jobs",        "sql": "SELECT position, pay_rate, post_date FROM placement_job WHERE pay_rate != '' ORDER BY post_date DESC;"},
    {"label": "Apps per Job",         "sql": "SELECT j.position, COUNT(a.app_id) AS total_applied, j.max_applicants FROM placement_job j LEFT JOIN placement_application a ON j.job_id = a.job_id GROUP BY j.job_id ORDER BY total_applied DESC;"},
    {"label": "Students w/ GitHub",   "sql": "SELECT name, roll_no, email, github FROM placement_student WHERE github != '' ORDER BY name;"},
    {"label": "Recent Applications",  "sql": "SELECT a.app_id, s.name AS student, j.position, c.name AS company, a.status, a.applied_at FROM placement_application a JOIN placement_student s ON a.student_id = s.student_id JOIN placement_job j ON a.job_id = j.job_id JOIN placement_company c ON j.company_id = c.company_id ORDER BY a.applied_at DESC LIMIT 20;"},
]

# SQL keywords that modify data — block these in the explorer
_BLOCKED = ('drop', 'truncate', 'alter', 'create', 'attach', 'detach', 'pragma')


def sql_explorer(request):
    _log_reset()
    query   = ''
    columns = None
    rows    = None
    error   = None
    affected = None

    import os
    from django.conf import settings
    db_name = os.path.basename(settings.DATABASES['default']['NAME'])

    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if query:
            lower_q = query.lower().lstrip()
            if any(lower_q.startswith(kw) for kw in _BLOCKED):
                error = f"Query type not allowed in explorer. Blocked keywords: {', '.join(_BLOCKED).upper()}"
            else:
                try:
                    _log(query)
                    with connection.cursor() as cursor:
                        cursor.execute(query)
                        if cursor.description:
                            columns = [col[0] for col in cursor.description]
                            rows    = cursor.fetchall()
                        else:
                            affected = cursor.rowcount
                            rows     = []
                except Exception as e:
                    error = str(e)
                    rows  = []

    return render(request, 'placement/sql_explorer.html', _ctx({
        'query':    query,
        'columns':  columns,
        'rows':     rows,
        'error':    error,
        'affected': affected,
        'presets':  PRESET_QUERIES,
        'db_name':  db_name,
    }))
