from django import forms
from .models import Student, Job, Application, Company


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing_classes + ' form-control').strip()
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label


class StudentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_no', 'email', 'phone', 'password', 'profile_pic', 'github', 'linkedin', 'resume', 'skills']
        widgets = {
            'password': forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Python, SQL, Django'}),
        }


class CompanyForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'website_link', 'location', 'password']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Company description'}),
            'password': forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        }


class JobForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Job
        fields = ['company', 'section', 'position', 'description', 'max_applicants', 'pay_rate']


class ApplicationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ['student', 'job', 'status']


class StudentLoginForm(StyledFormMixin, forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))


class CompanyLoginForm(StyledFormMixin, forms.Form):
    name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))
