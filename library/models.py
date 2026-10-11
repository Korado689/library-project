from __future__ import annotations
import re
import uuid
from django.core.validators import FileExtensionValidator
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


    @property
    def count_all_libraries(self):
        return sum(city.libraries.count() for city in self.cities.all())

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
    end = filename.rfind('.')
    if end >= 0:
        end = filename[end:]
    else:
        end = ""
    return f"libraries/{instance.album.library.pk}/{instance.album.title}/{title}{end}"


def type_icon_upload_path(instance: LibraryType, filename: str) -> str:
    return f"map/{instance.uuid}/icons/{filename}"


class LibraryType(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    type = models.CharField(verbose_name=_("Type"), max_length=255)
    icon = models.FileField(verbose_name=_("Icon"), upload_to=type_icon_upload_path,
                            validators=[FileExtensionValidator(['png', 'webp', 'svg', 'jpg', 'jpeg'])])
    legend = models.TextField(verbose_name=_("Legend Text"))

    def __str__(self):
        return self.type


class Photo(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=255, null=True, blank=True)
    image = models.ImageField(verbose_name=_("Image"), upload_to=photo_upload_path)
    album = models.ForeignKey(PhotoAlbum, on_delete=models.CASCADE, related_name='photos')

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return f"{self.album.title}: Photo {self.id}"


def lib_upload_path(instance: Library, filename: str) -> str:
    end = filename.rfind('.')
    if end >= 0:
        end = filename[end:]
    else:
        end = ""
    return f"libraries/{instance.pk}/main-photo{end}"


def design_upload_path(instance: Library, filename: str) -> str:
    end = filename.rfind('.')
    if end >= 0:
        end = filename[end:]
    else:
        end = ""
    return f"libraries/{instance.pk}/design-project{end}"


class Library(models.Model):
    type = models.ForeignKey(LibraryType, verbose_name=_("Type"), on_delete=models.PROTECT)
    projects = models.ManyToManyField(Project, through='ProjectLibraryMembership', related_name='libraries')
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='libraries')

    image = models.ImageField(verbose_name=_("Image"), upload_to=lib_upload_path, blank=True, null=True)
    name = models.TextField(verbose_name=_("Library name"))
    short_name = models.CharField(verbose_name=_("Library short name"), max_length=255, null=True, blank=True)
    status = models.TextField(verbose_name=_("Status"))
    creative = models.TextField(verbose_name=_("Creative Industry"), blank=True, null=True)
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

from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage

def _delete_file(field_file):
    """Удаляет файл из storage, если он существует."""
    if field_file and default_storage.exists(field_file.name):
        default_storage.delete(field_file.name)


@receiver(pre_save, sender=Photo)
def delete_image_icon_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # новый объект — удалять нечего

    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_file = old.image
    new_file = instance.image

    # файл заменили или очистили
    if old_file and old_file.name != getattr(new_file, "name", None):
        _delete_file(old_file)


@receiver(post_delete, sender=Photo)
def delete_image_on_delete(sender, instance, **kwargs):
    _delete_file(instance.image)



@receiver(pre_save, sender=LibraryType)
def delete_old_icon_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # новый объект — удалять нечего

    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_file = old.icon
    new_file = instance.icon

    # файл заменили или очистили
    if old_file and old_file.name != getattr(new_file, "name", None):
        _delete_file(old_file)


@receiver(post_delete, sender=LibraryType)
def delete_icon_on_delete(sender, instance, **kwargs):
    _delete_file(instance.icon)


@receiver(pre_save, sender=Library)
def delete_old_icon_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # новый объект — удалять нечего

    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_file = old.image
    new_file = instance.image

    # файл заменили или очистили
    if old_file and old_file.name != getattr(new_file, "name", None):
        _delete_file(old_file)


    old_file = old.design_project
    new_file = instance.design_project

    # файл заменили или очистили
    if old_file and old_file.name != getattr(new_file, "name", None):
        _delete_file(old_file)

@receiver(post_delete, sender=Library)
def delete_icon_on_delete(sender, instance, **kwargs):
    _delete_file(instance.icon)