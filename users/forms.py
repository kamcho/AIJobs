from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import MyUser, PersonalProfile, WorkExperience, Education, MySkill, UserDocument

class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = MyUser
        fields = ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'Job Seeker'
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = PersonalProfile
        fields = (
            'full_name', 'phone_primary', 'phone_secondary', 
            'gender', 'date_of_birth', 'city', 'country', 
            'bio', 'linkedin_url', 'portfolio_url', 'profile_picture'
        )
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input'})

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = (
            'company_name', 'job_title', 'location', 
            'start_date', 'end_date', 'is_current', 
            'description', 'referee_name', 'referee_contact'
        )
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'is_current':
                self.fields[field].widget.attrs.update({'class': 'form-input'})

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ('institution', 'level', 'field_of_study', 'start_date', 'end_date', 'grade')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input'})

class MySkillForm(forms.ModelForm):
    class Meta:
        model = MySkill
        fields = ('name', 'proficiency')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input'})

class UserDocumentForm(forms.ModelForm):
    class Meta:
        model = UserDocument
        fields = ('document_type', 'file')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input'})

class JobPreferenceForm(forms.ModelForm):
    class Meta:
        model = PersonalProfile
        fields = ('preferred_categories',)
        widgets = {
            'preferred_categories': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We don't want the default form-input class for checkboxes as it might break styling
