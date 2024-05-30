from django import forms
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class my_connector(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(default = 'mysql')
    username = models.CharField(max_length=100)
    host = models.GenericIPAddressField()
    password = models.CharField(max_length=100)


class PostgresConnector(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(default = 'PostgreSQL')
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    host = models.CharField(max_length=100)
    port = models.IntegerField(default=5432)
    database_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.service_name} Connector for {self.user.username}"

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')

    def __str__(self):
        return self.file_name