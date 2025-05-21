from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select file to upload')
    encryption_password = forms.CharField(
        label='Encryption password',
        widget=forms.PasswordInput,
        min_length=8
    )
    confirm_password = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput,
        min_length=8
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('encryption_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data