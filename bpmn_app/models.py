from django.db import models

# Create your models here.


class BpmnFile(models.Model):
    file = models.FileField(upload_to='uploads/')

    def __str__(self):
        return self.file.name

    def get_absolute_url(self):
        return reverse('bpmn_model-detail', kwargs={'pk': self.pk})
