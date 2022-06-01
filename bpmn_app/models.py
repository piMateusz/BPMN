from django.db import models

# Create your models here.


class BpmnFile(models.Model):
    header_choices = (
        ("Case ID", "Case ID"),
        ("Start Timestamp", "Start Timestamp"),
        ("Activity", "Activity")
    )
    file = models.FileField(upload_to='uploads/')
    first_header_dropdown = models.CharField(max_length=15, choices=header_choices, default="Case ID", blank=True)
    second_header_dropdown = models.CharField(max_length=15, choices=header_choices, default="Start Timestamp", blank=True)
    third_header_dropdown = models.CharField(max_length=15, choices=header_choices, default="Activity", blank=True)

    def __str__(self):
        return self.file.name

    def get_absolute_url(self):
        return reverse('bpmn_model-detail', kwargs={'pk': self.pk})
