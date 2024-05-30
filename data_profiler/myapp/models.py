from django.db import models

# Create your models here.

class User(models.Model):
	user_name = models.CharField(max_length=70)
	user_email = models.CharField(max_length=100)

