import json
from datetime import datetime, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from booking.models import Appointment, Patient


class TestListView(TestCase):

    def setUp(self):
        self._client = Client()
        self._today = datetime.now()
        self._yesterday = self._today - timedelta(days=1)

        Appointment(
            doctor_id=1,
            patient_id=1,
            created_at=datetime.now(),
            appointment_start=self._today,
            appointment_finish=self._today + timedelta(hours=1)
        ).save()

        Appointment(
            doctor_id=2,
            patient_id=1,
            created_at=self._yesterday - timedelta(hours=1),
            appointment_start=self._yesterday,
            appointment_finish=self._yesterday + timedelta(hours=2)
        ).save()

    def test_list_empty(self):
        date = datetime.fromisoformat('2019-10-08T17:20:58.975532').date()
        url = reverse('perday', args=(date,))

        response = self._client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_fetched_single_appointment_for_the_day(self):
        url = reverse('perday', args=(self._today,))
        response = self._client.get(url)
        self.assertEquals(response.status_code, 200)

        appointments = json.loads(response.content)['appointments']
        self.assertEquals(len(appointments), 1)

        appointment = appointments[0]
        self.assertEquals(appointment['status'], 'OPEN')
        self.assertEquals(appointment['patient'], 1)
        self.assertEquals(appointment['doctor'], 1)


_start_at = datetime.fromisoformat('2019-10-08T10:20:58.975532')
_finish_at = _start_at + timedelta(hours=2, minutes=20)


class TestBookingRangesConflicts(TestCase):

    def setUp(self) -> None:
        Appointment(
            doctor_id=2,
            patient_id=1,
            appointment_start=_start_at,
            appointment_finish=_finish_at
        ).save()
        self._client = Client()

    def test_same_doctor_patient_range_booking_conflict(self):
        for start_offset, finish_offset, response_status in [
            (1, 1, 409),
            (-1, -1, 409),
            (1, -1, 409),
            (-1, 1, 409),
            (3.3, 5, 201),  # successful case last, changes DB state
        ]:

            appointment_start = _start_at + timedelta(hours=start_offset)
            appointment_finish = _finish_at + timedelta(hours=finish_offset)

            number_of_appointments = len(Appointment.objects.all())

            response = self._client.post(reverse('bookings'), data={
                "appointment_start": appointment_start,
                "appointment_finish": appointment_finish,
                "doctor_id": 1
            }, content_type='application/json')

            self.assertEquals(response.status_code, response_status)

            if response_status == 409:
                self.assertEquals(len(Appointment.objects.all()), number_of_appointments)
            elif response_status == 201:
                self.assertEquals(len(Appointment.objects.all()), number_of_appointments + 1)


class TestBookingTwoDoctorsConflicts(TestCase):

    def setUp(self) -> None:
        _start_at = datetime.fromisoformat('2019-10-08T10:20:58.975532')
        self._appointment = Appointment(
            doctor_id=1,
            patient_id=1,
            appointment_start=_start_at,
            appointment_finish=_start_at + timedelta(hours=2, minutes=20)
        )
        self._appointment.save()
        self._client = Client()

    def test_two_doctors_appointment_with_the_same_patient_negative(self):
        for start_offset, finish_offset, status_code in [
            (1, 1, 409),  # negative
            (3, 3, 201),  # positive
        ]:
            response = self._client.post(reverse('bookings'), data={
                "appointment_start": self._appointment.appointment_start + timedelta(hours=start_offset),
                "appointment_finish": self._appointment.appointment_finish + timedelta(hours=finish_offset),
                "doctor_id": 2
            }, content_type='application/json')

            self.assertEquals(response.status_code, status_code)


class TestSetAppointmentNonWorkingHours(TestCase):
    def setUp(self) -> None:
        self._client = Client()

    def test_non_working_hours(self):
        for start_offset, finish_offset, status_code in [
            (-3, 0, 409),
            (0, 10, 409),
            (0, 24, 400),
        ]:
            _start_at = datetime.fromisoformat('2019-10-08T10:20:58.975532')
            response = self._client.post(reverse('bookings'), data={
                "appointment_start": _start_at + timedelta(hours=start_offset),
                "appointment_finish": _start_at + timedelta(hours=finish_offset),
                "doctor_id": 2
            }, content_type='application/json')

            self.assertEquals(response.status_code, status_code)


class TestDifferentMonthsAndWeeksDays(TestCase):
    def setUp(self) -> None:
        self._client = Client()
        Appointment(
            doctor_id=1,
            patient_id=1,
            appointment_start=datetime.fromisoformat("2020-10-08T12:14:58.975"),
            appointment_finish=datetime.fromisoformat("2020-10-08T16:14:58.975")
        ).save()
        Appointment(
            doctor_id=1,
            patient_id=1,
            appointment_start=datetime.fromisoformat("2020-10-08T17:20:58.975"),
            appointment_finish=datetime.fromisoformat("2020-10-08T17:21:58.975")
        ).save()
        Appointment(
            doctor_id=1,
            patient_id=1,
            appointment_start=datetime.fromisoformat("2020-10-05T17:20:58.975"),
            appointment_finish=datetime.fromisoformat("2020-10-05T17:21:58.975")
        ).save()
        Appointment(
            doctor_id=1,
            patient_id=1,
            appointment_start=datetime.fromisoformat("2020-11-02T17:20:58.975"),
            appointment_finish=datetime.fromisoformat("2020-11-02T17:21:58.975")
        ).save()

    def test_positive(self):
        response = self._client.post(reverse('bookings'), data={
            "appointment_start": datetime.fromisoformat("2020-10-02T17:20:58.975532"),
            "appointment_finish": datetime.fromisoformat("2020-10-02T17:21:58.975532"),
            "doctor_id": 1
        }, content_type='application/json')

        self.assertEquals(response.status_code, 201)


class TestBookingTwoPatientsConflicts(TestCase):

    def setUp(self) -> None:
        self._appointment = Appointment(
            doctor_id=2,
            patient_id=2,
            appointment_start=_start_at,
            appointment_finish=_finish_at
        )
        self._appointment.save()
        self._patient2 = Patient(email='Jane.Doe@gmail.com', name='Jane Doe', )
        self._patient2.save()
        self._client = Client()

    def test_two_patients_appointment_with_the_same_doctor(self):
        for start_offset, finish_offset, status_code in [
            (1, 1, 409),  # negative
            (3, 3, 201),  # positive
        ]:
            response = self._client.post(reverse('bookings'), data={
                "appointment_start": self._appointment.appointment_start + timedelta(hours=start_offset),
                "appointment_finish": self._appointment.appointment_finish + timedelta(hours=finish_offset),
                "doctor_id": 2
            }, content_type='application/json')

            self.assertEquals(response.status_code, status_code)

    def test_two_patients_two_doctors_positive(self):
        response = self._client.post(reverse('bookings'), data={
            "appointment_start": self._appointment.appointment_start + timedelta(hours=1),
            "appointment_finish": self._appointment.appointment_finish + timedelta(hours=1),
            "doctor_id": 1
        }, content_type='application/json')

        self.assertEquals(response.status_code, 201)
