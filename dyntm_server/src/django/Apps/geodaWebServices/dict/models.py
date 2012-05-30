from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Dictionary_Entry(models.Model):
    user = models.ForeignKey(User)
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=500)
    class Meta:
        unique_together = ("user","key")
