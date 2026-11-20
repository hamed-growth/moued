"""Authenticated mission submission, calendar and staff review endpoints."""
from datetime import date, timedelta
from django.db import DatabaseError
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.missions.models import Mission, MissionRequest
from apps.missions.selectors.path import day_range
from apps.missions.services.requests import create_mission_request
from apps.teams.selectors.membership import get_user_team
from apps.submissions import SubmissionRejected, MissionTeamAccessDenied
from .serializers import MissionRequestSerializer


class SubmissionInput(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=5000, default='')


class MissionSubmitView(APIView):
    def post(self, request, mission_id):
        data = SubmissionInput(data=request.data)
        data.is_valid(raise_exception=True)
        mission = get_object_or_404(Mission, pk=mission_id, is_active=True)
        try:
            result = create_mission_request(request.user, mission, data.validated_data['note'])
        except MissionTeamAccessDenied as exc:
            return Response({'message': str(exc)}, status=403)
        except SubmissionRejected as exc:
            return Response({'message': str(exc)}, status=409)
        except DatabaseError:
            return Response({'message': '??? ??????? ????? ???. ?????? ???? ????.'}, status=503)
        return Response(MissionRequestSerializer(result).data, status=201)


class MissionCalendarView(APIView):
    def get(self, request):
        today = timezone.localdate()
        try:
            start = date.fromisoformat(request.query_params.get('start', today.isoformat()))
            end = date.fromisoformat(request.query_params.get('end', start.isoformat()))
        except ValueError:
            return Response({'message': '????? ??????? ???.'}, status=400)
        if end < start or (end - start).days > 31 or end > today + timedelta(days=31):
            return Response({'message': '???? ???? ?????? ?? ??? ????.'}, status=400)
        days = day_range(request.user, start, end)
        team = get_user_team(request.user)
        output = []
        for day in days:
            nodes = []
            for node in day['nodes']:
                mission = node['mission']
                if day['date'] < max(timezone.localdate(mission.created_at), timezone.localdate(request.user.date_joined)):
                    continue
                points, coins = mission.get_rewards_for_team(team)
                nodes.append({'id': mission.pk, 'title': mission.title,
                    'description': mission.description or '',
                    'points': points, 'coins': coins,
                    'status': node['state'], 'can_submit': day['date'] == today and (
                        node['state'] == 'available' or node['retry_allowed']),
                    'start_time': mission.start_time, 'end_time': mission.end_time,
                    'has_time_limit': mission.has_time_limit})
            output.append({'date': day['iso'], 'missions': nodes})
        requests = MissionRequest.objects.filter(user=request.user, requested_at__date__range=(start, end))
        active_days = requests.filter(status='approved').values('requested_at__date').distinct().count()
        rewards = requests.filter(status='approved').aggregate(points=Sum('points_awarded'), coins=Sum('coins_awarded'))
        return Response({'today': today, 'days': output, 'summary': {
            'points': request.user.total_points, 'coins': request.user.total_coins,
            'streak': request.user.activity_streak, 'activeDays': active_days,
            'monthPoints': rewards['points'] or 0, 'monthCoins': rewards['coins'] or 0}})


class StaffMissionRequestsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from .views import StandardPagination
        queryset = MissionRequest.objects.select_related('mission').order_by('-requested_at', '-pk')
        status = request.query_params.get('status', 'pending')
        if status not in dict(MissionRequest.STATUS_CHOICES):
            return Response({'message': '????? ??????? ???.'}, status=400)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.filter(status=status), request)
        return paginator.get_paginated_response(MissionRequestSerializer(page, many=True).data)


class MissionReviewView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, request_id):
        status = request.data.get('status')
        if status not in ('approved', 'rejected'):
            return Response({'message': '????? ???? approved ?? rejected ????.'}, status=400)
        data = SubmissionInput(data={'note': request.data.get('admin_note', '')})
        data.is_valid(raise_exception=True)
        item = get_object_or_404(MissionRequest, pk=request_id)
        try:
            action = item.approve if status == 'approved' else item.reject
            changed = action(admin_user=request.user, admin_note=data.validated_data['note'])
        except DatabaseError:
            return Response({'message': '????? ????? ???. ?????? ???? ????.'}, status=503)
        if not changed:
            return Response({'message': '??????? ????? ????? ??? ???.'}, status=409)
        return Response(MissionRequestSerializer(item).data)
