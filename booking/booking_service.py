import abc
import json
from datetime import datetime

import typing

from django.db.models import Q

from booking.range import VisitTime, HoursRange, Range
from booking.models import Appointment


class BookingService:

    @staticmethod
    def get_appointments_for_range(user_id, from_date: datetime.date, to_date: datetime.date):
        return Appointment.objects.filter(
            patient=user_id,
            appointment_start__range=[from_date, to_date]
        )

    @staticmethod
    def appointments_fall_in_range(user_id, doctor_id, visit: VisitTime):
        from_date, to_date = visit.start, visit.end
        return Appointment.objects.filter(
            (Q(patient_id=user_id) | Q(doctor_id=doctor_id)) & (
                    Q(appointment_start__lte=to_date) & Q(appointment_finish__gte=from_date)
            )
        )

    @staticmethod
    def check_appointment_time_availability(user_id, doctor_id, visit_time: VisitTime):
        return filter(visit_time, user_id, doctor_id)


class AvailabilityFilter(abc.ABC):
    @abc.abstractmethod
    def __call__(self, visit: VisitTime, user_id, doctor_id) -> (bool, typing.List[str]):
        """
        General filter returns availability for a specified time of visit
        :return: tuple (availability, [explanations])
        """
        return NotImplementedError


class CompositeAvailabilityFilter(AvailabilityFilter):
    def __init__(self, filters):
        self._filters = filters

    def __call__(self, visit: VisitTime, user_id, doctor_id) -> (bool, typing.List[str]):
        reasons = [x[1] for x in (f(visit, user_id, doctor_id) for f in self._filters) if not x[0]]
        return not len(reasons), [item for sublist in reasons for item in sublist]


class WorkingDayAndHourAvailabilityFilter(AvailabilityFilter):
    def __call__(self, visit: VisitTime, user_id, doctor_id) -> (bool, typing.List[str]):
        """Check if appointment could be made due to hospital working hours"""
        week_day = visit.start.weekday()  # Monday == 0 ... Sunday == 6

        if not (0 <= week_day < 5):
            return False, ["Booking couldn't be made on the weekend."]

        hours_range = self.get_working_hours_range(visit.start)

        matches_range = hours_range(visit.start) and hours_range(visit.end)
        is_valid = matches_range and week_day == visit.end.weekday(), ["Close hours."]
        return is_valid

    def get_working_hours_range(self, _: datetime) -> Range:
        """Lookup schedule and retrieve working hours for a specific date"""
        return HoursRange(9, 18)


class SlotAvailabilityFilter(AvailabilityFilter):
    """Checking the slot availability"""

    def __call__(self, visit: VisitTime, user_id, doctor_id) -> (bool, typing.List[str]):
        conflicting_appointments = BookingService.appointments_fall_in_range(user_id, doctor_id, visit)
        return not len(conflicting_appointments), ["Time slot already taken."]


filter = CompositeAvailabilityFilter([WorkingDayAndHourAvailabilityFilter(), SlotAvailabilityFilter()])
