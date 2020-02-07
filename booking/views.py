import json
from datetime import date, timedelta, datetime

from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from booking.range import VisitTime
from booking.models import Appointment
from booking.booking_service import BookingService


@csrf_exempt
def list_appointments(request, for_date: date, current_user_id=1):
    """List available appointments for a specific day for a specific user."""

    if request.method != 'GET':
        return HttpResponse(status=405)

    query_set = BookingService.get_appointments_for_range(current_user_id, for_date, timedelta(days=1) + for_date)
    return JsonResponse(status=200, data={"appointments": [model_to_dict(model) for model in query_set]})


@csrf_exempt
def book_appointment(request, current_user_id=1):
    """Allow patients to only book appointment."""
    if request.method != 'POST':
        return JsonResponse(status=405, data={"reasons": ['Method Not Allowed']})
    payload = json.loads(request.body)
    doctor_id: int = payload['doctor_id']
    appointment_start: datetime = datetime.fromisoformat(payload['appointment_start'])
    appointment_finish: datetime = datetime.fromisoformat(payload['appointment_finish'])

    try:
        visit_time = VisitTime(appointment_start, appointment_finish)
    except ValueError as e:
        return JsonResponse(status=400, data={"reasons": [str(e)]})

    is_available, reasons = BookingService.check_appointment_time_availability(current_user_id, doctor_id, visit_time)
    if not is_available:
        return JsonResponse(status=409, data={"reasons": reasons})

    appointment = Appointment(
        patient_id=current_user_id,
        doctor_id=doctor_id,
        appointment_start=appointment_start,
        appointment_finish=appointment_finish,
    )
    appointment.save()
    return JsonResponse(status=201, data=model_to_dict(appointment))
