# management/commands/load_districts_extended.py
from django.core.management.base import BaseCommand
from library.models import District, City
from django.db import transaction


class Command(BaseCommand):
    help = 'Расширенная загрузка округов с дополнительной информацией'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-sample-libraries',
            action='store_true',
            help='Создать тестовые библиотеки для округов'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Удалить все существующие округа и города перед загрузкой'
        )

    EXTENDED_DISTRICT_DATA = {
        'sampur': {
            'name': 'Сампурский муниципальный округ',
            'capital': 'посёлок Сампур',
            'cities': ['Сампур', 'Сатинка', 'Петровка'],
            'founded': 1928,
            'area_km2': 1274.5,
        },
        'zjerdevka': {
            'name': 'Жердевский муниципальный округ',
            'capital': 'город Жердевка',
            'cities': ['Жердевка', 'Алексеевка', 'Питим'],
            'founded': 1928,
            'area_km2': 1685.3,
        },
        'tokarevka': {
            'name': 'Токарёвский муниципальный округ',
            'capital': 'рабочий посёлок Токарёвка',
            'cities': ['Токарёвка', 'Абакумовка', 'Васильевка'],
            'founded': 1928,
            'area_km2': 1433.6,
        },
        'morhansk': {
            'name': 'Моршанский муниципальный округ',
            'capital': 'город Моршанск',
            'cities': ['Моршанск', 'Алгасово', 'Устье'],
            'founded': 1928,
            'area_km2': 2435.3,
        },
        'pichaevskiy': {
            'name': 'Пичаевский муниципальный округ',
            'capital': 'село Пичаево',
            'cities': ['Пичаево', 'Байловка', 'Липовка'],
            'founded': 1928,
            'area_km2': 1301.5,
        },
        'tmb+kotovsk': {
            'name': 'Тамбовский муниципальный округ',
            'capital': 'город Тамбов',
            'cities': ['Тамбов', 'Котовск', 'Строитель', 'Новая Ляда'],
            'founded': 1928,
            'area_km2': 2473.2,
        },
        'mordovskiy': {
            'name': 'Мордовский муниципальный округ',
            'capital': 'рабочий посёлок Мордово',
            'cities': ['Мордово', 'Шульгино', 'Лаврентьевка'],
            'founded': 1928,
            'area_km2': 1447.8,
        },
        'uvarovskiy': {
            'name': 'Уваровский муниципальный округ',
            'capital': 'город Уварово',
            'cities': ['Уварово', 'Нижний Шибряй', 'Берёзовка'],
            'founded': 1928,
            'area_km2': 1141.5,
        },
        'insgavino': {
            'name': 'Инжавинский муниципальный округ',
            'capital': 'рабочий посёлок Инжавино',
            'cities': ['Инжавино', 'Караул', 'Красивка'],
            'founded': 1928,
            'area_km2': 1851.3,
        },
        'raskasovo': {
            'name': 'Рассказовский муниципальный округ',
            'capital': 'город Рассказово',
            'cities': ['Рассказово', 'Платоновка', 'Рождественское'],
            'founded': 1928,
            'area_km2': 1723.8,
        },
        'rhaksa': {
            'name': 'Ржаксинский муниципальный округ',
            'capital': 'рабочий посёлок Ржакса',
            'cities': ['Ржакса', 'Каменка', 'Большая Ржакса'],
            'founded': 1928,
            'area_km2': 1430.8,
        },
        'znamenka': {
            'name': 'Знаменский муниципальный округ',
            'capital': 'рабочий посёлок Знаменка',
            'cities': ['Знаменка', 'Кариан', 'Сухотинка'],
            'founded': 1928,
            'area_km2': 1194.2,
        },
        'dmitrievka': {
            'name': 'Никифоровский муниципальный округ',
            'capital': 'рабочий посёлок Дмитриевка',
            'cities': ['Дмитриевка', 'Екатеринино', 'Ярославка'],
            'founded': 1928,
            'area_km2': 1378.3,
        },
        'petrovskiy': {
            'name': 'Петровский муниципальный округ',
            'capital': 'село Петровское',
            'cities': ['Петровское', 'Волчки', 'Шехмань'],
            'founded': 1928,
            'area_km2': 1761.5,
        },
        'michurinsk': {
            'name': 'Мичуринский муниципальный округ',
            'capital': 'город Мичуринск',
            'cities': ['Мичуринск', 'Заворонежское', 'Старое Тарбеево'],
            'founded': 1928,
            'area_km2': 1655.2,
        },
        'pervomayskiy': {
            'name': 'Первомайский муниципальный округ',
            'capital': 'рабочий посёлок Первомайский',
            'cities': ['Первомайский', 'Хоботово', 'Старокленское'],
            'founded': 1935,
            'area_km2': 947.5,
        },
        'sosnovka': {
            'name': 'Сосновский муниципальный округ',
            'capital': 'рабочий посёлок Сосновка',
            'cities': ['Сосновка', 'Вторые Левые Ламки', 'Кулеватово'],
            'founded': 1928,
            'area_km2': 2380.3,
        },
        'staroyrievskiy': {
            'name': 'Староюрьевский муниципальный округ',
            'capital': 'село Староюрьево',
            'cities': ['Староюрьево', 'Новиково', 'Большая Дорога'],
            'founded': 1928,
            'area_km2': 1076.5,
        },
        'bondari': {
            'name': 'Бондарский муниципальный округ',
            'capital': 'село Бондари',
            'cities': ['Бондари', 'Пахотный Угол', 'Митрополье'],
            'founded': 1928,
            'area_km2': 1253.8,
        },
        'gaveriloskiy': {
            'name': 'Гавриловский муниципальный округ',
            'capital': 'село Гавриловка 2-я',
            'cities': ['Гавриловка', 'Козьмодемьяновка', 'Чуповка'],
            'founded': 1928,
            'area_km2': 986.3,
        },
        'kirsanovskiy': {
            'name': 'Кирсановский муниципальный округ',
            'capital': 'город Кирсанов',
            'cities': ['Кирсанов', 'Иноковка', 'Уваровщина'],
            'founded': 1928,
            'area_km2': 1324.1,
        },
        'umetskiy': {
            'name': 'Умётский муниципальный округ',
            'capital': 'рабочий посёлок Умёт',
            'cities': ['Умёт', 'Бибиково', 'Оржевка'],
            'founded': 1935,
            'area_km2': 1126.5,
        },
        'mushkapskiy': {
            'name': 'Мучкапский муниципальный округ',
            'capital': 'рабочий посёлок Мучкапский',
            'cities': ['Мучкапский', 'Шапкино', 'Кулябовка'],
            'founded': 1928,
            'area_km2': 1190.8,
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

        for map_id, data in self.EXTENDED_DISTRICT_DATA.items():
            district, cities_created = self.create_extended_district(map_id, data)
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

    def create_extended_district(self, map_id, data):
        """Создает округ и связанные города"""
        try:
            # Очищаем название столицы от типа населенного пункта
            capital_name = data['capital']
            for prefix in ['город ', 'рабочий посёлок ', 'село ', 'посёлок ']:
                capital_name = capital_name.replace(prefix, '')

            # Сначала создаем временный округ (нужен для создания городов)
            district, district_created = District.objects.update_or_create(
                map_id=map_id,
                defaults={
                    'name': data['name'],
                    'capital': None,  # Временно None, обновим позже
                }
            )

            # Создаем все города, привязанные к этому округу
            cities_created = 0
            capital_city = None

            for city_name in data['cities']:
                city, city_created = City.objects.get_or_create(
                    name=city_name,
                    district=district,  # Сразу указываем округ
                )

                if city_created:
                    cities_created += 1
                    self.stdout.write(f'    + Город: {city_name}')

                # Запоминаем столицу
                if city_name == capital_name:
                    capital_city = city

            # Если столица не найдена в списке городов, создаем её отдельно
            if not capital_city:
                capital_city, city_created = City.objects.get_or_create(
                    name=capital_name,
                    district=district,
                )
                if city_created:
                    cities_created += 1
                    self.stdout.write(f'    + Столица: {capital_name}')

            # Обновляем округ, устанавливая столицу
            district.capital = capital_city
            district.save(update_fields=['capital'])

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