from django import forms
from .models import Application, JobListing, JobRequirement
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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Only show CVs belonging to the user
            self.fields['cv_used'].queryset = UserDocument.objects.filter(
                user=user, 
                document_type__name='CV'
            )

class JobListingForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = [
            'title', 'category', 'company', 'description', 
            'location', 'url', 'education_level_required', 
            'experience_required_years', 'employer_email', 'expiry_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'expiry_date' and field != 'description':
                self.fields[field].widget.attrs.update({'class': 'form-input'})

class JobRequirementForm(forms.ModelForm):
    class Meta:
        model = JobRequirement
        fields = ['description', 'is_mandatory']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 3+ years of Python experience'}),
        }
