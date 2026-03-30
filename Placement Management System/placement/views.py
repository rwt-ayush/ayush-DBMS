from django.shortcuts import render, redirect
from django.http import Http404
from django.db import connection
from .models import Student, Job, Application, Company
from .forms import StudentForm, CompanyForm, JobForm, ApplicationForm, StudentLoginForm, CompanyLoginForm


def get_count(query, params=None):
    """Helper to execute raw SQL scalar queries."""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchone()[0]


class QueryList(list):
    """
    Helper class to make standard Python lists behave like Django QuerySets 
    in templates so that {{ my_list.count }} doesn't fail silently.
    """
    def count(self):
        return len(self)


def home(request):
    companies = QueryList(Company.objects.raw(f"SELECT * FROM {Company._meta.db_table}"))
    company_job_summary = []
    company_data = []
    
    for company in companies:
        jobs = QueryList(Job.objects.raw(f"SELECT * FROM {Job._meta.db_table} WHERE company_id = %s", [company.company_id]))
        
        apps_query = f"""
            SELECT a.* FROM {Application._meta.db_table} a
            INNER JOIN {Job._meta.db_table} j ON a.job_id = j.job_id
            WHERE j.company_id = %s
        """
        apps = QueryList(Application.objects.raw(apps_query, [company.company_id]))
        
        company_job_summary.append({
            'company': company,
            'jobs': jobs,
            'job_count': len(jobs),
        })
        company_data.append({
            'company': company,
            'jobs': jobs,
            'applications': apps,
        })

    selected_company_id = request.GET.get('company_id')
    selected_company_id = int(selected_company_id) if selected_company_id and selected_company_id.isdigit() else None
    if selected_company_id is None and company_data:
        selected_company_id = company_data[0]['company'].company_id

    student_count = get_count(f"SELECT COUNT(*) FROM {Student._meta.db_table}")
    job_count = get_count(f"SELECT COUNT(*) FROM {Job._meta.db_table}")
    application_count = get_count(f"SELECT COUNT(*) FROM {Application._meta.db_table}")

    return render(request, 'placement/home.html', {
        'student_count': student_count,
        'job_count': job_count,
        'application_count': application_count,
        'company_job_summary': company_job_summary,
        'company_data': company_data,
        'selected_company_id': selected_company_id,
    })


def companies(request, company_id=None):
    companies = QueryList(Company.objects.raw(f"SELECT * FROM {Company._meta.db_table}"))
    selected_company_id = company_id or request.GET.get('company_id')
    selected_company_id = int(selected_company_id) if selected_company_id and str(selected_company_id).isdigit() else None
    
    if selected_company_id is None and companies:
        selected_company_id = companies[0].company_id
        
    selected = next((c for c in companies if c.company_id == selected_company_id), None)
    
    if selected:
        apps_query = f"""
            SELECT a.* FROM {Application._meta.db_table} a
            INNER JOIN {Job._meta.db_table} j ON a.job_id = j.job_id
            WHERE j.company_id = %s
        """
        applications = QueryList(Application.objects.raw(apps_query, [selected.company_id]))
    else:
        applications = QueryList()
        
    return render(request, 'placement/companies.html', {
        'companies': companies,
        'selected_company': selected,
        'applications': applications,
        'selected_company_id': selected_company_id,
    })


def student_register(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save() # ORM Write
            return redirect('placement:student_login')
    else:
        form = StudentForm()
    return render(request, 'placement/student_register.html', {'form': form})


def student_login(request):
    msg = None
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            query = f"SELECT * FROM {Student._meta.db_table} WHERE email = %s AND password = %s LIMIT 1"
            students = QueryList(Student.objects.raw(query, [email, password])) # Raw SQL Read
            
            if students:
                request.session['student_id'] = students[0].student_id
                return redirect('placement:student_dashboard')
            msg = 'Invalid credentials'
    else:
        form = StudentLoginForm()
    return render(request, 'placement/student_login.html', {'form': form, 'msg': msg})


def company_register(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save() # ORM Write
            return redirect('placement:company_login')
    else:
        form = CompanyForm()
    return render(request, 'placement/company_register.html', {'form': form})


def company_login(request):
    msg = None
    if request.method == 'POST':
        form = CompanyLoginForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            query = f"SELECT * FROM {Company._meta.db_table} WHERE name = %s AND password = %s LIMIT 1"
            companies = QueryList(Company.objects.raw(query, [name, password])) # Raw SQL Read
            
            if companies:
                request.session['company_id'] = companies[0].company_id
                return redirect('placement:company_dashboard')
            msg = 'Invalid credentials'
    else:
        form = CompanyLoginForm()
    return render(request, 'placement/company_login.html', {'form': form, 'msg': msg})


def student_dashboard(request):
    sid = request.session.get('student_id')
    if not sid:
        return redirect('placement:student_login')
        
    students = QueryList(Student.objects.raw(f"SELECT * FROM {Student._meta.db_table} WHERE student_id = %s", [sid]))
    if not students:
        raise Http404("Student not found")
    student = students[0]
    
    jobs = QueryList(Job.objects.raw(f"SELECT * FROM {Job._meta.db_table}"))
    applications = QueryList(Application.objects.raw(f"SELECT * FROM {Application._meta.db_table} WHERE student_id = %s", [student.student_id]))

    total_applied = len(applications)
    accepted_count = sum(1 for a in applications if a.status == 'accepted')
    pending_count = sum(1 for a in applications if a.status == 'pending')
    rejected_count = sum(1 for a in applications if a.status == 'rejected')

    return render(request, 'placement/student_dashboard.html', {
        'student': student,
        'jobs': jobs,
        'applications': applications,
        'total_applied': total_applied,
        'accepted_count': accepted_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
    })


def company_dashboard(request):
    cid = request.session.get('company_id')
    if not cid:
        return redirect('placement:company_login')
        
    companies = QueryList(Company.objects.raw(f"SELECT * FROM {Company._meta.db_table} WHERE company_id = %s", [cid]))
    if not companies:
        raise Http404("Company not found")
    company = companies[0]
    
    jobs = QueryList(Job.objects.raw(f"SELECT * FROM {Job._meta.db_table} WHERE company_id = %s", [company.company_id]))
    
    apps_query = f"""
        SELECT a.* FROM {Application._meta.db_table} a
        INNER JOIN {Job._meta.db_table} j ON a.job_id = j.job_id
        WHERE j.company_id = %s
    """
    applications = QueryList(Application.objects.raw(apps_query, [company.company_id]))

    apps_by_status = {
        'pending': sum(1 for a in applications if a.status == 'pending'),
        'accepted': sum(1 for a in applications if a.status == 'accepted'),
        'rejected': sum(1 for a in applications if a.status == 'rejected'),
    }

    job_stats = []
    for job in jobs:
        job_apps = [a for a in applications if a.job_id == job.job_id]
        selected = sum(1 for a in job_apps if a.status == 'accepted')
        max_applicants = job.max_applicants or 1
        fill_percent = int(min(100, (selected / max_applicants) * 100))
        job_stats.append({
            'job': job,
            'applied': len(job_apps),
            'selected': selected,
            'ratio': f"{selected}/{job.max_applicants}",
            'fill_percent': fill_percent,
        })

    return render(request, 'placement/company_dashboard.html', {
        'company': company,
        'jobs': jobs,
        'applications': applications,
        'apps_by_status': apps_by_status,
        'job_stats': job_stats,
    })


def logout_view(request):
    request.session.flush()
    return redirect('placement:home')


def student_list(request):
    students = QueryList(Student.objects.raw(f"SELECT * FROM {Student._meta.db_table} ORDER BY student_id DESC"))
    return render(request, 'placement/student_list.html', {'students': students})


def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save() # ORM Write
            return redirect('placement:student_list')
    else:
        form = StudentForm()
    return render(request, 'placement/student_form.html', {'form': form})


def job_list(request):
    jobs = QueryList(Job.objects.raw(f"SELECT * FROM {Job._meta.db_table} ORDER BY job_id DESC"))
    return render(request, 'placement/job_list.html', {'jobs': jobs})


def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save() # ORM Write
            return redirect('placement:job_list')
    else:
        form = JobForm()
    return render(request, 'placement/job_form.html', {'form': form})


def application_list(request):
    applications = QueryList(Application.objects.raw(f"SELECT * FROM {Application._meta.db_table} ORDER BY applied_at DESC"))
    return render(request, 'placement/application_list.html', {'applications': applications})


def application_create(request, job_id=None):
    sid = request.session.get('student_id')
    if not sid:
        return redirect('placement:student_login')
        
    students = QueryList(Student.objects.raw(f"SELECT * FROM {Student._meta.db_table} WHERE student_id = %s", [sid])) # Raw Read
    if not students:
        raise Http404("Student not found")
    student = students[0]

    if job_id:
        jobs = QueryList(Job.objects.raw(f"SELECT * FROM {Job._meta.db_table} WHERE job_id = %s", [job_id])) # Raw Read
        if not jobs:
            raise Http404("Job not found")
        job = jobs[0]
        
        existing_query = f"SELECT * FROM {Application._meta.db_table} WHERE student_id = %s AND job_id = %s LIMIT 1"
        existing_apps = QueryList(Application.objects.raw(existing_query, [student.student_id, job.job_id])) # Raw Read
        if existing_apps:
            return render(request, 'placement/application_form.html', {
                'error': 'You already applied for this job.',
                'job': job,
                'student': student,
            })
            
        job_app_count = get_count(f"SELECT COUNT(*) FROM {Application._meta.db_table} WHERE job_id = %s", [job.job_id]) # Raw Read
        if job_app_count >= job.max_applicants:
            return render(request, 'placement/application_form.html', {
                'error': 'This job has reached the maximum applicants.',
                'job': job,
                'student': student,
            })

        if request.method == 'POST':
            # ORM Write! Django auto-handles the applied_at timestamp here
            Application.objects.create(student=student, job=job, status='pending')
            return redirect('placement:student_dashboard')

        return render(request, 'placement/application_form.html', {
            'job': job,
            'student': student,
        })

    # fallback list form for admin or manual apply
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            
            existing_query = f"SELECT * FROM {Application._meta.db_table} WHERE student_id = %s AND job_id = %s LIMIT 1"
            existing = QueryList(Application.objects.raw(existing_query, [app.student.student_id, app.job.job_id])) # Raw Read
            
            if existing:
                form.add_error(None, 'Duplicate application already exists.')
            else:
                app.status = 'pending'
                app.save() # ORM Write
                return redirect('placement:application_list')
    else:
        form = ApplicationForm()
    return render(request, 'placement/application_form.html', {'form': form})


def company_application_action(request, app_id, action):
    cid = request.session.get('company_id')
    if not cid:
        return redirect('placement:company_login')
        
    companies = QueryList(Company.objects.raw(f"SELECT * FROM {Company._meta.db_table} WHERE company_id = %s", [cid])) # Raw Read
    if not companies:
        raise Http404("Company not found")
    company = companies[0]

    app_query = f"""
        SELECT a.* FROM {Application._meta.db_table} a
        INNER JOIN {Job._meta.db_table} j ON a.job_id = j.job_id
        WHERE a.app_id = %s AND j.company_id = %s LIMIT 1
    """
    applications = QueryList(Application.objects.raw(app_query, [app_id, company.company_id])) # Raw Read
    if not applications:
        raise Http404("Application not found")
    application = applications[0]

    # ORM Updates
    if action == 'accept':
        application.status = 'accepted'
        application.save(update_fields=['status'])
    elif action == 'reject':
        application.status = 'rejected'
        application.save(update_fields=['status'])
            
    return redirect('placement:company_dashboard')
