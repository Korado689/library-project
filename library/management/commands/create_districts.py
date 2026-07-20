# management/commands/load_districts_extended.py
from django.core.management.base import BaseCommand
from library.models import District, City, DistrictType
from django.db import transaction


class Command(BaseCommand):
    help = 'Расширенная загрузка округов с дополнительной информацией'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Удалить все существующие округа и города перед загрузкой'
        )

    EXTENDED_CITY_DATA = {

        'city-kirsanovskiy': {
            'name': 'Кирсанов',
            'cities': ['Кирсанов'],
        },
        'city-kotovsk': {
            'name': 'Котовск',
            'cities': ['Котовск'],
        },
        'city-michurinsk': {
            'name': 'Мичуринск',
            'cities': ['Мичуринск'],
        },
        'city-morhansk': {
            'name': 'Моршанск',
            'cities': ['Моршанск'],
        },
        'city-raskasovo': {
            'name': 'Рассказово ',
            'cities': ['Рассказово'],
        },
        'city-tambov': {
            'name': 'Тамбов',
            'cities': ['Тамбов'],
        },
        'city-uvarovskiy': {
            'name': 'Уварово ',
            'cities': ['Уварово'],
        },
    }

    EXTENDED_DISTRICT_DATA = {
        'region-bondari': {
            'name': 'Бондарский ',
            'cities': ['село Бондари'],
        },
        'region-gavriloskiy': {
            'name': 'Гавриловский ',
            'cities': ['село Гавриловка'],
        },
        'region-zjerdevka': {
            'name': 'Жердевский',
            'cities': ['Жердевка'],
        },
        'region-znamenka': {
            'name': 'Знаменский ',
            'cities': ['рабочий поселок Знаменка'],
        },
        'region-insgavino': {
            'name': 'Инжавинский ',
            'cities': ['рабочий поселок Инжавино'],
        },
        'region-kirsanovskiy': {
            'name': 'Кирсановский ',
            'cities': ['село Голынщина', ],
        },
        'region-michurinsk': {
            'name': 'Мичуринский',
            'cities': ['село Заворонежское'],
        },
        'region-mordovskiy': {
            'name': 'Мордовский',
            'cities': ['рабочий поселок Мордово'],
        },
        'region-morhansk': {
            'name': 'Моршанский',
            'cities': ['село Устье'],
        },
        'region-mushkapskiy': {
            'name': 'Мучкапский ',
            'cities': ['Мучкапский рабочий поселок'],
        },
        'region-dmitrievka': {
            'name': 'Никифоровский ',
            'cities': ['рабочий поселок Дмитриевка'],
        },
        'region-pervomayskiy': {
            'name': 'Первомайский ',
            'cities': ['поселок Первомайский'],
        },
        'region-petrovskiy': {
            'name': 'Петровский ',
            'cities': ['село Петровское'],
        },
        'region-pichaevskiy': {
            'name': 'Пичаевский',
            'cities': ['село Пичаево'],
        },
        'region-raskasovo': {
            'name': 'Рассказовский ',
            'cities': ['село Платоновка'],
        },
        'region-rhaksa': {
            'name': 'Ржаксинский ',
            'cities': ['рабочий поселок Ржакса'],
        },
        'region-sampur': {
            'name': 'Сампурский',
            'cities': ['село Сампур', 'поселок Сатинка'],
        },
        'region-sosnovka': {
            'name': 'Сосновский ',
            'cities': ['поселок Сосновка'],
        },
        'region-staroyrievskiy': {
            'name': 'Староюрьевский ',
            'cities': ['село Староюрьево'],
        },
        'region-tmb+kotovsk': {
            'name': 'Тамбовский',
            'cities': ['село Авдеевка'],
        },
        'region-tokarevka': {
            'name': 'Токарёвский',
            'cities': ['рабочий поселок Токарёвка'],
        },
        'region-uvarovskiy': {
            'name': 'Уваровский ',
            'cities': ['село Подгорное'],
        },
        'region-umetskiy': {
            'name': 'Умётский ',
            'cities': ['рабочий поселок Умёт', ],
        },
    }

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear_existing']:
            confirm = input(
                'Вы уверены, что хотите удалить ВСЕ округа и города? [y/N]: '
            )
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Операция отменена'))
                return

            # Удаляем в правильном порядке из-за связей
            City.objects.all().delete()
            District.objects.all().delete()
            self.stdout.write(self.style.WARNING('Все округа и города удалены'))

        total_districts = 0
        total_cities = 0
        _types = DistrictType.values
        dists = (self.EXTENDED_DISTRICT_DATA, self.EXTENDED_CITY_DATA)
        for _type, d in zip(_types, dists):
            for map_id, data in d.items():
                district, cities_created = self.create_extended_district(map_id, data, _type)
                if district:
                    total_districts += 1
                    total_cities += cities_created

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'✓ Создано/обновлено округов: {total_districts}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✓ Создано городов: {total_cities}')
        )

    def create_extended_district(self, map_id, data, _type):
        """Создает округ и связанные города"""
        try:

            # Сначала создаем временный округ (нужен для создания городов)
            district, district_created = District.objects.update_or_create(
                map_id=map_id,
                defaults={
                    'name': data['name'],
                    'district_type': _type
                }
            )

            # Создаем все города, привязанные к этому округу
            cities_created = 0

            for city_name in data['cities']:
                city, city_created = City.objects.get_or_create(
                    name=city_name,
                    district=district,  # Сразу указываем округ
                )

                if city_created:
                    cities_created += 1
                    self.stdout.write(f'    + Город: {city_name}')


            # Выводим информацию
            if district_created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {data["name"]} (map_id: {map_id})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'↻ Обновлен: {data["name"]} (map_id: {map_id})'
                    )
                )
            self.stdout.write(f'    Всего городов: {len(data["cities"])}')

            return district, cities_created

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'✗ Ошибка при создании {data.get("name", map_id)}: {e}'
                )
            )
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            return None, 0
