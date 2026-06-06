from django import forms
from django.contrib import admin

# Register your models here.
# library/admin.py

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import (
    District, LibraryType, Library,
    Coordinators, Project,
    WebSite,
    PhotoAlbum, Photo, VideoBusinessCard, LibraryBlock, Settlement
)


# ==================== INLINE МОДЕЛИ ====================

class SettlementForm(forms.ModelForm):
    class Meta:
        model = Settlement
        fields = '__all__'

        def clean_is_main(self):
            # Валидируем только поле is_main, без district
            return self.cleaned_data.get('is_main')

class BaseSettlementInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Собираем все галочки is_main из всех форм
        main_count = 0
        for form in self.forms:
            if form.cleaned_data.get('is_main') and not form.cleaned_data.get('DELETE', False):
                main_count += 1

        if main_count > 1:
            raise ValidationError(
                'Может быть только один главный город в районе. '
                'Оставьте галочку только у одного населённого пункта.'
            )



class SettlementInline(admin.TabularInline):
    model = Settlement
    form = SettlementForm
    formset = BaseSettlementInlineFormSet
    extra = 1
    fields = ['name', 'is_main']



class WebSiteInline(admin.TabularInline):
    model = WebSite
    extra = 1
    fields = ['url']


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1
    fields = ['image', 'caption']


class PhotoAlbumInline(admin.TabularInline):
    model = PhotoAlbum
    extra = 0
    fields = ['title']
    show_change_link = True


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'svg_id', 'main_settlement', 'settlements_count']
    search_fields = ['name']
    inlines = [SettlementInline]
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'svg_id',)
        }),
    )

    def settlements_count(self, obj):
        return obj.settlements.count()

    settlements_count.short_description = "Населённых пунктов"


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    form = SettlementForm
    list_display = ['name', 'district', 'is_main']
    list_filter = ['district', 'is_main']
    search_fields = ['name']
    ordering = ['district', '-is_main', 'name']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # После сохранения проверяем связь с main_settlement
        if obj.is_main:
            obj.district.main_settlement = obj
            obj.district.save(update_fields=['main_settlement'])


class LibraryBlockInline(admin.StackedInline):
    model = LibraryBlock
    extra = 0
    fields = ['block_type', 'title', 'year', 'content', 'order', 'is_visible']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'year':
            field.widget.attrs['class'] = 'field-year'
        if db_field.name == 'block_type':
            field.widget.attrs['onchange'] = 'toggleYearField(this)'
        return field

    class Media:
        js = ('admin/scripts/toggleField.js',)


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'settlement', 'library_type', 'modernization_year', 'created_at']
    list_filter = ['district', 'library_type', 'modernization_year']
    search_fields = ['name', 'address', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [
        WebSiteInline,
        PhotoAlbumInline,
        LibraryBlockInline,  # Добавляем блоки
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'photo', 'library_type', 'district', 'settlement', 'status')
        }),
        ('Характеристики', {
            'fields': ('area', 'modernization_year')
        }),
        ('Адрес и контакты', {
            'fields': ('address', ('phone', 'phone_owner'), 'email', 'working_hours')
        }),
        ('Дизайн-проект', {
            'fields': ('pdf_file',),
            'classes': ('collapse',)
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "settlement":
            # Фильтруем населённые пункты по выбранному району
            if 'district' in request.GET:
                kwargs["queryset"] = Settlement.objects.filter(district_id=request.GET['district'])
            else:
                kwargs["queryset"] = Settlement.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Coordinators)
class CoordinatorAdmin(admin.ModelAdmin):
    list_display = ['name', ]
    search_fields = ['name']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', ]
    search_fields = ['name', 'description']


@admin.register(WebSite)
class WebSiteAdmin(admin.ModelAdmin):
    list_display = ['library', 'url']
    list_filter = ['library__district']
    search_fields = ['library__name', 'url']


@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(admin.ModelAdmin):
    list_display = ['title', 'library', 'created_at']
    list_filter = ['library__district']
    search_fields = ['title', 'library__name']
    inlines = [PhotoInline]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['caption', 'album']
    list_filter = ['album__library__district']
    search_fields = ['caption', 'album__title']


@admin.register(VideoBusinessCard)
class VideoBusinessCardAdmin(admin.ModelAdmin):
    list_display = ['library', 'video_url', ]
    search_fields = ['library__name']
