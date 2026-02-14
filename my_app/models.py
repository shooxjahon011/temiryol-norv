from django.db import models
from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    full_name = models.CharField(max_length=255)
    login = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    tabel_raqami = models.CharField(max_length=50)
    razryad = models.CharField(max_length=10, blank=True, null=True)
    oklad = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    activation_code = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    def __str__(self):
        return f"{self.full_name} ({self.tabel_raqami})"

from django.db import models
from django.contrib.auth.models import User


from django.db import models

class ChatMessage(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    video = models.FileField(upload_to='chat_videos/', blank=True, null=True)
    voice = models.FileField(upload_to='chat_voices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.login}: {self.text[:20]}"

class WorkSchedule(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField()
    oklad = models.FloatField(default=0)
    norma_soati = models.FloatField(default=0)
    ishlagan_soati = models.FloatField(default=0)
    tungi_soati = models.FloatField(default=0)
    bayram_soati = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # BU YERNI TO'G'IRLANG: .text[:20] ni olib tashlang
        return f"{self.user.login} - {self.date}"