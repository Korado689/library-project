import os
import zipfile

from django.core.files.base import ContentFile
from django.db import models


class Settlement(models.Model):
    """Населённый пункт внутри района"""
    district = models.ForeignKey(
        "District",
        on_delete=models.CASCADE,
        related_name='settlements',
        verbose_name="Район"
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    is_main = models.BooleanField(
        default=False,
        verbose_name="Главный город района"
    )

    class Meta:
        verbose_name = "Населённый пункт"
        verbose_name_plural = "Населённые пункты"
        unique_together = ['district', 'name']
        ordering = ['-is_main', 'name']  # Главный город первым

    def __str__(self):
        return f"{self.name} ({self.district.name})"

    def save(self, *args, **kwargs):
        # Сначала сохраняем сам settlement
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Если это главный город
        if self.is_main:
            # Убираем is_main у других пунктов этого района
            Settlement.objects.filter(
                district=self.district,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)

            # Обновляем main_settlement у района
            if self.district.main_settlement_id != self.pk:
                District.objects.filter(pk=self.district_id).update(main_settlement=self)

        # Если убрали is_main
        elif not self.is_main:
            if self.district.main_settlement_id == self.pk:
                District.objects.filter(pk=self.district_id).update(main_settlement=None)


class District(models.Model):
    """Муниципальный округ/район"""
    name = models.CharField(max_length=150, verbose_name="Название")

    main_settlement = models.ForeignKey(
        Settlement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='main_for_district',
        verbose_name="Главный город"
    )
    # Привязка к SVG
    svg_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="ID региона в SVG",
    )

    class Meta:
        verbose_name = "Муниципальный округ"
        verbose_name_plural = "Муниципальные округа"
        unique_together = ['name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class Project(models.Model):
    photo = models.ImageField(upload_to='projects/', blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return f"Проект: {self.name}"


class ProjectFieldTemplate(models.Model):
    """
    Определяет название будущего поля для конкретного проекта.
    Сами значения будут заполняться позже в ProjectFieldValue.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='field_templates'
    )
    field_name = models.CharField(max_length=255)


    def __str__(self):
        return f"{self.project.name} — {self.field_name}"

class LibraryType(models.Model):
    name = models.CharField(verbose_name='Тип библиотеки', max_length=255)
    logo = models.ImageField(upload_to='library-logo/', blank=True)

    def __str__(self):
        return f"{self.name}"

    # MODEL = 'model', 'Модельная библиотека'
    # GENIUS_LAB = 'genius_lab', 'Модельная библиотека с творческой лабораторией \"Гений места\"'
    # GENIUS = 'genius', 'Творческая лаборатория \"Гений места\"'
    # CHILDREN = 'children', 'Детский центр'


class ContactsType(models.TextChoices):
    PHONE = 'phone', 'Телефон'
    EMAIL = 'email', 'Электронная почта'
    WEBSITE = 'website', 'Веб-сайт'
    SOCIALMEDIA = 'socialmedia', 'Соц-сети'


class Contacts(models.Model):
    type = models.CharField(verbose_name="Вид контакта", max_length=255, choices=ContactsType.choices)
    value = models.TextField(verbose_name="Значение контакта")
    description = models.TextField(verbose_name="Подпись контакта")

    def __str__(self):

        type_:str = self.type
        if type_ == ContactsType.WEBSITE or type_ == ContactsType.SOCIALMEDIA:
            return f"{self.get_type_display()}: {self.value[:self.value.find('/',10)]} ({self.description})"
        return f"{self.get_type_display()}: {self.value} ({self.description})"






class Library(models.Model):
    """Библиотека"""

    library_type = models.ForeignKey(LibraryType, on_delete=models.PROTECT, verbose_name='Тип библиотеки')
    projects = models.ManyToManyField(Project)
    photo = models.ImageField(upload_to='libraries/main-photo/', blank=True)
    name = models.CharField(verbose_name='Название библиотеки', max_length=255)
    status = models.CharField(verbose_name='Статус', blank=True, null=True, max_length=255)
    area = models.FloatField(verbose_name="Площадь (кв. м)", blank=True, null=True)
    address = models.TextField(verbose_name='Адрес')
    working_hours = models.TextField(verbose_name='Рабочие часы', blank=True, null=True)
    contacts = models.ManyToManyField(Contacts)

    district = models.ForeignKey(District, verbose_name='Округ', on_delete=models.PROTECT, related_name='libraries')
    settlement = models.ForeignKey(Settlement, verbose_name='Населённый пункт', on_delete=models.PROTECT,
                                   blank=True, null=True, related_name='libraries')

    class Meta:
        verbose_name = "Библиотека"
        verbose_name_plural = "Библиотеки"

    def __str__(self):
        return self.name

    @property
    def marker_icon(self):
        """Возвращает путь к иконке маркера"""
        icons = {
            'model': 'images/map/icons/model-library.svg',
            'genius_lab': 'images/map/icons/genius-lab.svg',
            'genius': 'images/map/icons/genius.svg',
            'children': 'images/map/icons/children-center.svg',
        }

        if self.library_type and self.library_type.logo:
            return self.library_type.logo.url
        return 'images/map/icons/model-library.svg'


class ProjectFieldValue(models.Model):
    template = models.ForeignKey(
        ProjectFieldTemplate,
        on_delete=models.CASCADE,
        related_name='values'
    )
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='project_field_values',
        verbose_name="Библиотека",
    )
    value = models.TextField()  # Универсальное текстовое поле для хранения данных

    class Meta:
        unique_together = (('template', 'library'),)


class LibraryBlock(models.Model):
    """
    Универсальный текстовый блок на странице библиотеки.
    Может содержать историю, концепцию, описание зон и т.д.
    """

    class BlockType(models.TextChoices):
        FILE = 'file', 'Блок с файлом'
        VIDEO = 'video', 'Видеовизитка'
        PHOTOALBUM = 'photoalbum', 'Фотоальбом'
        INFO = 'info', 'Информационный блок'
        LIST = 'list', 'Список'

    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='blocks'
    )
    block_type = models.CharField(
        max_length=30,
        choices=BlockType.choices,
        verbose_name="Тип блока"
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Заголовок блока"
    )
    is_visible = models.BooleanField(default=True, verbose_name='Отображать')

    # Поля для info_block
    text = models.TextField(blank=True, null=True, verbose_name='Текст')

    # Поля для file
    pdf_file = models.FileField(
        upload_to='library/files/',
        blank=True,
        null=True,
        verbose_name='PDF файл'
    )

    # Поля для video
    video_description = models.TextField(blank=True, null=True, verbose_name='Описание видео')
    video_url = models.URLField(blank=True, null=True, verbose_name='Ссылка на видео')

    # Поля для photo_album
    album_description = models.TextField(blank=True, null=True, verbose_name='Описание альбома')


    zip_archive = models.FileField(
        upload_to='library/temp_zips/',
        blank=True,
        null=True,
        verbose_name='ZIP архив с фотографиями',
        help_text='Загрузите ZIP-архив с фотографиями. Они будут автоматически распакованы.'
    )


    class Meta:
        verbose_name = 'Секция'
        verbose_name_plural = 'Секции'

    def __str__(self):
        return f"{self.library.name} — {self.title} [{self.get_block_type_display()}]"

    def extract_photos_from_zip(self):
        """Распаковывает ZIP-архив и создаёт объекты Photo"""
        if not self.zip_archive:
            return 0

        created = 0
        try:
            with zipfile.ZipFile(self.zip_archive.path, 'r') as zip_ref:
                for filename in zip_ref.namelist():
                    # Пропускаем папки и скрытые файлы
                    if filename.endswith('/') or os.path.basename(filename).startswith('.'):
                        continue

                    # Проверяем расширение
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                        continue

                    # Читаем файл из архива
                    file_data = zip_ref.read(filename)

                    # Создаём объект Photo
                    photo = Photo(
                        block=self,
                        caption=os.path.splitext(os.path.basename(filename))[0]
                    )

                    # Сохраняем изображение
                    photo.image.save(
                        os.path.basename(filename),
                        ContentFile(file_data),
                        save=False
                    )
                    photo.save()
                    created += 1

        except (zipfile.BadZipFile, FileNotFoundError) as e:
            # Можно залогировать ошибку
            pass

        # Удаляем архив после распаковки
        if self.zip_archive:
            self.zip_archive.delete(save=False)
            self.zip_archive = None

        return created

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Распаковываем архив после сохранения
        if self.block_type == 'photoalbum' and self.zip_archive:
            self.extract_photos_from_zip()
            # Сохраняем ещё раз, чтобы убрать ссылку на архив
            super().save(update_fields=['zip_archive'])

    def clean(self):
        from django.core.exceptions import ValidationError

        type_required_fields = {
            'info': ['text'],
            'file': ['pdf_file'],
            'video': ['video_url'],
        }

        required = type_required_fields.get(self.block_type, [])
        for field in required:
            if not getattr(self, field):
                raise ValidationError({
                    field: f'Это поле обязательно для типа «{self.get_block_type_display()}»'
                })

        # Очищаем поля, не относящиеся к типу
        all_fields = {'text', 'pdf_file', 'video_description', 'video_url', 'album_description'}
        keep_fields = set(required)
        if self.block_type == 'video':
            keep_fields.add('video_description')
        if self.block_type == 'photo_album':
            keep_fields.add('album_description')

        for field in all_fields - keep_fields:
            setattr(self, field, None)


class ListItem(models.Model):
    """Элемент списка для секции типа 'list'"""
    block = models.ForeignKey(
        LibraryBlock,
        on_delete=models.CASCADE,
        related_name='list_items'
    )
    text = models.TextField(verbose_name='Текст элемента')
    class Meta:
        verbose_name = 'Элемент списка'
        verbose_name_plural = 'Элементы списка'

    def __str__(self):
        return self.text[:50]


# class PhotoAlbum(models.Model):
#     """Фотоальбомы (до/после модернизации)"""
#
#     library = models.ForeignKey(
#         Library,
#         on_delete=models.CASCADE,
#         related_name='photo_albums'
#     )
#     title = models.CharField(max_length=200, verbose_name="Название альбома")
#
#     class Meta:
#         verbose_name = "Фотоальбом"
#         verbose_name_plural = "Фотоальбомы"
#
#     def __str__(self):
#         return f"{self.title} ({self.library.name})"


class Photo(models.Model):
    """Фотографии в альбомах"""
    block = models.ForeignKey(
        LibraryBlock,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Блок"
    )
    image = models.ImageField(
        upload_to='libraries/photos/',
        verbose_name="Фотография"
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Подпись"
    )

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"

    def __str__(self):
        return f"Фото: {self.caption}"

class Her(models.Model):
    pass