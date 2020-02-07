from django.db import models
from django.db.models import PROTECT, CASCADE


class Doctor(models.Model):
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=300)
    specialization = models.CharField(max_length=300)

    def __str__(self):
        return f'{self.name} <{self.created_at.isoformat()}>'

    class Meta:
        ordering = ['created_at']


class Patient(models.Model):
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=300)

    def __str__(self):
        return f'{self.name} <{self.created_at.isoformat()}>'

    class Meta:
        ordering = ['created_at']


class Appointment(models.Model):
    """
    Implements many to many relationship between Doctor and Patient models
    """

    class AppointmentStatus(models.TextChoices):
        OPEN = 'OPEN'
        CANCELLED = 'CANCELLED'
        USED = 'USED'
        NO_SHOW = 'NO_SHOW'

    doctor = models.ForeignKey(Doctor, on_delete=PROTECT)
    patient = models.ForeignKey(Patient, on_delete=CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    appointment_start = models.DateTimeField()
    appointment_finish = models.DateTimeField()

    status = models.CharField(
        max_length=100,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.OPEN,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f'{self.id} {self.doctor.name}-{self.patient.name} ({self.status.capitalize()}) <{self.created_at.isoformat()}>'
