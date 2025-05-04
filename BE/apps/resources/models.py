from django.db import models

# Create your models here.
class StudySpace(models.Model):
    capacity = models.IntegerField()
    space_type = models.CharField(
        max_length=20,
        choices= ["INDIVIDUAL", "GROUP", "MENTORING"],
        default= "INDIVIDUAL"
    )
    space_status = models.CharField(
        max_length=20,
        choices= ["EMPTY", "BOOKED", "INUSE"],
        default= "EMPTY"
    )

    def __str__(self):
        return f"{self.capacity} - {self.space_type} - {self.space_status}"
