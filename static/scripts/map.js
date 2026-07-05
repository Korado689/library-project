document.addEventListener('DOMContentLoaded', function () {
    let districtLinks = document.querySelectorAll('.district-link');
    let svg = document.querySelector('#main-map');
    let districtsList = document.getElementById('districts-list');

    if (!svg) return;

    let paths = svg.querySelectorAll('path[id]');

    // Клик по ссылке
    districtLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            showDistrict(this.dataset.svgId);
        });
    });

    // Клик по региону
    paths.forEach(function (path) {
        path.style.cursor = 'pointer';
        path.addEventListener('click', function () {
            showDistrict(this.id);
        });
    });

    // Кнопки "Назад"
    let backButtons = document.querySelectorAll('.district-libraries__back');
    backButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            showAllDistricts();
        });
    });

    function highlightLink(svgId) {
        districtLinks.forEach(function (l) {
            l.classList.remove('active');
            if (l.dataset.svgId === svgId) l.classList.add('active');
        });
    }

    function highlightRegion(svgId) {
        paths.forEach(function (p) {
            paths.forEach(p => p.classList.toggle('map-region--active', p.id === svgId));
        });
    }

    function showDistrict(svgId) {
        // Скрыть все блоки библиотек
        let allLibraries = document.querySelectorAll('.district-libraries');
        allLibraries.forEach(function (el) {
            el.style.display = 'none';
        });

        // Показать нужный — ищем по data-svg-id
        let block = document.querySelector('.district-libraries[data-svg-id="' + svgId + '"]');
        if (block) block.style.display = 'block';

        // Скрыть список округов
        if (districtsList) districtsList.style.display = 'none';

        // Подсветка
        highlightLink(svgId);
        highlightRegion(svgId);
    }

    function showAllDistricts() {
        let allLibraries = document.querySelectorAll('.district-libraries');
        allLibraries.forEach(function (el) {
            el.style.display = 'none';
        });

        districtLinks.forEach(function (l) {
            l.classList.remove('active');
        });

        paths.forEach(function (p) {
            p.setAttribute('fill', '#faf2e5');
        });

        if (districtsList) districtsList.style.display = 'block';
    }
});



    // По нажатию на карту появится точка и в консоли будут её координаты на карте
//     (function() {
//     let svg = document.querySelector('#main-map');
//     if (!svg) return console.log('SVG не найден');
//
//     // Создаем кружок для визуального указателя
//     let dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
//     dot.setAttribute('r', '5');
//     dot.setAttribute('fill', 'red');
//     dot.setAttribute('id', 'temp-dot');
//     svg.appendChild(dot);
//
//     svg.addEventListener('click', function(e) {
//         let pt = svg.createSVGPoint();
//         pt.x = e.clientX;
//         pt.y = e.clientY;
//         let svgPt = pt.matrixTransform(svg.getScreenCTM().inverse());
//
//         dot.setAttribute('cx', svgPt.x);
//         dot.setAttribute('cy', svgPt.y);
//
//         console.log('x:', Math.round(svgPt.x), 'y:', Math.round(svgPt.y));
//     });
//
// })();
