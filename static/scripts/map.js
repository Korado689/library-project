document.addEventListener('DOMContentLoaded', function() {
    var districtLinks = document.querySelectorAll('.district-link');
    var svg = document.querySelector('#main-map');
    var districtsList = document.getElementById('districts-list');

    if (!svg) return;

    var paths = svg.querySelectorAll('path[id]');

    function highlightLink(svgId) {
        districtLinks.forEach(function(l) {
            l.classList.remove('active');
            if (l.dataset.svgId === svgId) l.classList.add('active');
        });
    }

    function highlightRegion(svgId) {
        paths.forEach(function(p) {
            p.setAttribute('fill', p.id === svgId ? '#DBDAAE' : '#faf2e5');
        });
    }

    function showDistrict(svgId) {
        // Скрыть все блоки библиотек
        var allLibraries = document.querySelectorAll('.district-libraries');
        allLibraries.forEach(function(el) { el.style.display = 'none'; });

        // Показать нужный — ищем по data-svg-id
        var block = document.querySelector('.district-libraries[data-svg-id="' + svgId + '"]');
        if (block) block.style.display = 'block';

        // Скрыть список округов
        if (districtsList) districtsList.style.display = 'none';

        // Подсветка
        highlightLink(svgId);
        highlightRegion(svgId);
    }

    function showAllDistricts() {
        var allLibraries = document.querySelectorAll('.district-libraries');
        allLibraries.forEach(function(el) { el.style.display = 'none'; });
        districtLinks.forEach(function(l) { l.classList.remove('active'); });
        paths.forEach(function(p) { p.setAttribute('fill', '#faf2e5'); });
        if (districtsList) districtsList.style.display = 'block';
    }

    // Клик по ссылке
    districtLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            showDistrict(this.dataset.svgId);
        });
    });

    // Клик по региону
    paths.forEach(function(path) {
        path.style.cursor = 'pointer';
        path.addEventListener('click', function() {
            showDistrict(this.id);
        });
    });

    // Кнопки "Назад"
    var backButtons = document.querySelectorAll('.district-libraries__back');
    backButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            showAllDistricts();
        });
    });
});