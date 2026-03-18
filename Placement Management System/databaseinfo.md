# 📊 Placement Management System - Database & Queries

---

## 🗄️ Database Creation

### 🔹 Student Table

```python
class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120)
    roll_no = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    password = models.CharField(max_length=128)
    profile_pic = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    resume = models.URLField(blank=True)
    skills = models.TextField(blank=True)
```

```sql
CREATE TABLE Student (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    roll_no VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    phone VARCHAR(30),
    password VARCHAR(128) NOT NULL,
    profile_pic TEXT,
    github TEXT,
    linkedin TEXT,
    resume TEXT,
    skills TEXT
);
```

---

### 🔹 PlacementSection Table

```python
class PlacementSection(models.Model):
    section_id = models.AutoField(primary_key=True)
    section_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    password = models.CharField(max_length=128, blank=True)
```

```sql
CREATE TABLE PlacementSection (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_name VARCHAR(120) NOT NULL,
    email VARCHAR(254),
    phone VARCHAR(30),
    password VARCHAR(128)
);
```

---

### 🔹 Company Table

```python
class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    website_link = models.URLField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    password = models.CharField(max_length=128, blank=True)
```

```sql
CREATE TABLE Company (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    website_link TEXT,
    location VARCHAR(120),
    password VARCHAR(128)
);
```

---

### 🔹 Job Table

```python
class Job(models.Model):
    job_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    section = models.ForeignKey(PlacementSection, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    max_applicants = models.PositiveIntegerField(default=100)
    pay_rate = models.CharField(max_length=80, blank=True)
    post_date = models.DateField(auto_now_add=True)
```

```sql
CREATE TABLE Job (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    section_id INTEGER,
    position VARCHAR(120) NOT NULL,
    description TEXT,
    max_applicants INTEGER DEFAULT 100,
    pay_rate VARCHAR(80),
    post_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (company_id) REFERENCES Company(company_id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES PlacementSection(section_id) ON DELETE SET NULL
);
```

---

### 🔹 Application Table

```python
class Application(models.Model):
    app_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    status = models.CharField(max_length=60, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
```

```sql
CREATE TABLE Application (
    app_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    status VARCHAR(60) DEFAULT 'pending',
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES Job(job_id) ON DELETE CASCADE
);
```

---

## 🔄 Project Flow (Django → SQL)

### Student Registration

```python
student = form.save()
```

```sql
INSERT INTO Student (name, roll_no, email, phone, password)
VALUES ('Ayush', 'CS101', 'ayush@gmail.com', '9876543210', 'hashed_password');
```

### Manual Save

```python
student = Student(name=request.POST['name'], roll_no=request.POST['roll_no'], email=request.POST['email'])
student.save()
```

```sql
INSERT INTO Student (name, roll_no, email)
VALUES ('Ayush', 'CS101', 'ayush@gmail.com');
```

### Company Registration

```python
form.save()
```

```sql
INSERT INTO Company (name, description, website_link, location, password)
VALUES ('Google', 'Tech Company', 'https://google.com', 'Bangalore', 'pass123');
```

### Job Creation

```python
job = form.save(commit=False)
job.company = request.user.company
job.save()
```

```sql
INSERT INTO Job (company_id, position)
VALUES (1, 'Software Engineer');
```

### Apply Job

```python
Application.objects.create(student=student, job=job)
```

```sql
INSERT INTO Application (student_id, job_id)
VALUES (1, 1);
```

### Prevent Duplicate Application

```python
Application.objects.filter(student=student, job=job).exists()
```

```sql
SELECT EXISTS (
    SELECT 1 FROM Application WHERE student_id=1 AND job_id=1
);
```

### Password Hashing

```python
make_password(request.POST['password'])
```

```sql
-- Stored as hashed value
```

---

## 📊 Queries

### 1. Companies Applied by Student

```python
Application.objects.filter(student_id=1).values('job__company').distinct().count()
```

```sql
SELECT COUNT(DISTINCT Job.company_id)
FROM Application
JOIN Job ON Application.job_id = Job.job_id
WHERE Application.student_id = 1;
```

### 2. Applications per Student

```python
Student.objects.annotate(total_apps=Count('application'))
```

```sql
SELECT Student.name, COUNT(Application.app_id)
FROM Student
LEFT JOIN Application ON Student.student_id = Application.student_id
GROUP BY Student.student_id;
```

### 3. Students per Job

```python
Job.objects.annotate(total_students=Count('application'))
```

```sql
SELECT Job.position, COUNT(Application.app_id)
FROM Job
LEFT JOIN Application ON Job.job_id = Application.job_id
GROUP BY Job.job_id;
```

### 4. Jobs Applied by Student

```python
Job.objects.filter(application__student_id=1)
```

```sql
SELECT Job.*
FROM Job
JOIN Application ON Job.job_id = Application.job_id
WHERE Application.student_id = 1;
```

### 5. Students Applied to Company

```python
Student.objects.filter(application__job__company_id=1).distinct()
```

```sql
SELECT DISTINCT Student.*
FROM Student
JOIN Application ON Student.student_id = Application.student_id
JOIN Job ON Application.job_id = Job.job_id
WHERE Job.company_id = 1;
```

### 6. Selected Applications

```python
Application.objects.filter(status='selected')
```

```sql
SELECT * FROM Application WHERE status='selected';
```

### 7. Selected Students per Company

```python
Company.objects.annotate(selected_count=Count('job__application'))
```

```sql
SELECT Company.name, COUNT(Application.app_id)
FROM Company
JOIN Job ON Company.company_id = Job.company_id
JOIN Application ON Job.job_id = Application.job_id
WHERE Application.status='selected'
GROUP BY Company.company_id;
```

### 8. Latest Jobs

```python
Job.objects.order_by('-post_date')[:5]
```

```sql
SELECT * FROM Job ORDER BY post_date DESC LIMIT 5;
```

### 9. Jobs Below Max Applicants

```python
Job.objects.annotate(app_count=Count('application')).filter(app_count__lt=F('max_applicants'))
```

```sql
SELECT Job.*, COUNT(Application.app_id) AS app_count
FROM Job
LEFT JOIN Application ON Job.job_id = Application.job_id
GROUP BY Job.job_id
HAVING app_count < Job.max_applicants;
```

### 10. Check Already Applied

```python
Application.objects.filter(student_id=1, job_id=1).exists()
```

```sql
SELECT EXISTS (SELECT 1 FROM Application WHERE student_id=1 AND job_id=1);
```

### 11. Search Jobs

```python
Job.objects.filter(position__icontains='engineer')
```

```sql
SELECT * FROM Job WHERE position LIKE '%engineer%';
```

### 12. Total Companies

```python
Company.objects.count()
```

```sql
SELECT COUNT(*) FROM Company;
```

### 13. Total Students

```python
Student.objects.count()
```

```sql
SELECT COUNT(*) FROM Student;
```

### 14. Applications per Company

```python
Company.objects.annotate(total_apps=Count('job__application'))
```

```sql
SELECT Company.name, COUNT(Application.app_id)
FROM Company
JOIN Job ON Company.company_id = Job.company_id
JOIN Application ON Job.job_id = Application.job_id
GROUP BY Company.company_id;
```

### 15. Full JOIN Data

```python
Application.objects.select_related('student', 'job__company')
```

```sql
SELECT *
FROM Application
JOIN Student ON Application.student_id = Student.student_id
JOIN Job ON Application.job_id = Job.job_id
JOIN Company ON Job.company_id = Company.company_id;
```

---

