from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    District, Library, Project,
    Photo, LibraryBlock, Settlement, ListItem,
    ProjectFieldValue, ProjectFieldTemplate, LibraryType, Contacts
)


# ==================== SETTLEMENT ====================

class SettlementForm(forms.ModelForm):
    class Meta:
        model = Settlement
        fields = '__all__'

    def clean_is_main(self):
        return self.cleaned_data.get('is_main')


class BaseSettlementInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        main_count = sum(
            1 for form in self.forms
            if form.cleaned_data.get('is_main') and not form.cleaned_data.get('DELETE', False)
        )
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


# ==================== PROJECT ====================

class ProjectFieldTemplateInline(admin.TabularInline):
    model = ProjectFieldTemplate
    extra = 0
    fields = ['field_name']


class ProjectFieldValueInline(admin.TabularInline):
    model = ProjectFieldValue
    extra = 0
    fields = ['template', 'value']
    autocomplete_fields = ['template']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.pk:
            project_ids = obj.projects.values_list('id', flat=True)
            formset.form.base_fields['template'].queryset = ProjectFieldTemplate.objects.filter(
                project_id__in=project_ids
            )
            # Если у выбранных проектов нет шаблонов — скрываем поле template
            if not formset.form.base_fields['template'].queryset.exists():
                formset.form.base_fields['template'].widget = forms.HiddenInput()
                formset.form.base_fields['value'].widget = forms.HiddenInput()
        else:
            formset.form.base_fields['template'].queryset = ProjectFieldTemplate.objects.none()
        return formset
# ==================== LIBRARY BLOCK FORM ====================

class LibraryBlockForm(forms.ModelForm):
    class Meta:
        model = LibraryBlock
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'library' in self.fields:
            self.fields['library'].label_from_instance = (
                lambda obj: f"{obj.name} ({obj.district.name})"
            )
        if 'zip_archive' in self.fields:
            self.fields['zip_archive'].help_text = (
                'Загрузите ZIP-архив с фотографиями. '
                'Поддерживаемые форматы: JPG, PNG, GIF, WebP. '
                'Фотографии будут автоматически распакованы.'
            )

    def clean(self):
        cleaned_data = super().clean()
        block_type = cleaned_data.get('block_type')

        type_required_fields = {
            'info': ['text'],
            'file': ['pdf_file'],
            'video': ['video_url'],
        }

        required = type_required_fields.get(block_type, [])
        for field in required:
            if not cleaned_data.get(field):
                self.add_error(
                    field,
                    f'Это поле обязательно для типа '
                    f'«{dict(LibraryBlock.BlockType.choices).get(block_type, "")}»'
                )

        # Очищаем поля, не нужные для текущего типа
        all_fields = {'text', 'pdf_file', 'video_description', 'video_url', 'album_description'}
        keep_fields = set(required)
        if block_type == 'video':
            keep_fields.add('video_description')
        if block_type == 'photoalbum':
            keep_fields.add('album_description')
        for field in all_fields - keep_fields:
            cleaned_data[field] = None

        return cleaned_data


# ==================== INLINES ДЛЯ STANDALONE БЛОКА ====================

class ListItemInline(admin.TabularInline):
    model = ListItem
    fields = ['text']
    extra = 1
    verbose_name = "Элемент списка"
    verbose_name_plural = "Элементы списка"


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 3
    fields = ['image', 'caption']
    verbose_name = "Фотография"
    verbose_name_plural = "Фотографии"


# ==================== INLINE БЛОКОВ НА СТРАНИЦЕ БИБЛИОТЕКИ ====================

class LibraryBlockInline(admin.StackedInline):
    """
    Инлайн на странице Библиотеки.
    Все поля присутствуют в DOM — JS скрывает лишние по выбранному типу.
    """
    model = LibraryBlock
    form = LibraryBlockForm
    extra = 0
    can_delete = True
    show_change_link = True  # ← ссылка на полную страницу блока (там фото/список)
    verbose_name = "Секция"
    verbose_name_plural = "Секции"

    fields = [
        'block_type', 'title', 'is_visible',
        'text',
        'pdf_file',
        'video_description', 'video_url',
        'album_description', 'zip_archive'
    ]

    class Media:
        js = ('admin/scripts/toggleField.js',)
        css = {'all': ('admin/css/toggleField.css',)}

    def get_inline_instances(self, request, obj=None):
        """
        Добавляем вложенные инлайны прямо в StackedInline.
        Для list — ListItemInline, для photoalbum — PhotoInline.
        """
        inline_instances = []

        block_type = None

        # Определяем тип блока
        if obj and obj.pk:
            block_type = obj.block_type
        elif request.method == 'POST':
            # Ищем block_type в POST-данных для этого конкретного инлайна
            prefix = self.get_prefix(request, obj=None)
            # Для существующих объектов
            if obj and obj.pk:
                key = f'blocks-{obj.pk}-block_type'
            else:
                # Для новых — ищем среди __prefix__ или новых строк
                for post_key in request.POST:
                    if post_key.endswith('-block_type') and 'blocks' in post_key:
                        block_type = request.POST[post_key]
                        break
                if not block_type:
                    # Пробуем найти в данных формы
                    for post_key in request.POST:
                        if 'blocks-' in post_key and post_key.endswith('-block_type'):
                            block_type = request.POST[post_key]
                            break

        if block_type == 'list':
            inline_instances.append(ListItemInline(self.model, self.admin_site))
        elif block_type == 'photoalbum':
            inline_instances.append(PhotoInline(self.model, self.admin_site))

        return inline_instances


# ==================== STANDALONE СТРАНИЦА БЛОКА ====================

@admin.register(LibraryBlock)
class LibraryBlockAdmin(admin.ModelAdmin):
    form = LibraryBlockForm
    list_display = ['title', 'library_link', 'block_type', 'is_visible', 'content_preview']
    list_filter = ['block_type', 'is_visible', 'library__district', 'library']
    search_fields = ['title', 'library__name']
    autocomplete_fields = ['library']

    class Media:
        js = ('admin/scripts/toggleField.js',)
        css = {'all': ('admin/css/toggleField.css',)}

    # Все поля присутствуют — JS скроет ненужные
    fieldsets = (
        ('Основное', {
            'fields': ('library', 'block_type', 'title', 'is_visible'),
        }),
        ('Информационный блок', {
            'fields': ('text',),
        }),
        ('Файл', {
            'fields': ('pdf_file',),
        }),
        ('Видео', {
            'fields': ('video_description', 'video_url'),
        }),
        ('Фотоальбом', {
            'fields': ('album_description', 'zip_archive'),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj and obj.pk:
            if obj.block_type == 'list':
                return [ListItemInline]
            if obj.block_type == 'photoalbum':
                return [PhotoInline]
        return []

    def library_link(self, obj):
        if obj.library:
            url = reverse('admin:library_library_change', args=[obj.library.id])
            return format_html('<a href="{}">{}</a>', url, obj.library.name)
        return "—"

    library_link.short_description = 'Библиотека'

    def content_preview(self, obj):
        if obj.block_type == 'info' and obj.text:
            return obj.text[:100] + ('...' if len(obj.text) > 100 else '')
        elif obj.block_type == 'list':
            return f"{obj.list_items.count()} элементов"
        elif obj.block_type == 'file' and obj.pdf_file:
            return "PDF"
        elif obj.block_type == 'video' and obj.video_url:
            return "Видео"
        elif obj.block_type == 'photoalbum':
            return f"{obj.photos.count()} фото"
        return "—"

    content_preview.short_description = 'Содержимое'

    def response_add(self, request, obj, post_url_continue=None):
        if '_addanother' not in request.POST and '_continue' not in request.POST:
            from django.http import HttpResponseRedirect
            if obj.library:
                return HttpResponseRedirect(
                    reverse('admin:library_library_change', args=[obj.library.id])
                )
        return super().response_add(request, obj, post_url_continue)


# ==================== DISTRICT / SETTLEMENT ====================

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'svg_id', 'main_settlement', 'settlements_count']
    search_fields = ['name']
    inlines = [SettlementInline]
    fieldsets = (
        ('Основное', {'fields': ('name', 'svg_id')}),
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
        if obj.is_main:
            obj.district.main_settlement = obj
            obj.district.save(update_fields=['main_settlement'])


# ==================== LIBRARY ====================

@admin.register(LibraryType)
class LibraryTypeAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Contacts)
class ContactsAdmin(admin.ModelAdmin):
    list_display = ['type', 'value', 'description']
    list_filter = ['type']
    search_fields = ['value', 'description']


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'settlement', 'library_type']
    list_filter = ['district', 'library_type']
    search_fields = ['name', 'address']
    inlines = [LibraryBlockInline, ProjectFieldValueInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'photo', 'library_type', 'district', 'settlement', 'status', 'area')
        }),
        ('Проекты', {
            'fields': ('projects',)
        }),
        ('Адрес и контакты', {
            'fields': ('address', 'working_hours', 'contacts')
        }),
    )
    filter_horizontal = ['projects', 'contacts']
    autocomplete_fields = ['projects', 'settlement']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "settlement":
            district_id = request.GET.get('district')
            if not district_id and request.resolver_match.kwargs.get('object_id'):
                try:
                    library = Library.objects.get(pk=request.resolver_match.kwargs['object_id'])
                    district_id = library.district_id
                except Library.DoesNotExist:
                    pass
            kwargs["queryset"] = (
                Settlement.objects.filter(district_id=district_id)
                if district_id else Settlement.objects.all()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_inline_instances(self, request, obj=None):
        inline_instances = []

        # Базовые инлайны
        for inline_class in self.inlines:
            inline_instances.append(inline_class(self.model, self.admin_site))

        # ProjectFieldValueInline — только если у библиотеки есть проекты
        if obj and obj.pk and obj.projects.exists():
            # Создаём инлайн и передаём библиотеку через начальные данные
            inline = ProjectFieldValueInline(self.model, self.admin_site)
            inline_instances.append(inline)

        # Если POST-запрос и в данных есть проекты
        elif request.method == 'POST':
            # Проверяем, выбраны ли проекты в POST-данных
            project_ids = request.POST.getlist('projects')
            if project_ids and any(pid for pid in project_ids if pid):
                inline = ProjectFieldValueInline(self.model, self.admin_site)
                inline_instances.append(inline)

        return inline_instances

    class Media:
        js = ('admin/scripts/toggleField.js', 'admin/scripts/project_fields_toggle.js')

# ==================== PROJECT ====================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'libraries_count']
    search_fields = ['name']
    inlines = [ProjectFieldTemplateInline]
    fieldsets = (
        ('Основное', {'fields': ('name', 'photo', 'description')}),
    )

    def libraries_count(self, obj):
        return obj.library_set.count()

    libraries_count.short_description = 'Библиотек'


@admin.register(ProjectFieldTemplate)
class ProjectFieldTemplateAdmin(admin.ModelAdmin):
    list_display = ['field_name', 'project', 'values_count']
    list_filter = ['project']
    search_fields = ['field_name', 'project__name']
    inlines = [ProjectFieldValueInline]

    def values_count(self, obj):
        return obj.values.count()

    values_count.short_description = 'Значений'
