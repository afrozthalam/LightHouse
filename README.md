# <img src="static/logo_dark.png" alt="LightHouse Logo" width="450">

LightHouse is a premium, modern web application that lets you explore trending movies, award-winning series, and top anime, and instantly finds direct streaming and download links from across the web.

**🔗 Deployed Website:** [lighthousecinema.vercel.app](https://lighthousecinema.vercel.app)

---

## 🌟 Key Features

* **Curated Homepage Feeds:** Browse trending content, Academy Award (Oscar) winners, Emmy Award winners, and top anime grids.
* **Premium Movie Details:** Click any card to view storylines, IMDb/TMDB ratings, award details, and recommendations.
* **Dynamic Grid View:** Seamlessly explore categories page-by-page (exactly 21 cards per page) with clean navigation.
* **Parallel Link Scraper:** Type any movie title and search over 70 streaming/download networks simultaneously to locate direct links.
* **Optimized for Scale:** Uses CDN Edge caching and API key rotation to deliver instant load times and prevent API limit bans.

---

## 🛠️ Technologies Used

### Frontend
* **HTML5 & Vanilla CSS3:** Dynamic layout, glassmorphism UI, custom animations, and responsive styling for mobile.
* **Vanilla JavaScript (ES6):** Fast, client-side routing, modular design, and real-time link search streams.

### Backend
* **Python (Flask):** Serves as a secure API gateway and coordinator.
* **BeautifulSoup4:** Parses HTML structures of indexer networks.
* **Playwright:** Headless automation engine for rendering graphics.
* **Requests:** Light, concurrent network fetcher.

---

## 🚀 Running Locally

Follow these steps to run the project on your machine:

1. **Install Python:** Ensure Python (v3.9 or higher) is installed.
2. **Open Terminal / Command Prompt:** Navigate to the project root directory.
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start the Flask Server:**
   ```bash
   python api/index.py
   ```
5. **Open in Browser:** Visit [http://localhost:8000](http://localhost:8000)

---

## 📜 Attributions & Credits

* **Movie Data & Images:** This product uses the TMDB API but is not officially endorsed or certified by TMDB.
* **Project Creator:** Developed by Afroz Thalam.

---

*Made with 💜 for movie and cinema lovers.*
