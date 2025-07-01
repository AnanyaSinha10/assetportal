# views.py (Updated with proper debugging and error handling)

from datetime import date
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction, IntegrityError
from django.db.models import Sum, Q
from django.utils import timezone
from django.contrib import messages
from slugify import slugify
import logging

# Set up logging
logger = logging.getLogger(__name__)

from .forms import LoginForm, ReportFilterForm, AssetRequestForm, RequestReportFilterForm, SurveyInfoForm
from .models import AssetRequest, Location, Department, Category, STATUS_CHOICES, SystemModel, SurveyEntry, SurveyInfo


# --- Authentication Views ---
def login_view(request):
    """Handles user login."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """Handles user logout."""
    logout(request)
    return redirect('login')


# --- Helper Function for Approver Check ---
def is_approver(user):
    """Checks if a user belongs to the 'Approvers' group."""
    return user.groups.filter(name='Approvers').exists()


# --- Main Application Views ---
@login_required
def home(request):
    """Renders the home page with role-based links."""
    is_user_approver = is_approver(request.user)
    return render(request, 'home.html', {
        'is_user_approver': is_user_approver,
        'now': timezone.now()
    })

@login_required
def request_submission(request):
    """Handles the submission of new asset requests."""
    if request.method == 'POST':
        form = AssetRequestForm(request.POST, request.FILES)
        if form.is_valid():
            asset_request = form.save()
            request.session['last_request_id'] = asset_request.id
            return redirect('request_receipt')
        else:
            today = date.today()
            current_year = today.year
            financial_years = [f"{year}-{year+1}" for year in range(current_year-2, current_year + 6)]
            locations = Location.objects.all()
            departments = Department.objects.all()
            asset_types = Category.objects.all()

            context = {
                'form': form,
                'locations': locations,
                'departments': departments,
                'asset_types': asset_types,
                'financial_years': financial_years,
                'today': today.strftime("%Y-%m-%d"),
            }
            return render(request, 'request_form.html', context)
    else:
        form = AssetRequestForm()

    today = date.today()
    current_year = today.year
    financial_years = [f"{year}-{year+1}" for year in range(current_year-2, current_year + 6)]
    locations = Location.objects.all()
    departments = Department.objects.all()
    asset_types = Category.objects.all()

    context = {
        'form': form,
        'locations': locations,
        'departments': departments,
        'asset_types': asset_types,
        'financial_years': financial_years,
        'today': today.strftime("%Y-%m-%d"),
    }
    return render(request, 'request_form.html', context)


@login_required
def request_receipt_view(request):
    """Displays the receipt for a submitted asset request."""
    request_id = request.session.get('last_request_id')
    asset_request = None
    if request_id:
        try:
            asset_request = AssetRequest.objects.select_related(
                'location', 'department', 'asset_type'
            ).get(id=request_id)
            if 'last_request_id' in request.session:
                del request.session['last_request_id']
        except AssetRequest.DoesNotExist:
            asset_request = None

    return render(request, 'request_receipt.html', {'request_entry': asset_request})


@login_required
def request_report_view(request):
    """Displays a report of all asset requests, with filtering options."""
    requests = AssetRequest.objects.select_related('location', 'department', 'asset_type').order_by('-date', 'location__name', 'department__name')
    form = RequestReportFilterForm(request.GET or None)

    if form.is_valid():
        financial_year = form.cleaned_data.get('financial_year')
        if financial_year:
            requests = requests.filter(financial_year=financial_year)

    context = {
        'form': form,
        'requests': requests,
        'STATUS_CHOICES': STATUS_CHOICES
    }
    return render(request, 'request_report.html', context)


@login_required
@user_passes_test(is_approver, login_url='/login/')
def review_requests_view(request):
    """Allows approvers to review and change the status of pending requests."""
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        remarks = request.POST.get('remarks_field', '').strip()

        asset_request = get_object_or_404(AssetRequest, id=request_id)

        if action == 'approve':
            asset_request.status = 'approved'
        elif action == 'reject':
            asset_request.status = 'rejected'
        elif action == 'mark_duplicate':
            asset_request.status = 'duplicate'
        else:
            pass

        asset_request.remarks = remarks if remarks else None
        asset_request.save()
        return redirect('review_requests')

    pending_requests = AssetRequest.objects.filter(status='pending').select_related('location', 'department', 'asset_type').order_by('-date')
    context = {
        'pending_requests': pending_requests,
        'STATUS_CHOICES': STATUS_CHOICES
    }
    return render(request, 'review_requests.html', context)


@login_required
def survey_form_view(request):
    """Handles the survey form submission and display with improved error handling."""
    # Initialize variables
    form = SurveyInfoForm(request.GET or None)
    departments_in_location = Department.objects.none()
    unique_model_names = []
    table_data = []
    model_totals = {}
    
    location_obj = None
    category_obj = None
    survey_date = date.today()
    selected_financial_year = None
    
    # Handle GET request for form display and dynamic table generation
    if request.method == 'GET' and form.is_valid():
        location_obj = form.cleaned_data.get('location')
        category_obj = form.cleaned_data.get('category')
        survey_date = form.cleaned_data.get('date')
        selected_financial_year = form.cleaned_data.get('financial_year')

        if location_obj:
            departments_in_location = Department.objects.filter(location=location_obj).order_by('name')

        if location_obj and category_obj:
            all_relevant_models = SystemModel.objects.filter(
                location=location_obj,
                category=category_obj
            ).order_by('name')

            unique_model_names = list(all_relevant_models.values_list('name', flat=True).distinct().order_by('name'))

            for dept in departments_in_location:
                row_cells = []
                for model_name in unique_model_names:
                    row_cells.append({
                        'type': 'input',
                        'model_name': model_name,
                        'dept_id': dept.id,
                        'initial_value': ''
                    })
                table_data.append({'dept': dept, 'cells': row_cells})

    # Handle POST request for survey submission
    if request.method == 'POST':
        logger.info("Processing POST request for survey submission")
        
        form = SurveyInfoForm(request.POST)
        
        # Validate the basic form first
        if not form.is_valid():
            logger.error(f"Form validation failed: {form.errors}")
            messages.error(request, f"Form validation failed: {form.errors}")
            return render(request, 'survey_form.html', {
                'form': form,
                'departments_in_location': departments_in_location,
                'unique_model_names': unique_model_names,
                'table_data': table_data,
                'location_obj': location_obj,
                'category_obj': category_obj,
                'survey_date': survey_date,
                'selected_financial_year': selected_financial_year,
            })
        
        # Validate count inputs
        count_inputs_valid = True
        count_data = {}
        
        # Get the location and category from the valid form
        loc = form.cleaned_data.get('location')
        cat = form.cleaned_data.get('category')
        
        if not loc or not cat:
            messages.error(request, "Location and Category are required.")
            return render(request, 'survey_form.html', {
                'form': form,
                'departments_in_location': departments_in_location,
                'unique_model_names': unique_model_names,
                'table_data': table_data,
                'location_obj': location_obj,
                'category_obj': category_obj,
                'survey_date': survey_date,
                'selected_financial_year': selected_financial_year,
            })
        
        # Get departments and models for this location/category
        departments_in_location_post = Department.objects.filter(location=loc).order_by('name')
        all_relevant_models_for_post = SystemModel.objects.filter(
            location=loc,
            category=cat
        ).order_by('name')
        unique_model_names_for_post = list(all_relevant_models_for_post.values_list('name', flat=True).distinct().order_by('name'))
        
        # Validate all count inputs
        for dept in departments_in_location_post:
            for model_name in unique_model_names_for_post:
                slugified_model_name = slugify(model_name)
                input_name = f'count__{dept.id}__{slugified_model_name}'
                headcount_str = request.POST.get(input_name, '0').strip()
                
                logger.info(f"Processing input {input_name}: '{headcount_str}'")
                
                if headcount_str and not headcount_str.isdigit():
                    count_inputs_valid = False
                    messages.error(request, f"Invalid count for {model_name} in {dept.name}: '{headcount_str}' is not a valid number")
                    continue
                
                if headcount_str.isdigit():
                    headcount_value = int(headcount_str)
                    if headcount_value > 0:
                        count_data[input_name] = {
                            'dept': dept,
                            'model_name': model_name,
                            'headcount': headcount_value
                        }
        
        if not count_inputs_valid:
            logger.error("Count input validation failed")
            return render(request, 'survey_form.html', {
                'form': form,
                'departments_in_location': departments_in_location_post,
                'unique_model_names': unique_model_names_for_post,
                'table_data': table_data,
                'location_obj': loc,
                'category_obj': cat,
                'survey_date': form.cleaned_data.get('date', date.today()),
                'selected_financial_year': form.cleaned_data.get('financial_year'),
            })
        
        # Check if we have any data to save
        if not count_data:
            messages.warning(request, "No survey data entered. Please enter at least one count value.")
            return render(request, 'survey_form.html', {
                'form': form,
                'departments_in_location': departments_in_location_post,
                'unique_model_names': unique_model_names_for_post,
                'table_data': table_data,
                'location_obj': loc,
                'category_obj': cat,
                'survey_date': form.cleaned_data.get('date', date.today()),
                'selected_financial_year': form.cleaned_data.get('financial_year'),
            })
        
        # Save the data using transaction
        try:
            with transaction.atomic():
                logger.info("Starting atomic transaction for survey save")
                
                # Save the SurveyInfo object
                survey_info_instance = form.save()
                logger.info(f"Saved SurveyInfo with ID: {survey_info_instance.id}")
                
                entries_created = 0
                
                # Create SurveyEntry objects
                for input_name, data in count_data.items():
                    dept = data['dept']
                    model_name = data['model_name']
                    headcount = data['headcount']
                    
                    # Get or create the SystemModel
                    system_model_instance, created = SystemModel.objects.get_or_create(
                        name=model_name,
                        location=loc,
                        category=cat
                    )
                    
                    if created:
                        logger.info(f"Created new SystemModel: {system_model_instance}")
                    
                    # Create the SurveyEntry
                    survey_entry = SurveyEntry.objects.create(
                        survey_info=survey_info_instance,
                        location=loc,
                        department=dept,
                        system_model=system_model_instance,
                        headcount=headcount
                    )
                    entries_created += 1
                    logger.info(f"Created SurveyEntry: {survey_entry}")
                
                logger.info(f"Successfully created {entries_created} survey entries")
                messages.success(request, f"Survey saved successfully! Created {entries_created} entries.")
                
                # Store the survey info ID in session for receipt
                request.session['survey_info_id'] = survey_info_instance.id
                return redirect('survey_receipt')
                
        except IntegrityError as e:
            logger.error(f"Database integrity error during survey save: {e}")
            messages.error(request, f"Database error: {str(e)}. This might be due to duplicate entries.")
            
        except Exception as e:
            logger.error(f"Unexpected error during survey save: {e}")
            messages.error(request, f"An unexpected error occurred: {str(e)}")
    
    # Render the form
    context = {
        'form': form,
        'departments_in_location': departments_in_location,
        'unique_model_names': unique_model_names,
        'table_data': table_data,
        'location_obj': location_obj,
        'category_obj': category_obj,
        'survey_date': survey_date,
        'selected_financial_year': selected_financial_year,
    }
    
    return render(request, 'survey_form.html', context)


@login_required
def survey_receipt_view(request):
    """Displays the receipt for a submitted survey."""
    survey_info_id = request.session.get('survey_info_id')
    survey_info = None
    survey_entries = []
    
    if survey_info_id:
        try:
            survey_info = SurveyInfo.objects.select_related(
                'location', 'category'
            ).get(id=survey_info_id)
            
            survey_entries = SurveyEntry.objects.filter(
                survey_info=survey_info
            ).select_related('department', 'system_model').order_by(
                'department__name', 'system_model__name'
            )
            
            # Clear the session
            if 'survey_info_id' in request.session:
                del request.session['survey_info_id']
                
        except SurveyInfo.DoesNotExist:
            survey_info = None
            messages.error(request, "Survey not found.")
    
    return render(request, 'survey_receipt.html', {
        'survey_info': survey_info,
        'survey_entries': survey_entries
    })


@login_required
def consolidated_report_view(request):
    """Displays consolidated report of all surveys."""
    form = ReportFilterForm(request.GET or None)
    survey_entries = SurveyEntry.objects.select_related(
        'survey_info', 'location', 'department', 'system_model'
    ).order_by('-survey_info__date', 'location__name', 'department__name')
    
    if form.is_valid():
        financial_year = form.cleaned_data.get('financial_year')
        if financial_year:
            survey_entries = survey_entries.filter(survey_info__financial_year=financial_year)
    
    # Group entries by survey
    surveys = {}
    for entry in survey_entries:
        survey_id = entry.survey_info.id
        if survey_id not in surveys:
            surveys[survey_id] = {
                'info': entry.survey_info,
                'entries': []
            }
        surveys[survey_id]['entries'].append(entry)
    
    context = {
        'form': form,
        'surveys': surveys.values(),
        'total_entries': survey_entries.count()
    }
    
    return render(request, 'consolidated_report.html', context)
