
from django.contrib import admin
from .models import Student, Subject, Result, Profile, UploadFile

admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(Result)
admin.site.register(Profile)
admin.site.register(UploadFile)