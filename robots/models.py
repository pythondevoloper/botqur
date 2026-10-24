from django.db import models
from django.contrib.auth.models import User

class Competition(models.Model):
    slug = models.SlugField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    format_label = models.CharField(max_length=200)
    age_range = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Competition"
        verbose_name_plural = "Competitions"

    def __str__(self):
        return self.name

class RobotKit(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='kits')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    price_uzs = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='images_kits/' , null=True, blank=True)

    class Meta:
        verbose_name = "Robot Kit"
        verbose_name_plural = "Robot Kits"

    def __str__(self):
        return self.name

class KitComponent(models.Model):
    kit = models.ForeignKey(RobotKit, on_delete=models.CASCADE, related_name='components')
    label = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Kit Component"
        verbose_name_plural = "Kit Components"

    def __str__(self):
        return self.label

class KitVideo(models.Model):
    kit = models.ForeignKey(RobotKit, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    video_url = models.URLField(max_length=500)
    duration_seconds = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Kit Video"
        verbose_name_plural = "Kit Videos"

    def __str__(self):
        return self.title

class Lead(models.Model):
    kit = models.ForeignKey(RobotKit, on_delete=models.SET_NULL, null=True, blank=True)
    competition = models.ForeignKey(Competition, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default='new')
    source = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return self.full_name

class AuditLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=200)
    action = models.CharField(max_length=100)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.table_name} - {self.action}"

class SiteSetting(models.Model):
    settings_key = models.CharField(max_length=200, unique=True)
    settings_value = models.TextField()
    value_type = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.settings_key

class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question

class Event(models.Model):
    name = models.CharField(max_length=200)
    frequency_label = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    organizer = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return self.name