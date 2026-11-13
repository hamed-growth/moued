from django.http import JsonResponse


def submission_error_response(error):
    data = {'success': False, 'message': str(error)}
    if error.completed:
        data['is_completed'] = True
    return JsonResponse(data, status=400)
