from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import Library, District, Project, City


def home(request):

    context = {
        'libraries': Library.objects.all(),
    }
    return render(request, 'pages/home.html', context)


def projects(request):
    context = {
        'projects': Project.objects.prefetch_related('libraries').all(),
    }
    return render(request, 'pages/projects.html', context)



def map_view(request):
    context = {
        'districts': District.objects.prefetch_related(
            Prefetch(
                'cities',
                queryset=City.objects.order_by('name').prefetch_related('libraries')
            )
        ).all().order_by('name'),
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
