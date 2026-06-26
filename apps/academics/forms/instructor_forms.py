from django import forms
from ..models import Assessment, MarkEntry


class AssessmentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.course_by_section = kwargs.pop(
            'course_by_section',
            None
        )
        super().__init__(*args, **kwargs)

    class Meta:
        model = Assessment
        fields = [
            'title',
            'assessment_type',
            'total_marks'
        ]

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'w-full border rounded-lg p-3'
                }
            ),
            'assessment_type': forms.Select(
                attrs={
                    'class': 'w-full border rounded-lg p-3'
                }
            ),
            'total_marks': forms.NumberInput(
                attrs={
                    'class': 'w-full border rounded-lg p-3',
                    'min': 1
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data['title'].strip()

        if len(title) < 3:
            raise forms.ValidationError(
                "Assessment title must contain at least 3 characters."
            )

        return title

    def clean_total_marks(self):
        total_marks = self.cleaned_data['total_marks']

        if total_marks <= 0:
            raise forms.ValidationError(
                "Invalid total marks."
            )

        if total_marks > 1000:
            raise forms.ValidationError(
                "Total marks seem unrealistic."
            )

        return total_marks

    def clean(self):
        cleaned_data = super().clean()

        title = cleaned_data.get('title')
        assessment_type = cleaned_data.get(
            'assessment_type'
        )

        if not title or not assessment_type:
            return cleaned_data

        queryset = Assessment.objects.filter(
            course_by_section=self.course_by_section,
            title__iexact=title
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise forms.ValidationError(
                "Assessment title already exists."
            )

        if assessment_type.is_unique:
            existing = Assessment.objects.filter(
                course_by_section=self.course_by_section,
                assessment_type=assessment_type
            )

            if self.instance.pk:
                existing = existing.exclude(
                    pk=self.instance.pk
                )

            if existing.exists():
                raise forms.ValidationError(
                    f"{assessment_type.name} can only be created once."
                )

        return cleaned_data
    
    def save(self, commit=True):
        obj = super().save(commit=False)

        obj.course_by_section = self.course_by_section

        if commit:
            super().save()
        
        return obj
    
class MarkEntryForm(forms.ModelForm):

    class Meta:
        model = MarkEntry
        fields = ['obtained_marks']

        widgets = {
            'obtained_marks': forms.NumberInput(
                attrs={
                    'class': (
                        'w-28 border rounded-lg p-2 '
                        'focus:outline-none '
                        'focus:ring-2 '
                        'focus:ring-indigo-500'
                    ),
                    'step': '0.01',
                    'min': '0'
                }
            )
        }

