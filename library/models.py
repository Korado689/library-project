from django.db import models


class Coordinators(models.Model):
    photo = models.ImageField(upload_to='projects/', blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100)

    def __str__(self):
        return f"Координаторы: {self.name}"


class Project(models.Model):
    # coordinator = models.ForeignKey(Coordinators, on_delete=models.CASCADE, related_name='projects')
    photo = models.ImageField(upload_to='projects/', blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return f"Проект: {self.name}"


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


class LibraryType(models.TextChoices):
    MODEL = 'model', 'Модельная библиотека'
    GENIUS_LAB = 'genius_lab', 'Модельная + Гений места'
    GENIUS = 'genius', 'Творческая лаборатория Гений места'
    CHILDREN = 'children', 'Детский центр'


class Library(models.Model):
    """Библиотека"""
    photo = models.ImageField(upload_to='libraries/', blank=True)
    name = models.CharField(verbose_name='Название', max_length=200)

    library_type = models.CharField(verbose_name='Тип библиотеки', max_length=20, choices=LibraryType.choices)
    district = models.ForeignKey(District, verbose_name='Округ', on_delete=models.CASCADE, related_name='libraries')

    status = models.CharField(verbose_name='Статус', max_length=300)
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
    settlement = models.ForeignKey(
        Settlement,
        verbose_name='Населённый пункт',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='libraries'
    )
    address = models.CharField(verbose_name='Адрес', max_length=300)

    working_hours = models.TextField(verbose_name='Рабочие часы', blank=True)

    phone = models.CharField(verbose_name='Телефон', max_length=200, blank=True)
    phone_owner = models.CharField(verbose_name='Владелец телефона', max_length=200, blank=True)

    email = models.CharField(verbose_name='Почта', max_length=200, blank=True)

    pdf_file = models.FileField(
        upload_to='libraries/design_projects/',
        verbose_name="PDF файл", blank=True
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


class LibraryBlock(models.Model):
    """
    Универсальный текстовый блок на странице библиотеки.
    Может содержать историю, концепцию, описание зон и т.д.
    """

    class BlockType(models.TextChoices):
        PROJECT = 'project', 'Включена в проект'
        DIRECTION = 'direction', 'Направление в сфере'
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
    # Год (только для проектов)
    year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Год",
        help_text="Год включения в проект"
    )
    content = models.TextField(
        verbose_name="Содержание",
        help_text="Основной текст блока. Используй Markdown для форматирования (списки, жирный, ссылки)"
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Порядок отображения"
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name="Отображать на сайте"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Текстовый блок"
        verbose_name_plural = "Текстовые блоки"
        ordering = ['order', 'created_at']  # Один тип блока на библиотеку

    def __str__(self):
        return f"{self.get_block_type_display()}: {self.library.name}"

    def get_title(self):
        """Возвращает заголовок: пользовательский или стандартный"""
        return self.title or self.get_block_type_display()

    def get_items(self):
        """Разбивает content на список (для типа LIST)"""
        if self.block_type == self.BlockType.LIST and self.content:
            return [line.strip() for line in self.content.strip().split('\n') if line.strip()]
        return []


class WebSite(models.Model):
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='website'
    )

    url = models.URLField(verbose_name="Ссылка")

    class Meta:
        verbose_name = "Веб-сайт / Соцсети"
        verbose_name_plural = "Веб-сайт / Соцсети"

    def __str__(self):
        return self.url


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
