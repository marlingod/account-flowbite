# quiz/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Quiz, Question, Choice, QuizAttempt, Answer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3
    fields = ('text', 'is_correct', 'order')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ('text', 'question_type', 'points', 'explanation', 'order')


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'text_answer', 'is_correct', 'points_earned', 'answered_at')
    fields = ('question', 'text_answer', 'is_correct', 'points_earned', 'feedback', 'answered_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'module', 'quiz_type', 'question_count', 
                   'passing_score', 'max_attempts', 'is_active')
    list_filter = ('quiz_type', 'is_active', 'course', 'passing_score')
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuestionInline]
    
    actions = ['activate_quizzes', 'deactivate_quizzes']
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = _("Questions")
    
    def activate_quizzes(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, _(f"{queryset.count()} quizzes were successfully activated."))
    activate_quizzes.short_description = _("Activate selected quizzes")
    
    def deactivate_quizzes(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, _(f"{queryset.count()} quizzes were successfully deactivated."))
    deactivate_quizzes.short_description = _("Deactivate selected quizzes")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('get_short_text', 'quiz', 'question_type', 'points', 'order')
    list_filter = ('question_type', 'quiz__title')
    search_fields = ('text', 'quiz__title')
    inlines = [ChoiceInline]
    
    def get_short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    get_short_text.short_description = _("Question")


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')
    list_filter = ('is_correct', 'question__quiz')
    search_fields = ('text', 'question__text')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'student', 'status', 'score', 'percentage', 'passed', 
                   'started_at', 'completed_at', 'time_spent')
    list_filter = ('status', 'passed', 'quiz__title')
    search_fields = ('student__username', 'student__email', 'quiz__title')
    date_hierarchy = 'started_at'
    readonly_fields = ('quiz', 'student', 'started_at', 'completed_at', 'time_spent')
    inlines = [AnswerInline]
    
    actions = ['mark_as_completed', 'reset_attempts']
    
    def mark_as_completed(self, request, queryset):
        for attempt in queryset.filter(status='in_progress'):
            attempt.status = 'completed'
            attempt.save()
        self.message_user(request, _(f"Selected in-progress attempts were marked as completed."))
    mark_as_completed.short_description = _("Mark selected attempts as completed")
    
    def reset_attempts(self, request, queryset):
        # Only allow resetting attempts that aren't completed
        if queryset.filter(status='completed').exists():
            self.message_user(request, _("Cannot reset completed attempts."), level='error')
            return
        
        # Delete answers and the attempts
        for attempt in queryset:
            attempt.answers.all().delete()
            attempt.delete()
            
        self.message_user(request, _(f"Selected attempts were reset."))
    reset_attempts.short_description = _("Reset selected attempts")
    
    def has_add_permission(self, request):
        return False


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'get_student', 'get_quiz', 'is_correct', 'points_earned', 
                   'answered_at')
    list_filter = ('is_correct', 'question__quiz', 'attempt__status')
    search_fields = ('text_answer', 'feedback', 'attempt__student__username', 
                    'attempt__quiz__title', 'question__text')
    readonly_fields = ('attempt', 'question', 'selected_choices', 'text_answer', 
                      'answered_at')
    
    def get_student(self, obj):
        return obj.attempt.student.username
    get_student.short_description = _("Student")
    get_student.admin_order_field = 'attempt__student__username'
    
    def get_quiz(self, obj):
        return obj.attempt.quiz.title
    get_quiz.short_description = _("Quiz")
    get_quiz.admin_order_field = 'attempt__quiz__title'
    
    def has_add_permission(self, request):
        return False