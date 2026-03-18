from django.db import models

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

    def __str__(self):
        return f"{self.name} ({self.roll_no})"


class PlacementSection(models.Model):
    section_id = models.AutoField(primary_key=True)
    section_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    password = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.section_name


class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    website_link = models.URLField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    password = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    job_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    section = models.ForeignKey(PlacementSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    position = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    max_applicants = models.PositiveIntegerField(default=100)
    pay_rate = models.CharField(max_length=80, blank=True)
    post_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.position} @ {self.company.name}"


class Application(models.Model):
    app_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=60, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} -> {self.job.position} ({self.status})"
