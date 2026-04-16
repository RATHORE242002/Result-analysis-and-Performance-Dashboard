from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .models import Profile, Student, Subject, Result, UploadFile
from .forms import UploadFileForm
import pandas as pd
import json


# 🔐 LOGIN
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            profile, _ = Profile.objects.get_or_create(user=user)
            role = profile.role.strip().lower()

            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'hod':
                return redirect('hod_dashboard')
            elif role == 'faculty':
                return redirect('faculty_dashboard')
            elif role == 'student':
                return redirect('student_home')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password ❌'})

    return render(request, 'login.html')


# 📝 REGISTER (FIXED)
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role').strip().lower()

        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()

          # ✅ FIXED (NO DUPLICATE ERROR)
        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()

        if role == 'student':
            Student.objects.create(
                user=user,
                name=username,
                roll_no=username,
                batch="N/A",
                course="N/A"
            )

        return redirect('login')

    return render(request, 'register.html')


# 🚪 LOGOUT
def user_logout(request):
    logout(request)
    return redirect('login')


# 📊 DASHBOARDS
@login_required
def admin_dashboard(request):
    if request.user.profile.role != 'admin':
        return redirect('login')
    return render(request, 'admin_dashboard.html')


@login_required
def hod_dashboard(request):
    if request.user.profile.role != 'hod':
        return redirect('login')
    return render(request, 'hod_dashboard.html')


@login_required
def faculty_dashboard(request):
    if request.user.profile.role != 'faculty':
        return redirect('login')
    return render(request, 'faculty_dashboard.html')


# ❌ DELETE FILE
@login_required
def delete_file(request, id):
    file = get_object_or_404(UploadFile, id=id)
    file.delete()
    return redirect('upload')


# 📤 FILE UPLOAD (FINAL FIXED)
@login_required
def upload_file(request):

    if request.user.profile.role not in ['admin', 'faculty']:
        return redirect('login')
    
    files = UploadFile.objects.all()   # ✅ ALWAYS FETCH FILES

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES['file']

            file_obj = UploadFile.objects.create(file=file)

            try:
                if file.name.endswith('.xlsx'):
                     df = pd.read_excel(file, dtype=str)
                else:
                    df = pd.read_csv(file, dtype= str)
            except Exception as e:
                return render(request, 'upload.html', {'error': str(e)})

            for _, row in df.iterrows():

                name = str(row.get('Name', '')).strip()
                roll = str(row.get('Roll', '')).strip()   # ✅ FIX

                if not name or not roll:
                    continue

                subject_name = str(row.get('Subject', '')).strip()
                marks = row.get('Marks')
                semester = row.get('Semester')
                batch = str(row.get('Batch', 'N/A')).strip()
                course = str(row.get('Course', 'N/A')).strip()

                if not subject_name or pd.isna(marks) or pd.isna(semester):
                    continue

                try:
                    marks = int(marks)
                    semester = int(semester)
                except:
                    continue

                student, _ = Student.objects.get_or_create(
                    roll_no=roll,
                    defaults={
                        'name': name,
                        'batch': batch,
                        'course': course
                    }
                )

                subject, _ = Subject.objects.get_or_create(name=subject_name)

                # ✅ PREVENT DUPLICATE
                if not Result.objects.filter(
                    file=file_obj,
                    student=student,
                    subject=subject,
                    semester=semester
                ).exists():

                    Result.objects.create(
                        file=file_obj,
                        student=student,
                        subject=subject,
                        marks=marks,
                        semester=semester
                    )

                      # ✅ REFRESH FILE LIST AFTER UPLOAD
            files = UploadFile.objects.all()

            return render(request, 'upload.html', {'success': True})

    else:
        form = UploadFileForm()

    return render(request, 'upload.html',{
                       'form': form,
                       'files': files 
                       })


# 📊 DASHBOARD
@login_required
def dashboard(request):

    file_id = request.GET.get('file')
    semester = request.GET.get('semester')
    batch = request.GET.get('batch')

    results = Result.objects.all()

    # ✅ FILTERS
    if file_id:
        results = results.filter(file_id=file_id)

    if semester:
        results = results.filter(semester=semester)

    if batch:
        results = results.filter(student__batch=batch)

    files = UploadFile.objects.all()

    # ✅ STATS
    total_students = results.count()
    average_marks = results.aggregate(Avg('marks'))['marks__avg'] or 0
    pass_count = results.filter(marks__gte=40).count()
    fail_count = results.filter(marks__lt=40).count()

    # ✅ CHART DATA
    subject_data = results.values('subject__name').annotate(avg_marks=Avg('marks'))
    subjects = [x['subject__name'] for x in subject_data]
    avg_marks = [float(x['avg_marks']) for x in subject_data]

    # 🔥 TOP STUDENTS
    top_students = (
        results.values('student__name')
        .annotate(avg_marks=Avg('marks'))
        .order_by('-avg_marks')[:5]
    )

    # 🔥 WEAK STUDENTS
    bottom_students = (
        results.values('student__name')
        .annotate(avg_marks=Avg('marks'))
        .order_by('avg_marks')[:5]
    )

    return render(request, 'dashboard.html', {
        'total_students': total_students,
        'average_marks': round(average_marks, 2),
        'pass_count': pass_count,
        'fail_count': fail_count,
        'subjects': json.dumps(subjects),
        'avg_marks': json.dumps(avg_marks),
        'files': files,
        'selected_file_id': file_id,

        # 🔥 IMPORTANT
        'top_students': top_students,
        'bottom_students': bottom_students,
    })


# 👨‍🎓 STUDENT HOME (FIXED)
@login_required
def student_home(request):
    if request.user.profile.role != 'student':
        return redirect('login')

    return render(request, 'student_home.html')



# 📂 VIEW CSV DATA
@login_required
def view_uploaded_data(request):

    files = UploadFile.objects.all()
    data = []
    headers = []
    selected_file_id = request.GET.get('file')

    try:
        if selected_file_id:
            selected_file = UploadFile.objects.get(id=selected_file_id)
            file_path = selected_file.file.path

            # Read file safely
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, dtype=str)
            else:
                df = pd.read_csv(file_path,dtype=str)

            # Clean data
            df = df.fillna("")  # replace NaN with empty string

            headers = df.columns.tolist()
            data = df.values.tolist()

    except UploadFile.DoesNotExist:
        headers = []
        data = []
    except Exception as e:
        print("Error loading file:", e)
        headers = []
        data = []

    return render(request, 'view_data.html', {
        'files': files,
        'headers': headers,
        'data': data,
        'selected_file_id': str(selected_file_id) if selected_file_id else ""
    })


# 🎓 STUDENT RESULT


@login_required
def student_result(request):

    roll = request.GET.get('roll')

    student = None
    results = []
    subjects = []
    marks = []

    if roll:
        student = Student.objects.filter(roll_no=roll).first()

        if student:
            results = Result.objects.filter(student=student)

            subjects = [r.subject.name for r in results]
            marks = [int(r.marks) for r in results]

    return render(request, 'student_result.html', {
        'student': student,
        'results': results,
        'subjects': json.dumps(subjects),   # ✅ IMPORTANT
        'marks': json.dumps(marks),         # ✅ IMPORTANT
    })