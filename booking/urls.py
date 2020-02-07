from datetime import datetime

from django.urls import path, register_converter

from . import views


class DateConverter:
    regex = '[0-9]{8}'
    DATE_FORMAT = '%Y%m%d'

    def to_python(self, value):
        return datetime.strptime(value, self.DATE_FORMAT).date()

    def to_url(self, value):
        return value.strftime(self.DATE_FORMAT)


register_converter(DateConverter, 'day')

urlpatterns = [
    path('appointments/dates/<day:for_date>', views.list_appointments, name='perday'),
    path('appointments/', views.book_appointment, name='bookings'),
]
