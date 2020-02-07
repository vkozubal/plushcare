import json
from datetime import date, timedelta

from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from booking.domain import *
from booking.models import Appointment
from booking.booking_dao import BookingDAO

doctor_availability_filter = CompositeAvailabilityFilter([
    WorkingDayAndHourAvailabilityFilter(),
    SlotAvailabilityFilter()
])

patient_availability_filter = CompositeAvailabilityFilter([
    SlotAvailabilityFilter()
])


@csrf_exempt
def list_appointments(request, for_date: date, current_user_id=1):
    """List available appointments for a specific day for a specific user."""

    if request.method != 'GET':
        return HttpResponse(status=405)

    query_set = BookingDAO.get_appointments_for_range(current_user_id, for_date, timedelta(days=1) + for_date)

    return JsonResponse(status=200, data={"appointments": [model_to_dict(model) for model in query_set]})


@csrf_exempt
def book_appointment(request, current_user_id=1):
    """Allow patients to only book appointment."""
    if request.method != 'POST':
        return JsonResponse(status=405, data='Method Not Allowed')

    payload = json.loads(request.body)
    doctor_id: int = payload['doctor_id']
    appointment_start: datetime = datetime.fromisoformat(payload['appointment_start'])
    appointment_finish: datetime = datetime.fromisoformat(payload['appointment_finish'])

    visit_time = VisitTime(appointment_start, appointment_finish)

    doctor_availability, reasons = doctor_availability_filter(visit_time, current_user_id)
    if not doctor_availability:  # doctor isn't available for the specified visit time
        return JsonResponse(status=409, data={"reasons": reasons})

    patient_available, reasons = patient_availability_filter(visit_time, current_user_id)
    if not patient_available:  # patient isn't available for the specified visit time
        return JsonResponse(status=409, data={"reasons": reasons})

    appointment = Appointment(
        patient_id=current_user_id,
        doctor_id=doctor_id,
        appointment_start=appointment_start,
        appointment_finish=appointment_finish,
    )
    appointment.save()
    return JsonResponse(status=201, data=model_to_dict(appointment))
