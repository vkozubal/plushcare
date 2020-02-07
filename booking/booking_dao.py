import datetime

from booking.models import Appointment
from django.db.models import Q


class BookingDAO:
    @staticmethod
    def get_appointments_for_range(user_id, from_date: datetime.date, to_date: datetime.date):
        return Appointment.objects.filter(
            patient=user_id,
            appointment_start__range=[from_date, to_date]
        )

    @staticmethod
    def appointments_fall_in_range(from_date: datetime.date, to_date: datetime.date, user_id):
        return Appointment.objects.filter(
            Q(patient=user_id) & (
                    Q(appointment_start__range=[from_date, to_date]) | Q(appointment_finish__range=[from_date, to_date])
            )
        )
