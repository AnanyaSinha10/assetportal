from datetime import date
from django import forms
from .models import (
    AssetRequest, Category, Department, Location,
    SubCategory, SurveyInfo,  SystemModel
)

# -------------------------------
# LOGIN FORM
# -------------------------------
class LoginForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')


# -------------------------------
# ASSET REQUEST FORM
# -------------------------------
class AssetRequestForm(forms.ModelForm):
    class Meta:
        model = AssetRequest
        fields = [
            'location', 'department', 'financial_year', 'asset_type',
            'description', 'estimated_cost', 'item_type', 'date',
            'indent_file', 'annexure_x', 'annexure_y', 'gem_file',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


# -------------------------------
# SURVEY INFO FORM (Corrected)
# -------------------------------
class SurveyInfoForm(forms.ModelForm):
    financial_year = forms.ChoiceField(choices=[], required=True)

    class Meta:
        model = SurveyInfo
        fields = ['location', 'category', 'date', 'financial_year']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = date.today()
        current_year = today.year
        if today.month >= 4:
            fin_year_start = current_year
        else:
            fin_year_start = current_year - 1

        # Build dynamic financial year choices
        financial_year_choices = []
        for i in range(-2, 6):  # E.g., 2022–2023 to 2030–2031
            start_year = fin_year_start + i
            end_year = start_year + 1
            fy_label = f"{start_year}-{end_year}"
            financial_year_choices.append((fy_label, fy_label))

        self.fields['financial_year'].choices = financial_year_choices

        # Set initial value if form is not bound
        if not self.is_bound and 'financial_year' not in self.initial:
            self.initial['financial_year'] = f"{fin_year_start}-{fin_year_start+1}"


# -------------------------------
# REPORT FILTER FORM (Used for consolidated report)
# -------------------------------
class ReportFilterForm(forms.Form):
    financial_year = forms.CharField(
        max_length=9,
        required=False,
        label='Financial Year',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., 2025-2026',
            'class': 'form-input'
        })
    )


# -------------------------------
# REQUEST REPORT FILTER FORM (Used in asset request report)
# -------------------------------
class RequestReportFilterForm(forms.Form):
    financial_year = forms.ChoiceField(choices=[], required=False, label="Financial Year")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        current_year = today.year
        if today.month >= 4:
            fin_year_start = current_year
        else:
            fin_year_start = current_year - 1

        current_financial_year_str = f"{fin_year_start}-{fin_year_start+1}"

        financial_years_choices = [('', 'All Years')]
        for i in range(-1, 6):
            start_year = fin_year_start + i
            end_year = start_year + 1
            financial_years_choices.append((f"{start_year}-{end_year}", f"{start_year}-{end_year}"))

        self.fields['financial_year'].choices = financial_years_choices

        if not self.is_bound:
            self.fields['financial_year'].initial = current_financial_year_str
