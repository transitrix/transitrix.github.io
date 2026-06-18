document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', function () {
      var isLight = document.documentElement.getAttribute('data-theme') === 'light';
      if (isLight) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.removeItem('theme');
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
      }
    });
  }

  document.querySelectorAll('.copy-btn').forEach(function (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var wrapper = copyBtn.closest('.code-wrapper');
      if (!wrapper) return;
      var pre = wrapper.querySelector('pre');
      if (!pre) return;
      var originalLabel = copyBtn.getAttribute('data-copy-label') || copyBtn.textContent;
      var copiedLabel = copyBtn.getAttribute('data-copied-label') || 'Copied ✓';
      navigator.clipboard.writeText(pre.textContent).then(function () {
        copyBtn.textContent = copiedLabel;
        copyBtn.setAttribute('data-copied', 'true');
        setTimeout(function () {
          copyBtn.textContent = originalLabel;
          copyBtn.removeAttribute('data-copied');
        }, 2000);
      });
    });
  });
});
