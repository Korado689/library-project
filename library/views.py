import json

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
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
    return render(request, 'about-project-page.html', context)


# ==================== КАРТА БИБЛИОТЕК ====================

def map_view(request):
    districts = District.objects.prefetch_related(
        'settlements__libraries'
    ).all().order_by('name')

    # Формируем JSON для фронта
    districts_data = []
    for district in districts:
        settlements_data = []
        for settlement in district.settlements.all():
            libraries_data = []
            for library in settlement.libraries.all():
                libraries_data.append({
                    'id': library.id,
                    'name': library.name,
                    'type': library.library_type,
                    'type_label': library.get_library_type_display(),
                    'icon': library.marker_icon,
                    'url': f'/library/{library.id}/',
                })
            if libraries_data:
                settlements_data.append({
                    'name': settlement.name,
                    'is_main': settlement.is_main,
                    'libraries': libraries_data,
                })

        districts_data.append({
            'id': district.id,
            'name': district.name,
            'svg_id': district.svg_id,
            'settlements': settlements_data,
        })

    context = {
        'districts': districts,
        'districts_json': json.dumps(districts_data, ensure_ascii=False),
    }
    return render(request, 'map-page.html', context)


def library_detail(request, pk):
    lib = get_object_or_404(Library, pk=pk)
    context = {
        'library': lib,
    }
    return render(request, 'library-detail.html', context)


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