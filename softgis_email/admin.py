from django.contrib import admin
from softgis_email.models import EmailAddress, EmailConfirmation

admin.site.register(EmailAddress)
admin.site.register(EmailConfirmation)
