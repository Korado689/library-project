import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Library, District, Project, Coordinators, LibraryType

# views.py
# ==================== ГЛАВНАЯ СТРАНИЦА ====================

def home(request):
    """Главная страница с информационными зонами"""
    return render(request, 'main-page.html')


# ==================== ПРОЕКТЫ ====================

def projects(request):
    """Страница с проектами и координаторами"""
    projects_list = Project.objects.select_related('coordinator').all()
    coordinators_list = Coordinators.objects.prefetch_related('projects').all()

    context = {
        'projects': projects_list,
        'coordinators': coordinators_list,
    }
    return render(request, 'projects.html', context)


# ==================== КАРТА БИБЛИОТЕК ====================

def map_view(request):
    districts = District.objects.prefetch_related(
        'settlements__libraries'
    ).all().order_by('name')

    context = {
        'districts': districts,
    }
    return render(request, 'map-page.html', context)


def get_libraries_by_district(request, district_id):
    """API: получить библиотеки конкретного района"""
    libraries = Library.objects.filter(
        district_id=district_id
    ).select_related('library_type')

    data = []
    for lib in libraries:
        data.append({
            'id': lib.id,
            'name': lib.name,
            'address': lib.address,
            'marker_type': lib.marker_type,
            'marker_icon': lib.marker_icon,
            'marker_size': lib.marker_size,
            'svg_x': lib.svg_x,
            'svg_y': lib.svg_y,
            'detail_url': f'/library/{lib.id}/',
        })

    return JsonResponse({'libraries': data})


def libraries_map_data(request):
    """API: все библиотеки для карты"""
    libraries = Library.objects.select_related(
        'district', 'library_type'
    )

    # Фильтры
    district_id = request.GET.get('district')
    if district_id:
        libraries = libraries.filter(district_id=district_id)

    type_id = request.GET.get('type')
    if type_id:
        libraries = libraries.filter(library_type_id=type_id)

    markers = []
    for lib in libraries:
        markers.append({
            'id': lib.id,
            'name': lib.name,
            'district_name': lib.district.name,
            'district_svg_id': lib.district.svg_id,
            'marker_icon': lib.marker_icon,
            'marker_size': lib.marker_size,
            'marker_type': lib.get_marker_type_display(),
            'detail_url': f'/library/{lib.id}/',
            'modernization_year': lib.modernization_year,
        })

    return JsonResponse({'markers': markers})