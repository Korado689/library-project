from django.shortcuts import render, get_object_or_404
from .models import Library, District, Project


def home(request):

    context = {
        'libraries': Library.objects.all(),
    }
    return render(request, 'pages/home.html', context)


def projects(request):
    context = {
        'projects': Project.objects.order_by('position'),
    }
    return render(request, 'pages/projects.html', context)


def map_view(request):
    context = {
        'districts': District.objects
        .prefetch_related('cities__libraries').all(),
    }
    return render(request, 'pages/map-page.html', context)


def library_detail(request, pk):
    lib = (Library.objects
    .select_related('city', 'city__district')
    .prefetch_related(
        'phones', 'emails', 'links',
        'collapsible_blocks',
        'list_blocks__elements',
        'albums__photos',
        'projectlibrarymembership_set__project',
    ))

    context = {
        'library': get_object_or_404(lib, pk=pk),
    }
    return render(request, 'pages/library-detail.html', context)
