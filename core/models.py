from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# ==========================================
# 1. CUSTOM USER MANAGER
# ==========================================
class CustomUserManager(BaseUserManager):
    def create_user(self, id_number, password=None, **extra_fields):
        if not id_number:
            raise ValueError('The ID Number field must be set')
        
        user = self.model(id_number=id_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, id_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(id_number, password, **extra_fields)


# ==========================================
# 2. CUSTOM USER MODEL
# ==========================================
class User(AbstractUser):
    username = None 
    id_number = models.CharField(max_length=50, unique=True)
    
    # Role flags
    is_instructor = models.BooleanField(default=False)
    
    department = models.CharField(max_length=150, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    USERNAME_FIELD = 'id_number'
    REQUIRED_FIELDS = []

    # LINK THE CUSTOM MANAGER HERE:
    objects = CustomUserManager()

    def __str__(self):
        # Fallback in case first/last name aren't set yet
        name = f"{self.first_name} {self.last_name}".strip()
        return f"{name} ({self.id_number})" if name else self.id_number
    
  # ==========================================
# 3. SECTIONS AND STUDENTS
# ==========================================
class Section(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sections')
    
    # New custom fields for cross-department teaching
    subject = models.CharField(max_length=150, default="General Subject") # e.g., "Purposive Communication"
    program = models.CharField(max_length=100, default="General")         # e.g., "BSIT"
    year_level = models.CharField(max_length=50, default="1st Year")      # e.g., "3rd Year"
    name = models.CharField(max_length=50)                                # e.g., "A" or "3A"
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.program} {self.year_level} Sec {self.name}"

class Student(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=200)
    student_id = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

 # ==========================================
# 4. ASSESSMENTS & GRADING
# ==========================================
class Assessment(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Active', 'Active'),
        ('Completed', 'Completed')
    ]
    
    TYPE_CHOICES = [
        ('Essay', 'Essay'),
        ('Coding', 'Coding'),
        ('Multiple Choice', 'Multiple Choice'),
        ('Identification', 'Identification'),
        ('Enumeration', 'Enumeration'),
        ('True or False', 'True or False'),
    ]
    
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=200)
    
    # The Assessment Type
    assessment_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Essay')
    
    rubric = models.TextField(help_text="Paste the grading rubric or instructions for the AI here.")
    max_score = models.IntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.section.name}) - {self.assessment_type}"

# ==========================================
# 4.5 ADVANCED EXAM STRUCTURE
# ==========================================
class AssessmentSection(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='exam_sections')
    title = models.CharField(max_length=200) # e.g., "Section A: Multiple Choice"
    section_type = models.CharField(max_length=50, choices=Assessment.TYPE_CHOICES)
    points_per_item = models.FloatField(default=1.0)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.assessment.title} - {self.title}"

class Question(models.Model):
    section = models.ForeignKey(AssessmentSection, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField() # The actual question
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"Q: {self.text[:50]}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200) # e.g., "A. The Mitochondria"
    is_correct = models.BooleanField(default=False) # The Answer Key!

    def __str__(self):
        return self.text

# ==========================================
# 5. SUBMISSIONS
# ==========================================
class Submission(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    
    # The scanned paper image
    scanned_image = models.ImageField(upload_to='scans/', blank=True, null=True)
    # The text extracted via OCR
    extracted_text = models.TextField(blank=True, null=True)
    
    # Grading results
    score = models.FloatField(null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(null=True, blank=True)
    
    graded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.assessment.title}"
    
# THIS IS THE MISSING MODEL!
class Submission(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    
    # The scanned paper image
    scanned_image = models.ImageField(upload_to='scans/', blank=True, null=True)
    # The text extracted via OCR
    extracted_text = models.TextField(blank=True, null=True)
    
    # Grading results
    score = models.FloatField(null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(null=True, blank=True)
    
    graded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.assessment.title}"