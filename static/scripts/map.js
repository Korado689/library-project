document.addEventListener('DOMContentLoaded', function () {
    const districtLinks = document.querySelectorAll('.district-link');
    const svg = document.querySelector('#main-map');
    const districtsList = document.getElementById('districts-list');

    if (!svg) return;

    const paths = svg.querySelectorAll('path[id]');
    const badgeObjects = document.querySelectorAll('.map-district-badge');
    const tooltip = document.getElementById('map-tooltip');
    const pulses = document.querySelectorAll('.dot-pulse');
    const badgeSize = 36;

    // Всплывающая подсказка
    function showTooltip(text, e) {
        if (!tooltip) return;
        tooltip.textContent = text;
        tooltip.style.opacity = '1';
        moveTooltip(e);
    }

    function moveTooltip(e) {
        if (!tooltip) return;
        tooltip.style.left = (e.clientX + 15) + 'px';
        tooltip.style.top = (e.clientY + 15) + 'px';
    }

    function hideTooltip() {
        if (tooltip) tooltip.style.opacity = '0';
    }

    // Включение пульсации точек района
    function activatePulses(regionId) {
        const targetPulses = document.querySelectorAll(`.dot-pulse[data-svg-id="${regionId}"]`);
        targetPulses.forEach(pulse => pulse.classList.add('active'));
    }

    function deactivateAllPulses() {
        pulses.forEach(p => p.classList.remove('active'));
    }

    // Автоматический расчет центров с защитой от изменения размеров окна
    function updateBadgePositions() {
        badgeObjects.forEach(badge => {
            badge.setAttribute('width', badgeSize);
            badge.setAttribute('height', badgeSize);

            const districtId = badge.getAttribute('data-district-id');
            const path = document.getElementById(districtId);

            if (path) {
                const bbox = path.getBBox();
                const centerX = (bbox.x + bbox.width / 2) - (badgeSize / 2);
                const centerY = (bbox.y + bbox.height / 2) - (badgeSize / 2);

                badge.setAttribute('x', centerX);
                badge.setAttribute('y', centerY);
            }
        });
    }

    // Расчет центров, событие изменения размеров экрана
    updateBadgePositions();
    window.addEventListener('resize', updateBadgePositions);

    // Клик по кнопкам-ссылкам под картой
    districtLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            showDistrict(this.dataset.svgId);
        });
    });

    // Наведение мышки на районы карты
    paths.forEach(path => {
        path.style.cursor = 'pointer';

        path.addEventListener('mouseenter', function (e) {
            const title = this.getAttribute('data-title');
            if (title) showTooltip(title, e);
            activatePulses(this.id);
        });

        path.addEventListener('mousemove', moveTooltip);
        path.addEventListener('mouseleave', function () {
            hideTooltip();
            deactivateAllPulses();
        });

        path.addEventListener('click', function (e) {
            e.stopPropagation();
            showDistrict(this.id);
        });
    });

    // Интерактивность для точки с Котовском
    const clickableDots = document.querySelectorAll('.city-dot[data-click-id]');
    
    clickableDots.forEach(dot => {
        dot.addEventListener('click', function (e) {
            e.stopPropagation();
            const targetId = this.getAttribute('data-click-id');
            showDistrict(targetId);

            const parentPulse = this.previousElementSibling;
            if (parentPulse) {
                const regionId = parentPulse.getAttribute('data-svg-id');
                highlightRegion(regionId);
                highlightLink(regionId);
            }
        });

        dot.addEventListener('mouseenter', function (e) {
            showTooltip("Городской округ Котовск", e);

            const parentPulse = this.previousElementSibling; 
            if (parentPulse) {
                const regionId = parentPulse.getAttribute('data-svg-id');
                activatePulses(regionId);

                const mapPath = document.getElementById(regionId);
                if (mapPath) mapPath.classList.add('map-region--hover');
            }
        });

        dot.addEventListener('mousemove', moveTooltip);

        dot.addEventListener('mouseleave', function () {
            hideTooltip();
            deactivateAllPulses();
            
            const parentPulse = this.previousElementSibling;
            if (parentPulse) {
                const regionId = parentPulse.getAttribute('data-svg-id');
                const mapPath = document.getElementById(regionId);
                if (mapPath) mapPath.classList.remove('map-region--hover');
            }
        });
    });

    // Кнопки "Назад" внутри карточек библиотек
    document.querySelectorAll('.district-libraries__back').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            showAllDistricts();
        });
    });

    // Фильтр по типам библиотек (Плитки Дашбоорда)
    const filterCards = document.querySelectorAll('.dashboard-card');

    filterCards.forEach(card => {
        card.addEventListener('click', function(e) {
            e.stopPropagation();
            const currentDistrict = this.closest('.district-libraries');
            if (!currentDistrict) return;

            currentDistrict.querySelectorAll('.dashboard-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');

            const selectedType = this.getAttribute('data-type');
            const typeRows = currentDistrict.querySelectorAll('.library-type-row');
            const settlementGroups = currentDistrict.querySelectorAll('.settlement-group');
            const emptyMessage = currentDistrict.querySelector('.filter-empty-message');
            const subTitle = currentDistrict.querySelector('.sub-district-title'); 

            typeRows.forEach(row => {
                const rowType = row.getAttribute('data-library-type');
                row.style.display = (selectedType === 'all' || rowType === selectedType) ? 'flex' : 'none';
            });

            settlementGroups.forEach(group => {
                const visibleRows = Array.from(group.querySelectorAll('.library-type-row'))
                                         .filter(row => row.style.display !== 'none');
                group.style.display = (selectedType !== 'all' && visibleRows.length === 0) ? 'none' : 'block';
            });

            const visibleVillageGroups = Array.from(settlementGroups).filter(g => {
                return g.style.display !== 'none' && !g.classList.contains('capital-group');
            });

            const totalVisibleGroups = Array.from(settlementGroups).filter(g => g.style.display !== 'none');

            if (subTitle) {
                subTitle.style.display = (selectedType !== 'all' && visibleVillageGroups.length === 0) ? 'none' : 'block';
            }

            if (emptyMessage) {
                emptyMessage.style.display = (selectedType !== 'all' && totalVisibleGroups.length === 0) ? 'block' : 'none';
            }
        });
    });

    // Интерактивная связь легенды и карты по клику
    const legendItems = document.querySelectorAll('.legend-item');

    legendItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.stopPropagation();
            const selectedType = this.getAttribute('data-legend-type');
            
            if (this.classList.contains('legend-item--active')) {
                resetLegendFilter();
                return;
            }

            legendItems.forEach(i => i.classList.remove('legend-item--active'));
            this.classList.add('legend-item--active');

            paths.forEach(p => p.classList.remove('map-region--active'));

            badgeObjects.forEach(badge => {
                const districtId = badge.getAttribute('data-district-id');
                const count = parseInt(badge.getAttribute(`data-count-${selectedType}`)) || 0;
                const path = document.getElementById(districtId);

                if (count > 0) {
                    if (path) path.classList.add('map-region--active');
                    const circle = badge.querySelector('.map-badge-circle');
                    if (circle) circle.textContent = count;
                    badge.style.display = 'block';
                } else {
                    const libraryBlock = document.querySelector(`.district-libraries[data-svg-id="${districtId}"]`);
                    const isCurrentlyOpen = libraryBlock && libraryBlock.style.display === 'block';
                    if (path && !isCurrentlyOpen) path.classList.remove('map-region--active');
                    badge.style.display = 'none';
                }
            });
        });
    });

    function resetLegendFilter() {
        legendItems.forEach(i => i.classList.remove('legend-item--active'));
        badgeObjects.forEach(badge => {
            const districtId = badge.getAttribute('data-district-id');
            const path = document.getElementById(districtId);
            
            const libraryBlock = document.querySelector(`.district-libraries[data-svg-id="${districtId}"]`);
            const isCurrentlyOpen = libraryBlock && libraryBlock.style.display === 'block';

            if (path && !isCurrentlyOpen) path.classList.remove('map-region--active');
            badge.style.display = 'none';
        });
    }

    svg.addEventListener('click', function(e) {
        if (e.target === svg) {
            resetLegendFilter();
            paths.forEach(p => p.classList.remove('map-region--active'));
            districtLinks.forEach(l => l.classList.remove('active'));
        }
    });

    function highlightLink(svgId) {
        districtLinks.forEach(l => {
            l.classList.toggle('active', l.dataset.svgId === svgId);
        });
    }

    function highlightRegion(svgId) {
        paths.forEach(p => {
            p.classList.toggle('map-region--active', p.id === svgId);
        });
    }

    function showDistrict(svgId) {
        document.querySelectorAll('.district-libraries').forEach(el => el.style.display = 'none');

        const block = document.querySelector(`.district-libraries[data-svg-id="${svgId}"]`);
        if (block) block.style.display = 'block';
        if (districtsList) districtsList.style.display = 'none';

        highlightLink(svgId);
        highlightRegion(svgId);

        if (block) {
            setTimeout(() => {
                block.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 10);
        }
    }

    function showAllDistricts() {
        document.querySelectorAll('.district-libraries').forEach(el => el.style.display = 'none');
        if (districtsList) districtsList.style.display = 'block';

        districtLinks.forEach(l => l.classList.remove('active'));
        paths.forEach(p => p.classList.remove('map-region--active'));

        resetLegendFilter();
        document.querySelectorAll('.dashboard-card[data-type="all"]').forEach(card => card.click());
    }

});



//     //По нажатию на карту появится точка и в консоли будут её координаты на карте
//     (function() {
//     let svg = document.querySelector('#main-map');
//     if (!svg) return console.log('SVG не найден');

//     // Создаем кружок для визуального указателя
//     let dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
//     dot.setAttribute('r', '5');
//     dot.setAttribute('fill', 'red');
//     dot.setAttribute('id', 'temp-dot');
//     svg.appendChild(dot);

//     svg.addEventListener('click', function(e) {
//         let pt = svg.createSVGPoint();
//         pt.x = e.clientX;
//         pt.y = e.clientY;
//         let svgPt = pt.matrixTransform(svg.getScreenCTM().inverse());

//         dot.setAttribute('cx', svgPt.x);
//         dot.setAttribute('cy', svgPt.y);

//         console.log('x:', Math.round(svgPt.x), 'y:', Math.round(svgPt.y));
//     });

// })();
