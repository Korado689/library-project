from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedModelAdmin, NestedTabularInline, NestedStackedInline

from .models import (
    District, Library, Project, Photo, City, Phone, Email, Links, CollapsibleBlock, ListBlock, ListElement,
    ProjectLibraryMembership, PhotoAlbum
)


class PhoneInline(NestedTabularInline):
    model = Phone
    extra = 0


class EmailInline(NestedTabularInline):
    model = Email
    extra = 0


class LinksInline(NestedTabularInline):
    model = Links
    extra = 0


class CollapsibleBlockInline(NestedStackedInline):
    model = CollapsibleBlock
    extra = 0


class ListElementInline(NestedTabularInline):
    model = ListElement
    extra = 0


class ListBlockInline(NestedStackedInline):
    model = ListBlock
    extra = 0
    inlines = [ListElementInline]


class ProjectInline(NestedTabularInline):
    model = ProjectLibraryMembership
    extra = 0

class PhotoInline(admin.StackedInline):
    model = Photo
    extra = 0

@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'library')
    list_filter = ('library',)
    inlines = [PhotoInline]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'position')
    list_filter = ('title', 'position')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'capital')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'district')


@admin.register(Library)
class LibraryAdmin(NestedModelAdmin):
    list_display = ('name', 'city', 'get_projects')
    inlines = [ProjectInline, PhoneInline, EmailInline, LinksInline, CollapsibleBlockInline, ListBlockInline]

    @admin.display(description=_('Проекты'))
    def get_projects(self, obj):
        return ", ".join([project.title for project in obj.projects.all()])
