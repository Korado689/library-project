from __future__ import annotations
import re

from django.db import models
from djangoyearlessdate.models import YearField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _


def project_upload_path(instance: Project, filename: str) -> str:
    return f"projects/{instance.pk}/{instance.title}-{filename}"


class Project(models.Model):
    title = models.CharField(verbose_name=_("Title of project"), max_length=100, null=True, blank=True)
    image = models.ImageField(verbose_name=_("Image"), upload_to=project_upload_path)
    description = models.TextField(verbose_name=_("Description of project"))
    lib_desc = models.TextField(verbose_name=_("Description showing in library"))
    position = models.PositiveIntegerField(verbose_name=_("Position on page"), )
    text_split = models.BooleanField(verbose_name=_("Horizontal view"), default=False)
    url = models.URLField(verbose_name=_("URL"), null=True, blank=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return super(Project, self).__str__()


class DistrictType(models.TextChoices):
    MUNICIPAL = 'municipal', _('муниципальный округ')
    URBAN = 'urban', _('городской округ')


class District(models.Model):
    name = models.CharField(verbose_name=_("District name"), max_length=255)
    map_id = models.CharField(verbose_name=_("Map ID"), max_length=255, null=True, blank=True)

    district_type = models.CharField(
        verbose_name=_("Тип округа"),
        max_length=20,
        choices=DistrictType.choices,
        default=DistrictType.MUNICIPAL
    )

    def _count_by_type(self, lib_type=None):
        if lib_type:
            return sum(city.libraries.filter(type=lib_type).count() for city in self.cities.all())
        return sum(city.libraries.count() for city in self.cities.all())

    @property
    def count_all_libraries(self):
        return self._count_by_type()

    @property
    def count_model_lib(self):
        return self._count_by_type('model_lib')

    @property
    def count_model_gen(self):
        return self._count_by_type('model_gen')

    @property
    def count_gen_lab(self):
        return self._count_by_type('gen_lab')

    @property
    def count_child_center(self):
        return self._count_by_type('child_center')

    @property
    def full_display_name(self):
        if self.district_type == DistrictType.URBAN:
            return f"Городской округ {self.name}"
        return f"{self.name} муниципальный округ"

    @property
    def clean_sub_title(self):
        return self.full_display_name

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(verbose_name=_("City name"), max_length=255)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='cities')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Phone(models.Model):
    number = PhoneNumberField(_("Phone"))
    owner = models.CharField(verbose_name=_("Owner"), max_length=255, null=True, blank=True)
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='phones')

    def __str__(self):
        return str(self.number)

    @property
    def formatted_number(self):
        cleaned = re.sub(r'[^\d+]', '', str(self.number))
        pattern = r'^(\+?\d{1})(\d{3})(\d{3})(\d{2})(\d{2})$'
        match = re.match(pattern, cleaned)

        if match:
            return f"{match.group(1)}({match.group(2)}){match.group(3)}-{match.group(4)}-{match.group(5)}"

        return self.number


class Email(models.Model):
    email = models.EmailField(verbose_name=_("Email"), max_length=255)
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='emails')

    def __str__(self):
        return self.email


class Links(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=255)
    url = models.URLField(verbose_name=_("URL"))
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='links')

    def __str__(self):
        return self.title


class CollapsibleBlock(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=255)
    text = models.TextField(verbose_name=_("Text"))
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='collapsible_blocks')

    def __str__(self):
        name = self.library.short_name if self.library.short_name else self.library.name
        return f"{name}: {self.title}"


class ListBlock(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=255)
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='list_blocks')

    def __str__(self):
        name = self.library.short_name if self.library.short_name else self.library.name
        return f"{name}: {self.title}"


class ListElement(models.Model):
    text = models.TextField(verbose_name=_("Text"))
    block = models.ForeignKey('ListBlock', on_delete=models.CASCADE, related_name='elements')

    def __str__(self):
        return f"{self.block.title}: ListElement {self.id}"


class PhotoAlbum(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=255)
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='albums')


def photo_upload_path(instance: Photo, filename: str) -> str:
    if hasattr(instance, 'title') and instance.title is not None:
        title = instance.title
    else:
        title = filename
    return f"libraries/{instance.album.library.pk}/{instance.album.title}/{title}"


class Photo(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=255, null=True, blank=True)
    image = models.ImageField(verbose_name=_("Image"), upload_to=photo_upload_path)
    album = models.ForeignKey(PhotoAlbum, on_delete=models.CASCADE, related_name='photos')

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return f"{self.album.title}: Photo {self.id}"


class LibraryType(models.TextChoices):
    MODEL_LIB = 'model_lib', _('Model library')
    MODEL_GEN = 'model_gen', _('Model library with Genius Place')
    GEN_LAB = 'gen_lab', _('Genius Place')
    CHILD = 'child_center', _('Children center')


def lib_upload_path(instance: Library, filename: str) -> str:
    return f"libraries/{instance.pk}/main-photo"


def design_upload_path(instance: Library, filename: str) -> str:
    return f"libraries/{instance.pk}/design-project"


class Library(models.Model):
    type = models.CharField(verbose_name=_("Type"), max_length=255, choices=LibraryType.choices, blank=True, null=True)
    projects = models.ManyToManyField(Project, through='ProjectLibraryMembership', related_name='libraries')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='libraries')

    image = models.ImageField(verbose_name=_("Image"), upload_to=lib_upload_path, blank=True, null=True)
    name = models.TextField(verbose_name=_("Library name"))
    short_name = models.CharField(verbose_name=_("Library short name"), max_length=255, null=True, blank=True)
    status = models.TextField(verbose_name=_("Status"))
    address = models.TextField(verbose_name=_("Address"), blank=True, null=True)

    area = models.CharField(verbose_name=_("Area"), max_length=255)
    schedule = models.TextField(verbose_name=_("Work Schedule"), max_length=255)

    design_project = models.FileField(verbose_name=_("Design project"), upload_to=design_upload_path, null=True,
                                      blank=True)
    video = models.URLField(verbose_name=_("Video URL"), null=True, blank=True)
    video_desc = models.TextField(verbose_name=_("Video description"), null=True, blank=True)

    def __str__(self):
        return self.short_name if self.short_name else self.name


class ProjectLibraryMembership(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.CASCADE)
    date_linked = YearField(verbose_name=_("Date linked"))

    class Meta:
        unique_together = ['project', 'library']
