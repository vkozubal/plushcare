import abc
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
    def appointments_fall_in_range(user_id, visit: VisitTime):
        from_date, to_date = visit.start, visit.end
        return Appointment.objects.filter(
            Q(patient=user_id) & (
                    Q(appointment_start__range=[from_date, to_date]) | Q(appointment_finish__range=[from_date, to_date])
            )
        )

    @staticmethod
    def check_appointment_time_availability(user_id, visit_time: VisitTime):
        doctor_availability, reasons = doctor_availability_filter(visit_time, user_id)
        if not doctor_availability:  # doctor isn't available for the specified visit time
            return False, reasons

        patient_available, reasons = patient_availability_filter(visit_time, user_id)
        if not patient_available:  # patient isn't available for the specified visit time
            return False, reasons

        return True, []


class AvailabilityFilter(abc.ABC):
    @abc.abstractmethod
    def __call__(self, visit: VisitTime, user_id) -> (bool, typing.List[str]):
        """
        General filter returns availability for a specified time of visit
        :return: tuple (availability, [explanations])
        """
        return NotImplementedError


class CompositeAvailabilityFilter(AvailabilityFilter):
    def __init__(self, filters):
        self._filters = filters

    def __call__(self, visit: VisitTime, user_id) -> (bool, typing.List[str]):
        reasons = [x[1] for x in (f(visit, user_id) for f in self._filters) if not x[0]]
        return not len(reasons), [item for sublist in reasons for item in sublist]


class WorkingDayAndHourAvailabilityFilter(AvailabilityFilter):
    def __call__(self, visit: VisitTime, user_id) -> (bool, typing.List[str]):
        """Check if appointment could be made due to hospital working hours"""
        week_day = visit.start.weekday()  # Monday == 0 ... Sunday == 6

        if not (0 <= week_day < 5):
            return False, ["Booking couldn't be made on the weekend."]

        hours_range = self.get_working_hours_range(visit.start)

        matches_range = hours_range(visit.start) and hours_range(visit.end)
        return matches_range and week_day == visit.end.weekday(), ["Close hours."]

    def get_working_hours_range(self, _: datetime) -> Range:
        """Lookup schedule and retrieve working hours for a specific date"""
        return HoursRange(9, 18)


class SlotAvailabilityFilter(AvailabilityFilter):
    """Checking the slot availability"""

    def __call__(self, visit: VisitTime, user_id) -> (bool, typing.List[str]):
        conflicting_appointments = BookingService.appointments_fall_in_range(user_id, visit)
        return not len(conflicting_appointments), ["Time slot already taken."]


doctor_availability_filter = CompositeAvailabilityFilter([
    WorkingDayAndHourAvailabilityFilter(),
    SlotAvailabilityFilter()
])

patient_availability_filter = CompositeAvailabilityFilter([
    SlotAvailabilityFilter()
])
