import os
from django.core.exceptions import ValidationError


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.csv', '.xes']
    if not ext.lower() in valid_extensions:
        raise ValidationError(f'Unsupported file extension. Supported files are: {", ".join(valid_extensions)}')
