import abc
from datetime import datetime

import typing

from booking.booking_dao import BookingDAO


class Range(abc.ABC):
    @abc.abstractmethod
    def __call__(self, dt: datetime) -> bool:
        raise NotImplementedError

    def __str__(self):
        return repr(self)


class HoursRange(Range):
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __call__(self, dt: datetime) -> bool:
        return self.start <= dt.hour < self.end

    def __repr__(self):
        return f'{self.start} <= current_hour < {self.end}'


class VisitTime:
    def __init__(self, start: datetime, end: datetime):
        """Visit time range. Performs validation of input parameters
        :param start: datetime we perform check for
        :param duration: duration of the visit
        """

        if start.date() != end.date():  # on the same date
            raise ValueError("Visit should finish on the same day.")

        if start >= end:
            raise ValueError("Visit duration should be positive.")

        self.start = start
        self.end = end


class AvailabilityFilter(abc.ABC):

    @abc.abstractmethod
    def __call__(self, visit: VisitTime, user_id) -> (bool, typing.List[str]):
        """
        General filter returns availability for a specified time of visit
        :return: tuple (availability, explanation)
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
    """Checking the """

    def __call__(self, visit: VisitTime, user_id) -> (bool, typing.List[str]):
        conflicting_appointments = BookingDAO.appointments_fall_in_range(visit.start, visit.end, user_id)
        return not len(conflicting_appointments), ["Time slot already taken."]
