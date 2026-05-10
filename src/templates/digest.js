(function () {
  // Source filter tabs
  var tabs = document.querySelectorAll('.source-tab');
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var src = tab.dataset.source;
      tabs.forEach(function (t) { t.classList.remove('active'); });
      tab.classList.add('active');
      document.querySelectorAll('.article-item').forEach(function (item) {
        if (src === 'all' || item.dataset.source === src) {
          item.classList.remove('hidden');
        } else {
          item.classList.add('hidden');
        }
      });
    });
  });
})();
