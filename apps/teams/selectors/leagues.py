"""Team ranking queries over caller-supplied monthly point totals."""

from missions.models import Team


def get_profile_team_leaderboard(user_month_points, user_team):
    team_leaderboard = []
    teams = Team.objects.prefetch_related('members__user')
    for team in teams:
        members = [m.user for m in team.members.all()]
        total = sum(user_month_points.get(u.id, 0) for u in members)

        team_leaderboard.append({
            'id': team.id,
            'name': team.name,
            'member_count': len(members),
            'total_points': total,
            'is_mine': user_team and team.id == user_team.id,
        })

    team_leaderboard.sort(key=lambda x: x['total_points'], reverse=True)

    for idx, row in enumerate(team_leaderboard, start=1):
        row['rank'] = idx
    return team_leaderboard


def get_league_rankings(user, user_team, user_month_points):
    all_teams = get_ranked_teams(user_month_points)
    my_team_data = None
    if user_team:
        members_data = []
        for member in user_team.members.select_related('user'):
            m_points = user_month_points.get(member.user_id, 0)
            members_data.append({
                'user': member.user,
                'points': m_points,
                'is_me': member.user_id == user.id,
            })

        members_data.sort(key=lambda x: x['points'], reverse=True)

        for idx, m in enumerate(members_data, start=1):
            m['rank'] = idx

        team_total = sum(m['points'] for m in members_data)

        my_team_rank = next(
            (t['rank'] for t in all_teams if t['id'] == user_team.id),
            None
        )

        my_team_data = {
            'team': user_team,
            'members': members_data,
            'member_count': len(members_data),
            'total_points': team_total,
            'rank': my_team_rank,
        }

    return my_team_data, all_teams


def get_ranked_teams(user_month_points):
    """لیست همه تیم‌ها با امتیاز ماهانه، مرتب‌شده و رتبه‌بندی‌شده."""
    teams = Team.objects.prefetch_related('members__user').select_related('manager')

    ranked = []
    for team in teams:
        members = [m.user for m in team.members.all()]
        total = sum(user_month_points.get(u.id, 0) for u in members)

        top_members = sorted(
            [{'user': u, 'points': user_month_points.get(u.id, 0)} for u in members],
            key=lambda x: x['points'],
            reverse=True,
        )[:3]

        ranked.append({
            'id': team.id,
            'name': team.name,
            'manager': team.manager,
            'member_count': len(members),
            'total_points': total,
            'top_members': top_members,
        })

    ranked.sort(key=lambda x: x['total_points'], reverse=True)

    for idx, row in enumerate(ranked, start=1):
        row['rank'] = idx

    return ranked
