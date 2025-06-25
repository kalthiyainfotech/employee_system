import os
import time
import threading
import pyautogui
import requests
from datetime import timedelta
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.utils.dateparse import parse_duration
from .models import Employee, TimeLog

# Global dictionary to manage screenshot threads
screenshot_threads = {}


# Screenshot function: saves locally and uploads every 10 seconds
def take_screenshots(session_id, user_id):
    while screenshot_threads.get(session_id, {}).get("running"):
        if screenshot_threads[session_id].get("paused"):
            time.sleep(1)
            continue

        now = timezone.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        folder = os.path.join("media", "screenshots", str(user_id), date_str)
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"{time_str}.png")

        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(file_path)
            print(f"[✔] Screenshot saved: {file_path}")
        except Exception as e:
            print(f"[✘] Screenshot error: {e}")
            time.sleep(10)
            continue

        # Upload to API
        try:
            with open(file_path, 'rb') as image_file:
                response = requests.post(
                    "https://kalathiyainfotechapi.in/api/screenshots",
                    files={'image': image_file},
                    data={'user_id': str(user_id)}
                )
                print(f"[↑] Upload status: {response.status_code}")
                if response.status_code != 201:
                    print(f"[!] Upload error: {response.text}")
        except Exception as api_error:
            print(f"[✘] Upload failed: {api_error}")

        time.sleep(10)


# Decorator to ensure employee is logged in
@never_cache
def staff_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'emp_id' not in request.session:
            return redirect('login_view')
        return view_func(request, *args, **kwargs)
    return wrapper


# Tracker View
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
    log, created = TimeLog.objects.get_or_create(emp=emp, date=today)

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "start_tracker" and not log.start_tracker:
            log.start_tracker = timezone.now()
            log.save()

            # Start screenshot thread
            screenshot_threads[log.id] = {"running": True, "paused": False}
            thread = threading.Thread(
                target=take_screenshots,
                args=(log.id, emp.id),
                daemon=True
            )
            thread.start()

        elif action == "end_tracker":
            if not log.end_tracker:
                log.end_tracker = timezone.now()

            total_str = request.POST.get("total_time")
            pause_str = request.POST.get("pause_time")
            work_str = request.POST.get("work_time")

            if total_str:
                log.total_time = parse_duration(total_str)
            if pause_str:
                log.pause_time = parse_duration(pause_str)
            if work_str:
                log.work_time = parse_duration(work_str)

            log.save()

            # Stop screenshot thread
            if log.id in screenshot_threads:
                screenshot_threads[log.id]["running"] = False

        return redirect('tracker')

    return render(request, 'tracker.html', {'emp': emp, 'log': login_view})


# Login View
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


# Logout View
@never_cache
def logout_view(request):
    emp_id = request.session.get('emp_id')
    if emp_id:
        today = timezone.now().date()
        try:
            log = TimeLog.objects.get(emp_id=emp_id, date=today)
            if log.id in screenshot_threads:
                screenshot_threads[log.id]["running"] = False
        except TimeLog.DoesNotExist:
            pass
    request.session.flush()
    return redirect('login_view')
