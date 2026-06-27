from django.shortcuts import render, redirect, get_object_or_404
from .forms import StudentRegistrationForm, InstructorRegistrationForm
from django.contrib import messages
from .services import StudentRegistration
from .services import InstructorRegistration
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from .permissions import admin_only
# Create your views here.


@login_required
@admin_only
def student_registration_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            StudentRegistration(form)
            messages.success(request, "Registration successful!")
            return redirect('home')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        'StudentRegistration.html',
        {'form': form}
    )

@login_required
@admin_only
def instructor_registration_view(request):
    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST)
        if form.is_valid():
            InstructorRegistration(form)
            messages.success(request, "Registeration successful!")
            return redirect('home')
        
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InstructorRegistrationForm()
    return render(request, 'InstructorRegistration.html',{'form':form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if hasattr(user,'student_profile'):
                return redirect('student_dashboard')
            elif hasattr(user, 'instructor_profile'):
                print("Hello ")
                return redirect('academics/instructor:instructor_dashboard')
            else:
                return redirect('accouts:login')
        else:
            return redirect('accounts:login')
    return render(request,'login.html',{})

@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')
