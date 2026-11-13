from apps.backoffice.selectors.archive import get_archive_context
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def archive(request):
    context = get_archive_context()
    return render(request, 'missions/archive.html', context)
