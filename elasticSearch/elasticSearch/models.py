from django.db import models

class Dummy(models.Model) :
    message = models.CharField(max_length=128, null=True)
    sent_on = models.DateTimeField(auto_now_add=True)

