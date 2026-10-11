const TYPE_FIELDS = {
    info:       ['text'],
    file:       ['pdf_file'],
    video:      ['video_description', 'video_url'],
    photoalbum: ['album_description', 'zip_archive'],
    list:       [],
};

const ALL_MANAGED_FIELDS = ['text', 'pdf_file',
    'video_description', 'video_url', 'album_description', 'zip_archive'];

function buildFieldId(selectName, fieldName) {
    if (selectName === 'block_type') {
        return 'id_' + fieldName;
    }
    const prefix = selectName.slice(0, selectName.lastIndexOf('-block_type'));
    return 'id_' + prefix + '-' + fieldName;
}

function getFieldRow($, fieldId) {
    const $el = $('#' + CSS.escape(fieldId));
    if (!$el.length) return $();
    return $el.closest('.form-row, .fieldBox, tr');
}

function applyVisibility($, $select) {
    const blockType = $select.val();
    const selectName = $select.attr('name') || '';
    const visibleFields = TYPE_FIELDS[blockType] || [];

    ALL_MANAGED_FIELDS.forEach(function (fieldName) {
        const fieldId = buildFieldId(selectName, fieldName);
        const $row = getFieldRow($, fieldId);
        if (!$row.length) return;
        $row.toggle(visibleFields.includes(fieldName));
    });

    if (!$select.closest('.inline-related').length) {
        toggleStandaloneInlines($, blockType);
    }
}

function toggleStandaloneInlines($, blockType) {
    $('.inline-group').each(function () {
        const $g = $(this);
        const id = ($g.attr('id') || '').toLowerCase();
        const h2 = $g.find('h2').text().toLowerCase();

        if (id.includes('listitem') || h2.includes('список') || h2.includes('элемент')) {
            $g.toggle(blockType === 'list');
        }
        if (id.includes('photo') || h2.includes('фото')) {
            $g.toggle(blockType === 'photoalbum');
        }
    });
}

function initSelect($, $select) {
    if ($select.data('lb-ready')) return;
    $select.data('lb-ready', true);
    applyVisibility($, $select);
    $select.on('change', function () {
        applyVisibility($, $(this));
    });
}

function initAll($) {
    $('select[name="block_type"], select[name$="-block_type"]').each(function () {
        if ($(this).attr('name').includes('__prefix__')) return;
        if ($(this).closest('[id*="__prefix__"]').length) return;
        initSelect($, $(this));
    });
}

function initProjectFieldsToggle($) {
    const $fieldInline = $('.inline-group').filter(function() {
        const h2 = $(this).find('h2').text();
        return h2.includes('Доп. поля проектов');
    });

    if (!$fieldInline.length) return;

    function toggleProjectFields() {
        // filter_horizontal: выбранные проекты в правом списке
        const $toSelect = $('#id_projects_to');
        // Обычный select multiple (запасной вариант)
        const $fromSelect = $('#id_projects_from, #id_projects');

        let selectedCount = 0;

        if ($toSelect.length) {
            selectedCount = $toSelect.find('option').length;
        } else if ($fromSelect.length) {
            selectedCount = $fromSelect.find('option:selected').length;
        }

        $fieldInline.toggle(selectedCount > 0);
    }

    toggleProjectFields();

    // Для обычного select multiple
    $(document).on('change', '#id_projects_from, #id_projects', toggleProjectFields);

    // Для filter_horizontal
    $(document).on('click', '.selector-chooser .add, .selector-chooser .remove', function() {
        setTimeout(toggleProjectFields, 100);
    });
}

function waitForDjangoJQuery() {
    if (typeof django !== 'undefined' && django.jQuery) {
        const $ = django.jQuery;

        $(document).ready(function () {
            initAll($);
            initProjectFieldsToggle($);

            // formset:added — в разных версиях Django $row может быть jQuery или Event
            // Используем document-level делегирование через нативный CustomEvent
            document.addEventListener('formset:added', function (event) {
                // Django 4.x передаёт строку как event.detail.formsetName и строку как второй аргумент
                // Сама новая строка — это event.target
                const row = event.target || event.detail;
                if (!row) return;
                $(row).find('select[name$="-block_type"]').each(function () {
                    if (!$(this).attr('name').includes('__prefix__')) {
                        initSelect($, $(this));
                    }
                });
            });

            // Запасной вариант через jQuery-событие (Django < 4.x)
            $(document).on('formset:added', function (event, $row, formsetName) {
                if (!$row) return;
                // $row может прийти как DOM-элемент или jQuery
                const $r = $ && $row.jquery ? $row : $($row);
                if (!$r || !$r.length) return;
                $r.find('select[name$="-block_type"]').each(function () {
                    if (!$(this).attr('name').includes('__prefix__')) {
                        initSelect($, $(this));
                    }
                });
            });
        });
    } else {
        setTimeout(waitForDjangoJQuery, 50);
    }
}

waitForDjangoJQuery();