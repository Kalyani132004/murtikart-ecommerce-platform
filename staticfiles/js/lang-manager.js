// Wait for the browser to finish loading the HTML
document.addEventListener('DOMContentLoaded', () => {
    // 1. Check if a language preference is already saved in the browser (LocalStorage)
    // If not, default to English ('en')
    const currentLang = localStorage.getItem('murtiKartLang') || 'en';
    
    // 2. Apply the initial language on page load
    setLanguage(currentLang);

    // 3. Setup event listeners for language switcher buttons
    // These are buttons with the attribute [data-lang-switch]
    const langButtons = document.querySelectorAll('[data-lang-switch]');
    langButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            // Get the language code (e.g., 'mr' or 'en') from the button
            const lang = btn.getAttribute('data-lang-switch');
            // Change the language when clicked
            setLanguage(lang);
        });
    });
});

/**
 * CORE FUNCTION: setLanguage
 * This function handles the logic of switching text across the whole site
 */
function setLanguage(lang) {
    // Save the selection so the user doesn't have to choose again next time
    localStorage.setItem('murtiKartLang', lang);
    
    // Update the main HTML lang attribute (important for accessibility)
    document.documentElement.lang = lang;

    // 4. Find all elements that need translation (marked with data-i18n)
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        
        // Check if the translation exists for this language and key
        if (translations[lang] && translations[lang][key]) {
            // SPECIAL CASE: If it's an input field, we update the placeholder text
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translations[lang][key];
            } else {
                // Otherwise, we update the inner text of the element
                el.innerText = translations[lang][key];
            }
        }
    });

    // 5. Find all elements that need inline bilingual data (marked with data-en/data-mr)
    const inlineElements = document.querySelectorAll('[data-en]');
    inlineElements.forEach(el => {
        const val = el.getAttribute(`data-${lang}`);
        if(val) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = val;
            } else {
                el.innerText = val;
            }
        }
    });

    // 6. Update UI state: Highlight the currently active language button
    const langButtons = document.querySelectorAll('[data-lang-switch]');
    langButtons.forEach(btn => {
        if (btn.getAttribute('data-lang-switch') === lang) {
            btn.classList.add('active'); // CSS will style this button differently
        } else {
            btn.classList.remove('active');
        }
    });

    // 7. NEW: Update any display elements with id "currentLangDisplay" or class ".currentLangDisplay"
    const displays = document.querySelectorAll('#currentLangDisplay, .currentLangDisplay');
    displays.forEach(d => {
        d.innerText = lang === 'mr' ? 'Marathi (मराठी)' : 'English';
    });
    
    // 8. Notify other parts of the application that the language has changed
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang: lang } }));
}
