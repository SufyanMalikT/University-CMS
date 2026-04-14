from django import forms
from .models import CustomUser
from ..academics.models import Department
class StudentRegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password','class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label='Select a Department'
    )
    class Meta:
        model = CustomUser
        fields = ['username','email','first_name','last_name','phone','birth_date','department','password']
        widgets = {
            'password':forms.PasswordInput(attrs={'placeholder':'Password','class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
            'birth_date':forms.DateInput(attrs={'placeholder':'YYYY-MM-DD','class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
            'username':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
            'email':forms.EmailInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
            'department':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
            'first_name':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
            'last_name':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
            'phone':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md focus:outline-none transition focus:bg-gray-300'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords donot match!!!")
        return cleaned_data
    
    
class InstructorRegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password','class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'})
    )
    class Meta:
        model = CustomUser
        fields = ['username','email','first_name','last_name','phone','birth_date','password']
        widgets = {
            'password':forms.PasswordInput(attrs={'placeholder':'Password','class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'}),
            'birth_date':forms.DateInput(attrs={'placeholder':'YYYY-MM-DD','class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'}),
            'username':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'}),
            'email':forms.EmailInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'}),
            'first_name':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'}),
            'last_name':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'}),
            'phone':forms.TextInput(attrs={'class':'border border-gray-300 shadow py-1 px-2 w-md rounded-md'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords donot match!!!")
        return cleaned_data
