document.addEventListener('DOMContentLoaded', function () {
    const districtLinks = document.querySelectorAll('.district-link');
    const svg = document.querySelector('#main-map');
    const districtsList = document.getElementById('districts-list');

    if (!svg) return;

    const paths = svg.querySelectorAll('path[id]');
    const badgeObjects = document.querySelectorAll('.map-district-badge');
    const tooltip = document.getElementById('map-tooltip');
    const pulses = document.querySelectorAll('.dot-pulse');
    const clickableDots = document.querySelectorAll('.city-dot--clickable');
    const badgeSize = 36;

    // ─────────────────────────────────────────────
    // Тултип
    // ─────────────────────────────────────────────
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

    // ─────────────────────────────────────────────
    // Пульсации
    // ─────────────────────────────────────────────
    function activatePulses(pulseId) {
        if (!pulseId) return;
        const targetPulses = document.querySelectorAll(`.dot-pulse[data-svg-id="${pulseId}"]`);
        targetPulses.forEach(pulse => pulse.classList.add('active'));
    }

    function deactivateAllPulses() {
        pulses.forEach(p => p.classList.remove('active'));
    }

    // ─────────────────────────────────────────────
    // Хелперы подсветки
    // ─────────────────────────────────────────────
    function highlightRegion(svgId, addClass = true) {
        paths.forEach(p => {
            if (p.id === svgId) {
                p.classList.toggle('map-region--hover', addClass);
            } else if (!p.classList.contains('map-region--active')) {
                p.classList.remove('map-region--hover');
            }
        });
    }

    function clearAllHighlights() {
        paths.forEach(p => {
            if (!p.classList.contains('map-region--active')) {
                p.classList.remove('map-region--hover');
            }
        });
    }

    // ─────────────────────────────────────────────
    // Позиционирование бейджей по центрам регионов
    // ─────────────────────────────────────────────
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

    updateBadgePositions();
    window.addEventListener('resize', updateBadgePositions);

    // ─────────────────────────────────────────────
    // Клики по списку районов под картой
    // ─────────────────────────────────────────────
    districtLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            window.showDistrict(this.dataset.svgId);
        });
    });

    // ─────────────────────────────────────────────
    // Наведение/клик по регионам карты
    // ─────────────────────────────────────────────
    paths.forEach(path => {
        path.style.cursor = 'pointer';

        path.addEventListener('mouseenter', function (e) {
            const title = this.getAttribute('data-title');
            if (title) showTooltip(title, e);

            if (!this.classList.contains('map-region--active')) {
                this.classList.add('map-region--hover');
            }
        });

        path.addEventListener('mousemove', moveTooltip);

        path.addEventListener('mouseleave', function () {
            hideTooltip();
            if (!this.classList.contains('map-region--active')) {
                this.classList.remove('map-region--hover');
            }
        });

        path.addEventListener('click', function (e) {
            e.stopPropagation();
            window.showDistrict(this.id);
        });
    });

    // ─────────────────────────────────────────────
    // Точки городов
    // ─────────────────────────────────────────────

    clickableDots.forEach(dot => {
        dot.style.pointerEvents = 'auto';
        dot.style.cursor = 'pointer';

        dot.addEventListener('mouseenter', function (e) {
            const title = this.getAttribute('data-title') || 'Городской округ';
            showTooltip(title, e);

            const pulseId = this.getAttribute('data-pulse-id');
            if (pulseId) activatePulses(pulseId);

            const regionId = this.getAttribute('data-click-id');
            if (regionId) {
                activatePulses(regionId);
                clearAllHighlights();
                highlightRegion(regionId, true);
            }
        });

        dot.addEventListener('mousemove', moveTooltip);

        dot.addEventListener('mouseleave', function () {
            hideTooltip();
            deactivateAllPulses();

            const regionId = this.getAttribute('data-click-id');
            if (regionId) {
                const path = document.getElementById(regionId);
                if (path && !path.classList.contains('map-region--active')) {
                    path.classList.remove('map-region--hover');
                }
            }
        });

        dot.addEventListener('click', function (e) {
            e.stopPropagation();
            const targetId = this.getAttribute('data-click-id');
            if (targetId) window.showDistrict(targetId);

        });
    });

    // ─────────────────────────────────────────────
    // Кнопки "Назад" внутри карточек библиотек
    // ─────────────────────────────────────────────
    document.querySelectorAll('.district-libraries__back').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            window.showAllDistricts();
        });
    });

    // ─────────────────────────────────────────────
    // Фильтр по типам библиотек (плитки-дашборды)
    // ─────────────────────────────────────────────
    const filterCards = document.querySelectorAll('.dashboard-card');

    filterCards.forEach(card => {
        card.addEventListener('click', function (e) {
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

    // ─────────────────────────────────────────────
    // Легенда (фильтр по типу библиотеки на карте)
    // Работает динамически: типы и счётчики приходят из шаблона
    // через data-legend-type и data-count-<type>.
    // ─────────────────────────────────────────────
    const legendItems = document.querySelectorAll('.legend-item');

    legendItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.stopPropagation();
            const selectedType = this.getAttribute('data-legend-type');

            // Повторный клик по активному элементу → сброс
            if (this.classList.contains('legend-item--active')) {
                resetLegendFilter();
                return;
            }

            legendItems.forEach(i => i.classList.remove('legend-item--active'));
            this.classList.add('legend-item--active');

            paths.forEach(p => {
                p.classList.remove('map-region--active', 'map-region--hover');
            });

            badgeObjects.forEach(badge => {
                const districtId = badge.getAttribute('data-district-id');
                const count = parseInt(badge.getAttribute(`data-count-${selectedType}`)) || 0;
                const path = document.getElementById(districtId);
                const circle = badge.querySelector('.map-badge-circle');
                if (count > 0) {
                    if (path) path.classList.add('map-region--active');
                    if (circle) circle.textContent = count;
                    badge.style.display = 'block';
                } else {
                    if (circle) circle.textContent = '0';
                    badge.style.display = 'none';
                    if (path) path.classList.remove('map-region--active');
                }
            });
        });
    });

    function resetLegendFilter() {
        legendItems.forEach(i => i.classList.remove('legend-item--active'));

        // Районы, у которых открыта карточка библиотек — оставляем активными
        const openIds = new Set(
            Array.from(document.querySelectorAll('.district-libraries'))
                .filter(el => el.style.display === 'block')
                .map(el => el.getAttribute('data-svg-id'))
        );

        badgeObjects.forEach(badge => {
            const districtId = badge.getAttribute('data-district-id');
            const path = document.getElementById(districtId);

            if (path && !openIds.has(districtId)) {
                path.classList.remove('map-region--active');
                path.classList.remove('map-region--hover');
            }
            badge.style.display = 'none';
        });
    }

    // ─────────────────────────────────────────────
    // Клик по пустому месту SVG — сброс всего
    // ─────────────────────────────────────────────
    svg.addEventListener('click', function (e) {
        if (e.target === svg || e.target === this) {
            const isPath = e.target.closest('path');
            const isDot = e.target.closest('.city-dot--clickable');

            if (!isPath && !isDot) {
                paths.forEach(p => {
                    p.classList.remove('map-region--active', 'map-region--hover');
                });

                districtLinks.forEach(l => l.classList.remove('active'));
                deactivateAllPulses();
                resetLegendFilter();

                if (districtsList) districtsList.style.display = 'block';
                document.querySelectorAll('.district-libraries').forEach(el => el.style.display = 'none');
            }
        }
    });

    // ─────────────────────────────────────────────
    // Показ/скрытие районов
    // ─────────────────────────────────────────────
    function highlightLink(svgId) {
        districtLinks.forEach(l => {
            l.classList.toggle('active', l.dataset.svgId === svgId);
        });
    }

    window.showDistrict = function (svgId) {
        document.querySelectorAll('.district-libraries').forEach(el => el.style.display = 'none');

        const block = document.querySelector(`.district-libraries[data-svg-id="${svgId}"]`);
        if (block) block.style.display = 'block';
        if (districtsList) districtsList.style.display = 'none';

        highlightLink(svgId);

        paths.forEach(p => {
            p.classList.toggle('map-region--active', p.id === svgId);
            if (p.id !== svgId) {
                p.classList.remove('map-region--hover');
            }
        });

        if (block) {
            setTimeout(() => {
                block.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 10);
        }
    };

    window.showAllDistricts = function () {
        document.querySelectorAll('.district-libraries').forEach(el => el.style.display = 'none');
        if (districtsList) districtsList.style.display = 'block';

        districtLinks.forEach(l => l.classList.remove('active'));
        paths.forEach(p => {
            p.classList.remove('map-region--active');
            p.classList.remove('map-region--hover');
        });

        document.querySelectorAll('.legend-item').forEach(i => i.classList.remove('legend-item--active'));
        document.querySelectorAll('.dashboard-card[data-type="all"]').forEach(card => card.click());
        deactivateAllPulses();
    };
});


// ─────────────────────────────────────────────
// DEV: по клику на карту выводит координаты в консоль.
// Раскомментируйте при подгонке координат новых точек.
// ─────────────────────────────────────────────
// (function () {
//     const svg = document.querySelector('#main-map');
//     if (!svg) return console.log('SVG не найден');
//
//     const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
//     dot.setAttribute('r', '5');
//     dot.setAttribute('fill', 'red');
//     dot.setAttribute('id', 'temp-dot');
//     svg.appendChild(dot);
//
//     svg.addEventListener('click', function (e) {
//         const pt = svg.createSVGPoint();
//         pt.x = e.clientX;
//         pt.y = e.clientY;
//         const svgPt = pt.matrixTransform(svg.getScreenCTM().inverse());
//
//         dot.setAttribute('cx', svgPt.x);
//         dot.setAttribute('cy', svgPt.y);
//
//         console.log('x:', Math.round(svgPt.x), 'y:', Math.round(svgPt.y));
//     });
// })();