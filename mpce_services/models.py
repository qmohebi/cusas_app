from django.db import models


class MPCESections(models.Model):
    section = models.CharField(max_length=250)
    service_provided = models.TextField()
    url = models.CharField(max_length=250)
    image = models.ImageField(upload_to="images")
    opening_hours = models.TimeField(null=True, blank=True)
    closing_hours = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.section
