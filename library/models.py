from enum import Enum

from django.db import models


class Coordinators(models.Model):
    photo = models.ImageField(upload_to='projects/', blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100)

    def __str__(self):
        return f"Координаторы: {self.name}"


class Project(models.Model):
    coordinator = models.ForeignKey(Coordinators, on_delete=models.CASCADE, related_name='projects')
    photo = models.ImageField(upload_to='projects/', blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100)

    def __str__(self):
        return f"Проект: {self.name}"


class Region(models.Choices):
    pass

# Create your models here.

class District(models.Model):
    """Муниципальный округ/район"""
    name = models.CharField(max_length=150, verbose_name="Название")
    # Привязка к SVG
    svg_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="ID региона в SVG",
        help_text="Например: zjerdevka, michurinsk"
    )

    class Meta:
        verbose_name = "Муниципальный округ"
        verbose_name_plural = "Муниципальные округа"
        unique_together = ['name', 'region']
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class LibraryType(models.TextChoices):
    MODEL = 'model', 'Модельная библиотека'
    GENIUS_LAB = 'genius_lab', 'Модельная + Гений места'
    GENIUS = 'genius', 'Творческая лаборатория Гений места'
    CHILDREN = 'children', 'Детский центр'


class Library(models.Model):
    """Библиотека"""
    photo = models.ImageField(upload_to='libraries/', blank=True)
    name = models.CharField(max_length=200)

    library_type = models.CharField(max_length=20, choices=LibraryType)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='libraries')

    status = models.CharField(max_length=300)
    area = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Площадь (кв. м)"
    )
    modernization_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Год модернизации"
    )
    address = models.CharField(max_length=300)

    working_hours = models.TextField(blank=True)

    phone = models.CharField(max_length=20, blank=True)
    phone_owner = models.CharField(max_length=200, blank=True)

    email = models.EmailField(blank=True)

    history = models.TextField(verbose_name="Текст истории")

    pdf_file = models.FileField(
        upload_to='libraries/design_projects/',
        verbose_name="PDF файл"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        return icons.get(self.library_type, 'images/map/icons/model-library.svg')

class WebSite(models.Model):
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='website'
    )

    url = models.URLField(verbose_name="Ссылка")

    class Meta:
        verbose_name = "Веб-сайт / Соцсети"

    def __str__(self):
        return self.url


class Zone(models.Model):
    """Зоны пространства библиотеки"""
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='zones'
    )
    name = models.CharField(max_length=200, verbose_name="Название зоны")
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Порядок сортировки"
    )

    class Meta:
        verbose_name = "Зона пространства"
        verbose_name_plural = "Зоны пространства"
        ordering = ['order']
        unique_together = ['library', 'name']

    def __str__(self):
        return f"{self.name} ({self.library.name})"


class Technology(models.Model):
    """Технологии и оборудование"""
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='technologies'
    )
    name = models.CharField(max_length=200, verbose_name="Название")

    class Meta:
        verbose_name = "Технология/оборудование"
        verbose_name_plural = "Технологии и оборудование"

    def __str__(self):
        return f"{self.name} ({self.library.name})"


class PhotoAlbum(models.Model):
    """Фотоальбомы (до/после модернизации)"""

    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='photo_albums'
    )
    title = models.CharField(max_length=200, verbose_name="Название альбома")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фотоальбом"
        verbose_name_plural = "Фотоальбомы"

    def __str__(self):
        return f"{self.title} ({self.library.name})"


class Photo(models.Model):
    """Фотографии в альбомах"""
    album = models.ForeignKey(
        PhotoAlbum,
        on_delete=models.CASCADE,
        related_name='photos'
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


class VideoBusinessCard(models.Model):
    """Видеовизитка библиотеки"""
    library = models.OneToOneField(
        Library,
        on_delete=models.CASCADE,
        related_name='video_business_card',
        verbose_name="Библиотека"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание видео"
    )

    # Или ссылка на внешний видеохостинг
    video_url = models.URLField(
        blank=True,
        verbose_name="Ссылка на видео",
        help_text="Ссылка на YouTube, VK Видео, Rutube и др."
    )

    # Превью для видео
    thumbnail = models.ImageField(
        upload_to='libraries/videos/thumbnails/',
        blank=True,
        null=True,
        verbose_name="Превью видео"
    )

    class Meta:
        verbose_name = "Видеовизитка"
        verbose_name_plural = "Видеовизитки"

    def __str__(self):
        return f"Видеовизитка: {self.library.name}"
