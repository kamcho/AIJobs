from django import forms
from .models import Application, JobListing, JobRequirement, Company
from users.models import UserDocument

class ApplicationForm(forms.ModelForm):
    cv_used = forms.ModelChoiceField(
        queryset=UserDocument.objects.none(),
        label="Select CV",
        required=True,
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    class Meta:
        model = Application
        fields = ['cv_used']
    
    cover_letter_text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 15, 'placeholder': 'Your AI-generated cover letter will appear here...'}),
        required=False,
        label="Cover Letter"
    )

    file_format = forms.ChoiceField(
        choices=[('pdf', 'PDF (.pdf)'), ('docx', 'Word (.docx)')],
        initial='pdf',
        widget=forms.RadioSelect(attrs={'class': 'format-radio'}),
        label="Choose your preferred file format"
    )

    cover_letter_file = forms.FileField(
        required=False, 
        label="Upload Cover Letter (PDF/DOCX)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Only show CVs belonging to the user
            self.fields['cv_used'].queryset = UserDocument.objects.filter(
                user=user, 
                document_type__name='CV'
            )

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('cover_letter_text')
        file = cleaned_data.get('cover_letter_file')

        if not text and not file:
            raise forms.ValidationError("Please either generate a cover letter or upload a file.")
        
        return cleaned_data

class JobListingForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = [
            'title', 'category', 'terms', 'company', 'company_profile', 'description', 
            'location', 'url', 'education_level_required', 
            'experience_required_years', 'application_method', 'employer_email', 
            'application_url', 'application_instructions', 'expiry_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'application_instructions': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Optional: Add special instructions for applicants'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].required = False
        self.fields['company_profile'].required = False
        self.fields['url'].required = False
        for field in self.fields:
            if field != 'expiry_date' and field != 'description':
                self.fields[field].widget.attrs.update({'class': 'form-input'})

    def save(self, commit=True):
        job = super().save(commit=False)
        company_profile = self.cleaned_data.get('company_profile')
        if company_profile and not job.company:
            job.company = company_profile.name
        
        # Sync with application_url if url is empty
        app_url = self.cleaned_data.get('application_url')
        if app_url and not job.url:
            job.url = app_url
        elif not job.url:
            # Fallback to a placeholder if absolutely empty and required by DB
            job.url = "https://example.com"
            
        if commit:
            job.save()
        return job

class JobRequirementForm(forms.ModelForm):
    class Meta:
        model = JobRequirement
        fields = ['description', 'is_mandatory']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 3+ years of Python experience'}),
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'logo', 'description', 'website', 'location',
            'primary_phone', 'secondary_phone', 'primary_email', 'secondary_email',
            'founded_in'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'founded_in': forms.NumberInput(attrs={'class': 'form-input', 'min': '1900', 'max': '2100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'description' and field != 'logo':
                self.fields[field].widget.attrs.update({'class': 'form-input'})

class PublicApplicationForm(forms.Form):
    full_name = forms.CharField(
        label="Full Name", 
        max_length=255, 
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. John Doe'})
    )
    email = forms.EmailField(
        label="Email Address", 
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'e.g. john@example.com'})
    )
    phone = forms.CharField(
        label="Phone Number", 
        max_length=20, 
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. +1234567890'})
    )
    cv_file = forms.FileField(
        label="Upload CV (PDF/DOCX)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx'})
    )
    cover_letter_text = forms.CharField(
        label="Cover Letter",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 8, 'placeholder': 'Explain why you are a good fit...'})
    )
    cover_letter_file = forms.FileField(
        required=False, 
        label="Or Upload Cover Letter File",
        widget=forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx'})
    )

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('cover_letter_text')
        file = cleaned_data.get('cover_letter_file')
        if not text and not file:
             # It's okay to be optional if that's the requirement, but usually one is needed.
             # User prompt said "ask for ... cover letter", implying it's needed.
             # Let's make at least one required.
             raise forms.ValidationError("Please provide a cover letter (text or file).")
        return cleaned_data
