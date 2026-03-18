from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, Job, Application, Company
from .forms import StudentForm, CompanyForm, JobForm, ApplicationForm, StudentLoginForm, CompanyLoginForm


def home(request):
    companies = Company.objects.all().prefetch_related('jobs')
    company_job_summary = []
    company_data = []
    for company in companies:
        jobs = list(company.jobs.all())
        apps = list(Application.objects.filter(job__company=company).select_related('student', 'job'))
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

    return render(request, 'placement/home.html', {
        'student_count': Student.objects.count(),
        'job_count': Job.objects.count(),
        'application_count': Application.objects.count(),
        'company_job_summary': company_job_summary,
        'company_data': company_data,
        'selected_company_id': selected_company_id,
    })

def companies(request, company_id=None):
    companies = Company.objects.all().prefetch_related('jobs')
    selected_company_id = company_id or request.GET.get('company_id')
    selected_company_id = int(selected_company_id) if selected_company_id and str(selected_company_id).isdigit() else None
    if selected_company_id is None and companies:
        selected_company_id = companies.first().company_id
    selected = companies.filter(company_id=selected_company_id).first() if selected_company_id else None
    applications = Application.objects.filter(job__company=selected).select_related('student', 'job') if selected else []
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
            form.save()
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
            student = Student.objects.filter(email=email, password=password).first()
            if student:
                request.session['student_id'] = student.student_id
                return redirect('placement:student_dashboard')
            msg = 'Invalid credentials'
    else:
        form = StudentLoginForm()
    return render(request, 'placement/student_login.html', {'form': form, 'msg': msg})


def company_register(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
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
            company = Company.objects.filter(name=name, password=password).first()
            if company:
                request.session['company_id'] = company.company_id
                return redirect('placement:company_dashboard')
            msg = 'Invalid credentials'
    else:
        form = CompanyLoginForm()
    return render(request, 'placement/company_login.html', {'form': form, 'msg': msg})


def student_dashboard(request):
    sid = request.session.get('student_id')
    if not sid:
        return redirect('placement:student_login')
    student = get_object_or_404(Student, student_id=sid)
    jobs = Job.objects.select_related('company').all()
    applications = Application.objects.filter(student=student).select_related('job')

    total_applied = applications.count()
    accepted_count = applications.filter(status='accepted').count()
    pending_count = applications.filter(status='pending').count()
    rejected_count = applications.filter(status='rejected').count()

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
    company = get_object_or_404(Company, company_id=cid)
    jobs = Job.objects.filter(company=company)
    applications = Application.objects.filter(job__company=company).select_related('student', 'job')

    apps_by_status = {
        'pending': applications.filter(status='pending').count(),
        'accepted': applications.filter(status='accepted').count(),
        'rejected': applications.filter(status='rejected').count(),
    }

    job_stats = []
    for job in jobs:
        job_apps = applications.filter(job=job)
        selected = job_apps.filter(status='accepted').count()
        max_applicants = job.max_applicants or 1
        fill_percent = int(min(100, (selected / max_applicants) * 100))
        job_stats.append({
            'job': job,
            'applied': job_apps.count(),
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
    students = Student.objects.all().order_by('-student_id')
    return render(request, 'placement/student_list.html', {'students': students})


def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('placement:student_list')
    else:
        form = StudentForm()
    return render(request, 'placement/student_form.html', {'form': form})


def job_list(request):
    jobs = Job.objects.select_related('company', 'section').order_by('-job_id')
    return render(request, 'placement/job_list.html', {'jobs': jobs})


def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('placement:job_list')
    else:
        form = JobForm()
    return render(request, 'placement/job_form.html', {'form': form})


def application_list(request):
    applications = Application.objects.select_related('student', 'job').order_by('-applied_at')
    return render(request, 'placement/application_list.html', {'applications': applications})


def application_create(request, job_id=None):
    sid = request.session.get('student_id')
    if not sid:
        return redirect('placement:student_login')
    student = get_object_or_404(Student, student_id=sid)

    if job_id:
        job = get_object_or_404(Job, job_id=job_id)
        if Application.objects.filter(student=student, job=job).exists():
            return render(request, 'placement/application_form.html', {
                'error': 'You already applied for this job.',
                'job': job,
                'student': student,
            })
        if job.applications.count() >= job.max_applicants:
            return render(request, 'placement/application_form.html', {
                'error': 'This job has reached the maximum applicants.',
                'job': job,
                'student': student,
            })

        if request.method == 'POST':
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
            if Application.objects.filter(student=app.student, job=app.job).exists():
                form.add_error(None, 'Duplicate application already exists.')
            else:
                app.status = 'pending'
                app.save()
                return redirect('placement:application_list')
    else:
        form = ApplicationForm()
    return render(request, 'placement/application_form.html', {'form': form})


def company_application_action(request, app_id, action):
    cid = request.session.get('company_id')
    if not cid:
        return redirect('placement:company_login')
    company = get_object_or_404(Company, company_id=cid)
    application = get_object_or_404(Application, app_id=app_id, job__company=company)

    if action == 'accept':
        application.status = 'accepted'
        application.save()
    elif action == 'reject':
        application.status = 'rejected'
        application.save()
    return redirect('placement:company_dashboard')
