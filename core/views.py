from .models import User, Section, Student, Assessment, Submission, AssessmentSection, Question, Choice
import csv
import io
import json
import pytesseract
from PIL import Image
import google.generativeai as genai

import base64
import io
from django.core.files.base import ContentFile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .forms import InstructorRegistrationForm, InstructorProfileForm
from .models import User, Section, Student, Assessment, Submission

# Configure Tesseract path for Zorin OS / Linux
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# ==========================================
# 1. LOGIN LOGIC
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_instructor:
            return redirect('instructor_dashboard')

    if request.method == 'POST':
        id_number = request.POST.get('id_number')
        password = request.POST.get('password')
        
        user = authenticate(request, id_number=id_number, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.is_instructor:
                return redirect('instructor_dashboard')
        else:
            messages.error(request, "Invalid ID Number or Password.")
            
    return render(request, 'login.html')

# ==========================================
# 2. INSTRUCTOR DASHBOARD
# ==========================================
@login_required
def instructor_dashboard(request):
    return render(request, 'instructor_dashboard.html')


# ==========================================
# 3. ADMIN DASHBOARD & REGISTRATION
# ==========================================
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_instructor = True 
            user.save()
            messages.success(request, f"Instructor {user.first_name} {user.last_name} registered successfully!")
            return redirect('admin_dashboard')
    else:
        form = InstructorRegistrationForm()

    instructors = User.objects.filter(is_instructor=True)
    
    context = {
        'form': form,
        'instructors': instructors
    }
    return render(request, 'admin_dashboard.html', context)


# ==========================================
# 4. INSTRUCTOR SETTINGS / PROFILE
# ==========================================
@login_required
def instructor_settings(request):
    if request.method == 'POST':
        # request.FILES handles the profile picture upload
        form = InstructorProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('instructor_settings')
    else:
        # Pre-fill the form with the logged-in user's data
        form = InstructorProfileForm(instance=request.user)

    return render(request, 'settings.html', {'form': form})

# ==========================================
# 5. LOGOUT LOGIC
# ==========================================
def logout_user(request):
    logout(request) # This destroys the user's session safely
    return redirect('login') # Sends them right back to the login screen

# ==========================================
# 6. INSTRUCTOR SECTIONS
# ==========================================
@login_required
def instructor_sections(request):
    # Handle the form submission when they add a new section
    if request.method == 'POST':
        subject = request.POST.get('subject')
        program = request.POST.get('program')
        year_level = request.POST.get('year_level')
        name = request.POST.get('name')
        
        # Create and save the new section linked to this instructor
        Section.objects.create(
            instructor=request.user,
            subject=subject,
            program=program,
            year_level=year_level,
            name=name
        )
        messages.success(request, f"Successfully added {program} {year_level} - Section {name}!")
        return redirect('instructor_sections')

    # Get all sections to display on the page
    sections = Section.objects.filter(instructor=request.user).order_by('-created_at')
    return render(request, 'sections.html', {'sections': sections})

# ==========================================
# 7. VIEW SECTION LIST & SYNC CSV
# ==========================================
@login_required
def section_detail(request, section_id):
    # Fetch the specific section, making sure it belongs to this instructor
    section = get_object_or_404(Section, id=section_id, instructor=request.user)
    # Get all students in this section, ordered alphabetically
    students = section.students.all().order_by('name')
    
    return render(request, 'section_detail.html', {
        'section': section,
        'students': students
    })

@login_required
def sync_students_csv(request, section_id):
    section = get_object_or_404(Section, id=section_id, instructor=request.user)
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid .csv file.')
            return redirect('section_detail', section_id=section.id)
        
        # Read the file
        dataset = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(dataset)
        
        # Skip the header row (assumes row 1 is "ID Number, Name")
        next(io_string) 
        
        count = 0
        for row in csv.reader(io_string, delimiter=',', quotechar="|"):
            # Ensure the row has at least 2 columns (ID and Name)
            if len(row) >= 2:
                student_id = row[0].strip()
                name = row[1].strip()
                
                if student_id and name:
                    # update_or_create prevents duplicate students!
                    Student.objects.update_or_create(
                        section=section,
                        student_id=student_id,
                        defaults={'name': name}
                    )
                    count += 1
                    
        messages.success(request, f'Successfully synced {count} students!')
        
    return redirect('section_detail', section_id=section.id)

# ==========================================
# 8. ASSESSMENTS & TOGGLE STATUS
# ==========================================
@login_required
def instructor_assessments(request):
    # Handle the form submission for creating a new Assessment
    if request.method == 'POST':
        title = request.POST.get('title')
        section_id = request.POST.get('section_id')
        rubric = request.POST.get('rubric')
        max_score = request.POST.get('max_score')
        
        # Verify the section belongs to this instructor
        section = get_object_or_404(Section, id=section_id, instructor=request.user)
        
        Assessment.objects.create(
            section=section,
            title=title,
            rubric=rubric,
            max_score=max_score
        )
        messages.success(request, f"Assessment '{title}' created successfully!")
        return redirect('instructor_assessments')

    # Get data for the page: the instructor's sections (for the dropdown form) and all assessments
    sections = Section.objects.filter(instructor=request.user)
    assessments = Assessment.objects.filter(section__instructor=request.user).order_by('-created_at')
    
    return render(request, 'assessments.html', {
        'sections': sections,
        'assessments': assessments
    })

@login_required
def toggle_assessment_status(request, assessment_id):
    # Fetch the assessment and ensure the instructor owns it
    assessment = get_object_or_404(Assessment, id=assessment_id, section__instructor=request.user)
    
    # Flip the status
    if assessment.status == 'Draft':
        assessment.status = 'Active'
        messages.success(request, f"'{assessment.title}' is now Active!")
    else:
        assessment.status = 'Draft'
        messages.warning(request, f"'{assessment.title}' moved back to Draft.")
        
    assessment.save()
    return redirect('instructor_assessments')

# ==========================================
# 9. PRINT ASSESSMENT VIEW
# ==========================================
@login_required
def print_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id, section__instructor=request.user)
    return render(request, 'print_assessment.html', {'assessment': assessment})


# ==========================================
# 10. AI GRADING DASHBOARD & VISION SCANNER
# ==========================================
@login_required
def grade_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id, section__instructor=request.user)
    students = assessment.section.students.all().order_by('name')
    graded_submissions = Submission.objects.filter(assessment=assessment).order_by('-graded_at')

    if request.method == 'POST':
        scanned_file = request.FILES.get('scanned_image')
        camera_data = request.POST.get('camera_image_data')
        
        # 1. LOAD THE IMAGE INTO MEMORY FIRST
        if camera_data:
            format, imgstr = camera_data.split(';base64,')
            img_data = base64.b64decode(imgstr)
            img = Image.open(io.BytesIO(img_data))
            file_to_save = ContentFile(img_data, name=f"scan_temp.jpg")
        elif scanned_file:
            img = Image.open(scanned_file)
            file_to_save = scanned_file
        else:
            messages.error(request, "No image provided. Please snap a photo or upload a file.")
            return redirect('grade_assessment', assessment_id=assessment.id)
            
        try:
            # 2. GENERATE THE MASTER ANSWER KEY AND ROSTER
            answer_key_prompt = f"Assessment Type: {assessment.assessment_type}\nMax Score: {assessment.max_score}\n\n"
            for section in assessment.exam_sections.all():
                answer_key_prompt += f"--- {section.title} ({section.section_type}) ---\n"
                for q in section.questions.all().order_by('order'):
                    if section.section_type == 'Multiple Choice':
                        correct = q.choices.filter(is_correct=True).first()
                        answer_key_prompt += f"Question: {q.text}\nCorrect Bubble: {correct.text if correct else 'N/A'}\n"
                    elif section.section_type == 'Identification':
                        correct = q.choices.filter(is_correct=True).first()
                        answer_key_prompt += f"Question: {q.text}\nCorrect Answer: {correct.text if correct else 'N/A'}\n"
                    else:
                        answer_key_prompt += f"Essay Prompt: {q.text}\nGrading Rubric: {assessment.rubric}\n"

            # Create a string of all students in this section so the AI can match them
            roster_str = ", ".join([f"ID: {s.student_id} (Name: {s.name})" for s in students])

            # 3. THE VISION AI PROMPT
            genai.configure(api_key="AIzaSyAB66-Ls5x0-Bd8jmHGbwS_XNl_NFX9KDg") # <--- PASTE YOUR KEY AGAIN!
            ai_model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            You are an Optical Mark Recognition (OMR) and Handwriting Analysis system.
            
            YOUR TASKS:
            1. Look at the top of the paper to read the student's handwritten Name and ID.
            2. Match their handwriting against this official class roster: [{roster_str}]. Find the exact ID.
            3. Grade the rest of the paper using this MASTER ANSWER KEY:
            {answer_key_prompt}
            
            Format your exact response like this:
            STUDENT_ID: [insert only the numeric ID from the roster here]
            SCORE: [numeric score]
            FEEDBACK: [Brief summary of what they got right/wrong based on visual evidence.]
            """
            
            # Send the image and prompt to Gemini
            ai_response = ai_model.generate_content([prompt, img]).text
            
            # Parse the AI's response safely
            try:
                extracted_id = next(line for line in ai_response.split('\n') if line.startswith('STUDENT_ID:')).replace('STUDENT_ID:', '').strip()
                score_line = next(line for line in ai_response.split('\n') if line.startswith('SCORE:')).replace('SCORE:', '').strip()
                feedback_line = next(line for line in ai_response.split('\n') if line.startswith('FEEDBACK:')).replace('FEEDBACK:', '').strip()
            except Exception:
                messages.error(request, "The AI could not format the output correctly. Ensure the image is clear.")
                return redirect('grade_assessment', assessment_id=assessment.id)

            # 4. FIND THE STUDENT AND SAVE THE GRADE
            student = students.filter(student_id=extracted_id).first()
            
            if student:
                # We found them! Create/Update their submission
                submission, created = Submission.objects.update_or_create(assessment=assessment, student=student)
                submission.scanned_image = file_to_save
                submission.score = float(score_line)
                submission.percentage = (submission.score / assessment.max_score) * 100
                submission.ai_feedback = feedback_line
                submission.save()
                
                messages.success(request, f"Successfully identified and graded {student.name}'s paper!")
            else:
                messages.error(request, f"Could not match handwriting to the roster. The AI read ID: {extracted_id}")

        except Exception as e:
            messages.error(request, f"AI Grading Error: {str(e)}")

        return redirect('grade_assessment', assessment_id=assessment.id)

    return render(request, 'grade_assessment.html', {
        'assessment': assessment,
        'students': students,
        'graded_submissions': graded_submissions
    })

# ==========================================
# 11. ADVANCED EXAM BUILDER
# ==========================================
@login_required
def build_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id, section__instructor=request.user)
    
    if request.method == 'POST':
        exam_data_str = request.POST.get('exam_data')
        
        if exam_data_str:
            import json
            exam_data = json.loads(exam_data_str)
            
            # Delete old sections so we don't create duplicates when editing
            assessment.exam_sections.all().delete()
            
            # Loop through the JSON and save everything to the database
            for sec_idx, sec in enumerate(exam_data):
                new_section = AssessmentSection.objects.create(
                    assessment=assessment,
                    title=sec['title'],
                    section_type=sec['type'],
                    order=sec_idx
                )
                
                # Save each question AND its choices/answers!
                for q_idx, q_data in enumerate(sec['questions']):
                    new_q = Question.objects.create(
                        section=new_section,
                        text=q_data['text'],
                        order=q_idx
                    )
                    
                    # Save the choices and the answer key
                    for choice in q_data['choices']:
                        if choice['text'].strip(): # Make sure it isn't blank
                            Choice.objects.create(
                                question=new_q,
                                text=choice['text'],
                                is_correct=choice['is_correct']
                            )
            
            messages.success(request, f"Successfully built and saved the exam structure for {assessment.title}!")
            return redirect('instructor_assessments')

    return render(request, 'build_assessment.html', {'assessment': assessment})