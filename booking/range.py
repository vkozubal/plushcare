import abc
from datetime import datetime


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
