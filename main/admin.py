from django.contrib import admin
from .models import Profile, Task, AuditLog

admin.site.register(Profile)
admin.site.register(Task)
admin.site.register(AuditLog)