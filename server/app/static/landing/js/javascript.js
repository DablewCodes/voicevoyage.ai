function handleLanguageClick(language) {
    selectedLanguage = language;

    console.log("Clicked")

    var languages = ['English', 'Hindi', 'German', 'French', 'Spanish'];
    for (var i = 0; i < languages.length; i++) {
        var lang = languages[i];
        var button = document.getElementById(lang);
        if (button) {
            if (lang === selectedLanguage) {
                button.classList.add('language-selected');
                button.classList.remove('language-not-selected');
            } else {
                button.classList.add('language-not-selected');
                button.classList.remove('language-selected');
            }
        }
    }
}