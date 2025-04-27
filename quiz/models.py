# quiz/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import User
from courses.models import Course, Lesson, Module


class Quiz(models.Model):
    """Quiz model containing questions for assessment"""
    QUIZ_TYPES = (
        ('lesson_quiz', _('Lesson Quiz')),
        ('module_quiz', _('Module Quiz')),
        ('final_exam', _('Final Exam')),
        ('practice', _('Practice Quiz')),
    )
    
    title = models.CharField(max_length=255, verbose_name=_("Quiz Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='quizzes',
        verbose_name=_("Course")
    )
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='quizzes',
        null=True, 
        blank=True, 
        verbose_name=_("Module")
    )
    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='quizzes',
        null=True, 
        blank=True, 
        verbose_name=_("Lesson")
    )
    quiz_type = models.CharField(
        max_length=20, 
        choices=QUIZ_TYPES, 
        default='lesson_quiz',
        verbose_name=_("Quiz Type")
    )
    time_limit = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text=_("Time limit in minutes (leave empty for unlimited time)"),
        verbose_name=_("Time Limit")
    )
    passing_score = models.PositiveIntegerField(
        default=70, 
        help_text=_("Minimum percentage to pass"),
        verbose_name=_("Passing Score")
    )
    max_attempts = models.PositiveIntegerField(
        default=3, 
        help_text=_("Maximum number of attempts allowed (0 for unlimited)"),
        verbose_name=_("Maximum Attempts")
    )
    randomize_questions = models.BooleanField(
        default=True, 
        verbose_name=_("Randomize Questions Order")
    )
    show_correct_answers = models.BooleanField(
        default=True, 
        verbose_name=_("Show Correct Answers After Submission")
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name=_("Active")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    
    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")
        ordering = ['course', 'module__order', 'id']
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """Validate that the quiz is associated with the correct objects based on type"""
        super().clean()
        
        if self.quiz_type == 'lesson_quiz' and not self.lesson:
            raise ValidationError(_("Lesson quiz must be associated with a lesson."))
        elif self.quiz_type == 'module_quiz' and not self.module:
            raise ValidationError(_("Module quiz must be associated with a module."))
        elif self.quiz_type == 'final_exam' and (self.module or self.lesson):
            raise ValidationError(_("Final exam should not be associated with a specific module or lesson."))
    
    def get_total_points(self):
        """Calculate total points for this quiz"""
        return sum(question.points for question in self.questions.all())
    
    @property
    def question_count(self):
        """Get the number of questions in this quiz"""
        return self.questions.count()


class Question(models.Model):
    """Question for a quiz"""
    QUESTION_TYPES = (
        ('multiple_choice', _('Multiple Choice')),
        ('true_false', _('True/False')),
        ('short_answer', _('Short Answer')),
        ('essay', _('Essay')),
        ('matching', _('Matching')),
    )
    
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='questions',
        verbose_name=_("Quiz")
    )
    text = models.TextField(verbose_name=_("Question Text"))
    question_type = models.CharField(
        max_length=20, 
        choices=QUESTION_TYPES, 
        default='multiple_choice',
        verbose_name=_("Question Type")
    )
    points = models.PositiveIntegerField(
        default=1, 
        verbose_name=_("Points")
    )
    explanation = models.TextField(
        blank=True, 
        verbose_name=_("Explanation"),
        help_text=_("Explanation shown after question is answered")
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Order")
    )
    
    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['quiz', 'order']
    
    def __str__(self):
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text
    
    def get_correct_answers(self):
        """Get the correct answers for this question"""
        if self.question_type == 'multiple_choice':
            return self.choices.filter(is_correct=True)
        elif self.question_type == 'true_false':
            return self.choices.filter(is_correct=True)
        else:
            return None  # For short_answer and essay, correctness is determined manually


class Choice(models.Model):
    """Answer choice for a multiple choice question"""
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='choices',
        verbose_name=_("Question")
    )
    text = models.CharField(max_length=255, verbose_name=_("Choice Text"))
    is_correct = models.BooleanField(default=False, verbose_name=_("Correct Answer"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    
    class Meta:
        verbose_name = _("Choice")
        verbose_name_plural = _("Choices")
        ordering = ['question', 'order']
    
    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    """Student's attempt at a quiz"""
    STATUS_CHOICES = (
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('timed_out', _('Timed Out')),
    )
    
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='attempts',
        verbose_name=_("Quiz")
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='quiz_attempts',
        verbose_name=_("Student")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='in_progress',
        verbose_name=_("Status")
    )
    score = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name=_("Score")
    )
    percentage = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name=_("Percentage")
    )
    passed = models.BooleanField(
        null=True, 
        blank=True, 
        verbose_name=_("Passed")
    )
    started_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Started At")
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Completed At")
    )
    time_spent = models.DurationField(
        null=True, 
        blank=True, 
        verbose_name=_("Time Spent")
    )
    
    class Meta:
        verbose_name = _("Quiz Attempt")
        verbose_name_plural = _("Quiz Attempts")
        ordering = ['-started_at']
        unique_together = [['quiz', 'student', 'started_at']]
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.started_at})"
    
    def save(self, *args, **kwargs):
        # If attempt is being marked as completed, set completed_at and calculate time_spent
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            self.time_spent = self.completed_at - self.started_at
            
            # Calculate score and percentage
            total_points = self.quiz.get_total_points()
            if total_points > 0:
                self.score = sum(answer.points_earned for answer in self.answers.all())
                self.percentage = (self.score / total_points) * 100
                self.passed = self.percentage >= self.quiz.passing_score
        
        super().save(*args, **kwargs)
    
    def is_timed_out(self):
        """Check if attempt has timed out"""
        if self.quiz.time_limit:
            time_limit = timezone.timedelta(minutes=self.quiz.time_limit)
            elapsed_time = timezone.now() - self.started_at
            return elapsed_time > time_limit
        return False
    
    def mark_timed_out(self):
        """Mark attempt as timed out"""
        self.status = 'timed_out'
        self.completed_at = timezone.now()
        self.time_spent = self.completed_at - self.started_at
        self.save()


class Answer(models.Model):
    """Student's answer to a question"""
    attempt = models.ForeignKey(
        QuizAttempt, 
        on_delete=models.CASCADE, 
        related_name='answers',
        verbose_name=_("Quiz Attempt")
    )
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='student_answers',
        verbose_name=_("Question")
    )
    selected_choices = models.ManyToManyField(
        Choice, 
        blank=True, 
        related_name='selected_in',
        verbose_name=_("Selected Choices")
    )
    text_answer = models.TextField(
        blank=True, 
        verbose_name=_("Text Answer")
    )
    is_correct = models.BooleanField(
        null=True, 
        blank=True, 
        verbose_name=_("Correct")
    )
    points_earned = models.FloatField(
        default=0, 
        verbose_name=_("Points Earned")
    )
    feedback = models.TextField(
        blank=True, 
        verbose_name=_("Instructor Feedback")
    )
    answered_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Answered At")
    )
    
    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        ordering = ['attempt', 'question__order']
        unique_together = [['attempt', 'question']]
    
    def __str__(self):
        return f"Answer to {self.question} by {self.attempt.student.username}"
    
    def evaluate_correctness(self):
        """Evaluate if answer is correct and calculate points earned"""
        question = self.question
        
        if question.question_type == 'multiple_choice':
            # For multiple choice, check if selected choices match correct choices
            correct_choices = set(question.choices.filter(is_correct=True).values_list('id', flat=True))
            selected_choices = set(self.selected_choices.values_list('id', flat=True))
            
            # If question allows multiple correct answers
            if len(correct_choices) > 1:
                # Partial credit: points based on correct selections minus incorrect ones
                correct_selections = len(correct_choices.intersection(selected_choices))
                incorrect_selections = len(selected_choices - correct_choices)
                
                # Calculate points with penalty for incorrect selections
                max_points = question.points
                points_per_correct = max_points / len(correct_choices)
                penalty_per_incorrect = points_per_correct
                
                self.points_earned = max(0, points_per_correct * correct_selections - 
                                        penalty_per_incorrect * incorrect_selections)
                
                # Is correct if all correct choices selected and no incorrect ones
                self.is_correct = (correct_choices == selected_choices)
            else:
                # Single correct answer: all or nothing
                self.is_correct = (correct_choices == selected_choices)
                self.points_earned = question.points if self.is_correct else 0
                
        elif question.question_type == 'true_false':
            # True/False is essentially multiple choice with two options
            correct_choice = question.choices.filter(is_correct=True).first()
            selected_choice = self.selected_choices.first()
            
            self.is_correct = (selected_choice == correct_choice)
            self.points_earned = question.points if self.is_correct else 0
            
        elif question.question_type in ['short_answer', 'essay', 'matching']:
            # These require manual grading - leave as None until instructor reviews
            self.is_correct = None
            self.points_earned = 0
        
        self.save()