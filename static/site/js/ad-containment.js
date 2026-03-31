(function () {
    'use strict';

    function enforceAdContainment(element) {
        if (!element) return;

        element.style.setProperty('width', '100%', 'important');
        element.style.setProperty('maxWidth', '100%', 'important');
        element.style.setProperty('overflow', 'hidden', 'important');
        element.style.setProperty('boxSizing', 'border-box', 'important');

        const children = element.querySelectorAll('*');
        children.forEach(function (child) {
            if (child.style.width && !child.style.width.includes('%')) {
                child.style.setProperty('width', '100%', 'important');
                child.style.setProperty('maxWidth', '100%', 'important');
            }
            if (child.style.height && child.style.height.includes('px') && parseInt(child.style.height, 10) > 300) {
                child.style.setProperty('height', 'auto', 'important');
                child.style.setProperty('maxHeight', '300px', 'important');
            }
            child.style.setProperty('overflow', 'hidden', 'important');
            child.style.setProperty('boxSizing', 'border-box', 'important');
        });
    }

    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            mutation.addedNodes.forEach(function (node) {
                if (node.nodeType === 1) {
                    if (node.classList && (
                        node.classList.contains('ad-wrapper') ||
                        node.classList.contains('ad-container') ||
                        node.classList.contains('ad-strict-container') ||
                        (node.id && node.id.includes('ad')) ||
                        (typeof node.className === 'string' && node.className.includes('ad'))
                    )) {
                        enforceAdContainment(node);
                    }

                    const adElements = node.querySelectorAll('.ad-wrapper, .ad-container, .ad-strict-container, [id*="ad"], [class*="ad"]');
                    adElements.forEach(function (adEl) {
                        enforceAdContainment(adEl);
                    });
                }
            });
        });
    });

    function initAdContainment() {
        const adContainers = document.querySelectorAll('.ad-strict-container, .ad-wrapper, .ad-container');
        adContainers.forEach(function (container) {
            enforceAdContainment(container);
            observer.observe(container, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'width', 'height'],
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAdContainment);
    } else {
        initAdContainment();
    }

    setTimeout(function () {
        const adContainers = document.querySelectorAll('.ad-strict-container, .ad-wrapper, .ad-container');
        adContainers.forEach(function (container) {
            enforceAdContainment(container);
        });
    }, 2000);

    window.addEventListener('resize', function () {
        const adContainers = document.querySelectorAll('.ad-strict-container, .ad-wrapper, .ad-container');
        adContainers.forEach(function (container) {
            enforceAdContainment(container);
        });
    });
})();
