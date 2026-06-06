// static/js/admin/block_toggle.js

document.addEventListener('DOMContentLoaded', function() {

    function hideYearForRow(row) {
        var select = row.querySelector('[id$="block_type"]');
        var yearField = row.querySelector('.field-year');

        if (!select || !yearField) return;

        function toggle() {
            yearField.style.display = (select.value === 'project') ? '' : 'none';
        }

        select.addEventListener('change', toggle);
        toggle();
    }

    // Находим все существующие строки
    var rows = document.querySelectorAll('.inline-related:not(.empty-form)');
    rows.forEach(hideYearForRow);

    // Отслеживаем добавление новых строк
    var addButton = document.querySelector('.add-row a');
    if (addButton) {
        addButton.addEventListener('click', function() {
            setTimeout(function() {
                var newRows = document.querySelectorAll('.inline-related:not(.empty-form)');
                var lastRow = newRows[newRows.length - 1];
                if (lastRow) {
                    hideYearForRow(lastRow);
                }
            }, 50);
        });
    }
});