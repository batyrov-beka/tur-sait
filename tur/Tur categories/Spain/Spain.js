const themeToggleBtn = document.getElementById('theme-toggle');
const body = document.body;

themeToggleBtn.addEventListener('click', () => {
    body.classList.toggle('dark-theme');
    body.classList.toggle('light-content');
});


function initMap() {
    const location = { lat: 42.8746, lng: 74.6034 };  // Мисал үчүн Бишкек
    const map = new google.maps.Map(document.getElementById("google-map"), {
        zoom: 12,
        center: location,
    });
    const marker = new google.maps.Marker({
        position: location,
        map: map,
        title: "Биздин Локация",
    });
}