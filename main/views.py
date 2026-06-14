from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Task, AuditLog, Profile
from .forms import RegisterForm, TaskForm, ProfileForm
from django.utils import timezone


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def get_greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    return "Good evening"

def log_action(user, action, request):
    AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=get_client_ip(request)
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            log_action(user, 'User logged in', request)
            return redirect('dashboard')
        else:
            log_action(None, f'Failed login attempt for username: {username}', request)
            messages.error(request, 'Invalid username or password')
    return render(request, 'main/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        log_action(request.user, 'User logged out', request)
        logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(user, 'New user registered', request)
            messages.success(request, 'Account created. Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


@login_required
def dashboard(request):
    if request.user.is_staff:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(created_by=request.user)
    completed = tasks.filter(status='completed').count()
    return render(request, 'main/dashboard.html', {
        'tasks': tasks,
        'greeting': get_greeting(),
        'completed': completed
    })

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            log_action(request.user, f'Created task: {task.title}', request)
            messages.success(request, 'Task created.')
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'main/task_form.html', {'form': form, 'action': 'Create'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not request.user.is_staff and task.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            log_action(request.user, f'Edited task: {task.title}', request)
            messages.success(request, 'Task updated.')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)
    return render(request, 'main/task_form.html', {'form': form, 'action': 'Edit'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not request.user.is_staff and task.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    if request.method == 'POST':
        log_action(request.user, f'Deleted task: {task.title}', request)
        task.delete()
        messages.success(request, 'Task deleted.')
    return redirect('dashboard')


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
            log_action(request.user, 'Updated profile', request)
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'main/profile.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def audit_log_view(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'main/audit_log.html', {'logs': logs})


def custom_404(request, exception):
    return render(request, 'main/404.html', status=404)


def custom_500(request):
    return render(request, 'main/500.html', status=500)