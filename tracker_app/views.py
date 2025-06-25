import os
import time
import threading
import pyautogui
import requests
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from .models import Employee, TimeLog
from django.views.decorators.cache import never_cache
from django.utils.dateparse import parse_duration

# Manage running screenshot threads
screenshot_threads = {}

# API URL to send screenshots
API_URL = "https://kalathiyainfotechapi.in/api/screenshots"

# Function to capture and send screenshots
def take_screenshots(session_id, employee_name):
    while screenshot_threads.get(session_id, {}).get("running"):
        if screenshot_threads[session_id].get("paused"):
            time.sleep(1)
            continue

        now = timezone.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        folder = os.path.join("media", "screenshots", employee_name, date_str)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{time_str}.png")

        # Capture and save screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(path)

        print(f"[✓] Saved screenshot: {path}")

        # Upload to Laravel API
        try:
            with open(path, 'rb') as f:
                files = {'screenshot': f}
                data = {
                    'employee_name': employee_name,
                    'timestamp': now.strftime("%Y-%m-%d %H:%M:%S")
                }
                response = requests.post(API_URL, files=files, data=data)

            if response.status_code == 200:
                print(f"[↑] Screenshot uploaded successfully for {employee_name}")
            else:
                print(f"[!] Failed to upload screenshot: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"[x] Error uploading screenshot: {e}")

        time.sleep(10)  # Take screenshot every 10 seconds

# Login-required decorator
@never_cache
def staff_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'emp_id' not in request.session:
            return redirect('login_view')
        return view_func(request, *args, **kwargs)
    return wrapper

# Tracker view
@never_cache
def tracker(request):
    emp_id = request.session.get('emp_id')
    if not emp_id:
        return redirect('login_view')

    try:
        emp = Employee.objects.get(id=emp_id)
    except Employee.DoesNotExist:
        request.session.flush()
        return redirect('login_view')

    today = timezone.now().date()
    log, _ = TimeLog.objects.get_or_create(emp=emp, date=today)

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "start_tracker" and not log.start_tracker:
            log.start_tracker = timezone.now()
            log.save()

            screenshot_threads[log.id] = {"running": True, "paused": False}
            thread = threading.Thread(
                target=take_screenshots,
                args=(log.id, emp.name),
                daemon=True
            )
            thread.start()

        elif action == "end_tracker":
            if not log.end_tracker:
                log.end_tracker = timezone.now()

            log.total_time = parse_duration(request.POST.get("total_time") or "0:00:00")
            log.pause_time = parse_duration(request.POST.get("pause_time") or "0:00:00")
            log.work_time = parse_duration(request.POST.get("work_time") or "0:00:00")
            log.save()

            if log.id in screenshot_threads:
                screenshot_threads[log.id]["running"] = False

        return redirect('tracker')

    return render(request, 'tracker.html', {'emp': emp, 'log': log})

# Login view
@never_cache
def login_view(request):
    if request.session.get('emp_id'):
        return redirect('tracker')

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            emp = Employee.objects.get(email=email, password=password)
            request.session['emp_id'] = emp.id
            return redirect('tracker')
        except Employee.DoesNotExist:
            return render(request, 'login.html', {'error': 'Invalid email or password'})

    return render(request, 'login.html')

# Logout view
@never_cache
def logout_view(request):
    request.session.flush()
    return redirect('login_view')
