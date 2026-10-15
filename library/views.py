from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, Count
from .models import Library, District, Project, City, LibraryType


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


CITY_TO_REGION = {
    "city-michurinsk":   "region-michurinsk",
    "city-tambov":       "region-tmb+kotovsk",
    "city-kotovsk":      "region-tmb+kotovsk",
    "city-kirsanovskiy": "region-kirsanovskiy",
    "city-morhansk":     "region-morhansk",
    "city-raskasovo":    "region-raskasovo",
    "city-uvarovskiy":   "region-uvarovskiy",
}

def map_view(request):
    districts = District.objects.prefetch_related(
        Prefetch(
            'cities',
            queryset=City.objects.order_by('name').prefetch_related('libraries')
        )
    ).all().order_by('name')

    library_types = list(LibraryType.objects.order_by("pk"))

    rows = (
        Library.objects
        .filter(city__district__isnull=False)
        .values("city__district_id", "type")
        .annotate(cnt=Count("id"))
    )
    counts_map = {(r["city__district_id"], r["type"]): r["cnt"] for r in rows}

    # pk города → pk региона
    by_map_id = {d.map_id: d for d in districts}
    merge_map = {}  # region_pk → [city_pk, ...]
    merged_city_pks = set()

    for city_map_id, region_map_id in CITY_TO_REGION.items():
        city = by_map_id.get(city_map_id)
        region = by_map_id.get(region_map_id)
        if city and region:
            merge_map.setdefault(region.pk, []).append(city.pk)
            merged_city_pks.add(city.pk)

    for d in districts:
        counts = []
        for lt in library_types:
            total = counts_map.get((d.pk, lt.pk), 0)
            for city_pk in merge_map.get(d.pk, []):
                total += counts_map.get((city_pk, lt.pk), 0)
            counts.append({"slug": lt.pk, "count": total})
        d.library_counts = counts
        # бейдж рисуем только для тех, у кого есть <path> (регионы)
        d.show_badge = d.pk not in merged_city_pks

    context = {
        "districts": districts,
        "library_types": library_types,
    }
    return render(request, 'pages/map-page.html', context)

"""

- поле про креативные место отдельное
- слить себя в мастер
- слить ветку Андрея в себя
- Слить в мастер
"""


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
