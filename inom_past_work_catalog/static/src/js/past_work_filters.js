/** @odoo-module **/

function runPastWorkFilters() {
    const items = Array.from(document.querySelectorAll('.js-past-work-item'));
    if (!items.length) {
        return;
    }

    const checkboxes = Array.from(document.querySelectorAll('.js-past-work-filter'));
    const countNode = document.querySelector('.js-past-work-count');
    const emptyNode = document.querySelector('.js-past-work-empty');
    const clearButton = document.querySelector('.js-past-work-clear');

    const applyFilters = () => {
        const selectedSectors = checkboxes
            .filter((box) => box.name === 'sector' && box.checked)
            .map((box) => box.value);
        const selectedTypes = checkboxes
            .filter((box) => box.name === 'work_type' && box.checked)
            .map((box) => box.value);

        let visibleCount = 0;

        items.forEach((item) => {
            const sector = item.dataset.sector || '';
            const workType = item.dataset.workType || '';

            const sectorMatch = !selectedSectors.length || selectedSectors.includes(sector);
            const typeMatch = !selectedTypes.length || selectedTypes.includes(workType);
            const isVisible = sectorMatch && typeMatch;

            item.classList.toggle('d-none', !isVisible);
            if (isVisible) {
                visibleCount += 1;
            }
        });

        if (countNode) {
            countNode.textContent = String(visibleCount);
        }
        if (emptyNode) {
            emptyNode.classList.toggle('d-none', visibleCount !== 0);
        }
    };

    checkboxes.forEach((box) => box.addEventListener('change', applyFilters));

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            checkboxes.forEach((box) => {
                box.checked = false;
            });
            applyFilters();
        });
    }

    applyFilters();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runPastWorkFilters);
} else {
    runPastWorkFilters();
}
