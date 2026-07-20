import os
import zipfile
from urllib.parse import unquote

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models import Max
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedModelAdmin, NestedTabularInline, NestedStackedInline

from .models import (
    District, Library, Project, Photo, City, Phone, Email, Links, CollapsibleBlock, ListBlock, ListElement,
    ProjectLibraryMembership, PhotoAlbum
)


def _decode_zip_filename(info: zipfile.ZipInfo) -> str:
    """
    Корректно декодирует имя файла из ZIP.
    Если UTF-8 флаг (бит 11) выставлен — Python уже всё правильно декодировал.
    Если нет — Python декодировал как cp437, восстанавливаем байты и пробуем cp866/cp1251.
    """
    if info.flag_bits & 0x800:
        # UTF-8 флаг выставлен — всё ок
        return info.filename

    # Восстанавливаем исходные байты (Python читал как cp437)
    try:
        raw_bytes = info.filename.encode('cp437')
    except UnicodeEncodeError:
        return info.filename

    # Пробуем кодировки по порядку
    for encoding in ('utf-8', 'cp866', 'cp1251'):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    return info.filename  # fallback

def _sanitize_filename(name: str) -> str:
    """
    Раздекодируем URL-percent-encoding (%20 → пробел, %D0%B2 → в),
    затем убираем любые оставшиеся % которые ломают Python % string formatting.
    """
    name = unquote(name)       # %D0%B2%D0%B5%D0%BA → «век»
    name = name.replace('%', '_')  # на случай голых % без hex-пары
    return name

class PhotoAlbumAdminForm(forms.ModelForm):
    zip_archive = forms.FileField(
        required=False,
        label='📦 Загрузить ZIP архив с фотографиями',
        help_text='Поддерживаются JPG, PNG, GIF, WebP, BMP. Названия файлов станут заголовками фото.',
        widget=forms.FileInput(attrs={'accept': '.zip'})
    )

    class Meta:
        model = PhotoAlbum
        fields = '__all__'

    def clean_zip_archive(self):
        zip_file = self.cleaned_data.get('zip_archive')

        if not zip_file:
            return None

        if not zip_file.name.lower().endswith('.zip'):
            raise ValidationError('Файл должен быть ZIP архивом')

        try:
            with zipfile.ZipFile(zip_file) as zf:
                if zf.testzip() is not None:
                    raise ValidationError('Архив поврежден')

                supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')

                # Собираем ZipInfo-объекты, а не строки
                image_infos = []
                for info in zf.infolist():
                    decoded_name = _decode_zip_filename(info)
                    if (
                            decoded_name.lower().endswith(supported_extensions)
                            and not decoded_name.startswith('__MACOSX')
                            and not os.path.basename(decoded_name).startswith('.')
                    ):
                        image_infos.append(info)

                if not image_infos:
                    raise ValidationError(
                        'В архиве нет изображений. Поддерживаемые форматы: JPG, PNG, GIF, WebP, BMP'
                    )

                # Проверяем размер через info.file_size напрямую — никакого getinfo()
                for info in image_infos:
                    if info.file_size > 10 * 1024 * 1024:
                        decoded_name = _decode_zip_filename(info)
                        raise ValidationError(
                            'Файл %(filename)s слишком большой. Максимум 10 MB',
                            params={'filename': os.path.basename(decoded_name)},
                            code='file_too_large',
                        )

        except zipfile.BadZipFile:
            raise ValidationError('Файл не является ZIP архивом или архив поврежден')

        # Сбрасываем позицию — ZipFile читал файл, указатель сместился
        zip_file.seek(0)
        return zip_file


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
    form = PhotoAlbumAdminForm  # Добавляем форму
    list_display = ('title', 'library', 'photos_count')
    list_filter = ('library',)
    inlines = [PhotoInline]

    def photos_count(self, obj):
        return obj.photos.count()

    photos_count.short_description = _('Кол-во фото')

    def save_model(self, request, obj, form, change):
        # This actually persists album to DB (obj.pk is guaranteed after this)
        super().save_model(request, obj, form, change)

        zip_file = form.cleaned_data.get('zip_archive')
        if zip_file:
            self._create_photos_from_zip(obj, zip_file)

    def _create_photos_from_zip(self, album, zip_file):
        supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')

        with zipfile.ZipFile(zip_file) as zf:
            entries = []
            for info in zf.infolist():
                name = _decode_zip_filename(info)  # ← правильно декодированное имя
                if (
                        name.lower().endswith(supported_extensions)
                        and not name.startswith('__MACOSX')
                        and not os.path.basename(name).startswith('.')
                ):
                    entries.append((info, name))

            entries.sort(key=lambda x: x[1])

            photos_to_create = []
            for image_name, decoded_name  in entries:
                file_data = zf.read(image_name)
                clean_name = _sanitize_filename(os.path.basename(decoded_name))
                title = os.path.splitext(clean_name)[0]
                content_file = ContentFile(file_data, name=clean_name)

                photos_to_create.append(
                    Photo(
                        album=album,  # album is now saved and has a pk
                        image=content_file,
                        title=title,
                    )
                )

            if photos_to_create:
                Photo.objects.bulk_create(photos_to_create)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'position')
    list_filter = ('title', 'position')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'district_type')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'district')


@admin.register(Library)
class LibraryAdmin(NestedModelAdmin):
    list_display = ('name', 'city', 'get_projects')
    inlines = [ProjectInline, PhoneInline, EmailInline, LinksInline, CollapsibleBlockInline, ListBlockInline]

    @admin.display(description=_('Проекты'))
    def get_projects(self, obj):
        return ", ".join([str(project) for project in obj.projects.all()])
