const savedTheme = localStorage.getItem('theme') || 'default';

if (savedTheme !== 'default' && savedTheme !== 'light' && savedTheme !== 'custom-light') {
    var cssFile = document.querySelector('[rel="stylesheet"]');
    cssFile.setAttribute('href', '{{ "assets/css/just-the-docs-" | relative_url }}' + savedTheme + '.css');
}