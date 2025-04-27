# enrollment/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Enrollment


class EnrollmentForm(forms.ModelForm):
    """Form for enrolling in a course"""
    
    agree_terms = forms.BooleanField(
        required=True,
        label=_("I agree to follow the course guidelines and code of conduct"),
        widget=forms.CheckboxInput(
            attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600'
            }
        )
    )
    
    class Meta:
        model = Enrollment
        fields = []  # We don't need any fields from the model since we'll create it in the view
    

class StudentFilterForm(forms.Form):
    """Form for filtering students on the course students list"""
    
    status = forms.ChoiceField(
        required=False,
        choices=(
            ('', _('All Status')),
            ('active', _('Active')),
            ('completed', _('Completed')),
            ('dropped', _('Dropped')),
            ('pending', _('Pending')),
        ),
        widget=forms.Select(
            attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'
            }
        )
    )
    
    progress_min = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        label=_("Minimum Progress"),
        widget=forms.NumberInput(
            attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'
            }
        )
    )
    
    progress_max = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        label=_("Maximum Progress"),
        widget=forms.NumberInput(
            attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'
            }
        )
    )
    
    search = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Search by name or email'),
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'
            }
        )
    )