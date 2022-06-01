from django import forms
from .validators import validate_file_extension
from .models import BpmnFile


class ModelFormWithFileField(forms.ModelForm):
    file = forms.FileField(validators=[validate_file_extension],
                           widget=forms.FileInput(attrs={'class': 'form-control', 'type': 'file'}))

    class Meta:
        model = BpmnFile
        fields = ['file']


class ModelCsvHeaderForm(forms.ModelForm):
    class Meta:
        model = BpmnFile
        fields = ['first_header_dropdown', 'second_header_dropdown', 'third_header_dropdown']
