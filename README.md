# plushcare


The ask is to build a simple booking service using Python/Django to allow a user to see available appointments and to book one. At a minimum an appointment has a date, time and assigned doctor. 
Booking an appointment will mark it as booked and tie to the user who booked it, preventing it from being booked by other users.

- Build models for appointment, patient and doctor
- Build two endpoints:
a) List of available appointments for a specific day
b) Book appointment
- Allow patients to only book appointment if it's available

For simplicity reasons, both APIs won't require authentication. A front-end is also not required. Unit tests are not required but encouraged.

Please send back the project as a zip file with instructions on how to run it. You could also add a Postman or Charles session to demonstrate the use of the API.


HOW TO:

Apply migration and run server. Database is populated with patients and doctors.
```bash
python manage.py migrate booking
python manage.py runserver
```

Book appointment
```bash
curl -v -X POST http://127.0.0.1:8000/appointments/ -d '{"appointment_start":"2020-10-08T12:14:58.975532", "appointment_finish":"2020-10-08T16:14:58.975532", "doctor_id":2 }'
```

List appointments for the specific date. Date format: `%Y%m%d`
```bash
curl -v  http://127.0.0.1:8000/appointments/dates/20201008
```