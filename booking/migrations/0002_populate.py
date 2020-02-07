# Generated by Django 3.0.3 on 2020-02-07 15:07
from datetime import datetime

from django.db import migrations


def combine_names(apps, _):
    Doctor = apps.get_model('booking', 'Doctor')
    Doctor(
        email='Joey.Tribbiani@gmail.com',
        name='Drake Ramore',
        created_at=datetime.utcnow(),
        specialization='neuroscience',
    ).save()

    Doctor(
        email='Hugh.Laurie@gmail.com',
        name='Dr. Gregory House',
        created_at=datetime.utcnow(),
        specialization='physician',
    ).save()

    Patient = apps.get_model('booking', 'Patient')
    Patient(
        email='johnd@gmail.com',
        name='John Doe',
        created_at=datetime.utcnow(),
    ).save()


class Migration(migrations.Migration):
    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [migrations.RunPython(combine_names)]
