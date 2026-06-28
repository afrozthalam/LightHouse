// ==========================================================================
// PARROT Cinema - Frontend Controller (Apple Minimalist style)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // State Variables
    let selectedMovie = null;
    let eventSource = null;
    let activeFilters = {
        purpose: null,
        language: null
    };

    // Top Progress Bar controller matching Moctale style
    const topProgressBar = {
        element: document.getElementById('top-progress-bar'),
        timer: null,
        start() {
            if (!this.element) this.element = document.getElementById('top-progress-bar');
            if (this.timer) clearInterval(this.timer);
            
            this.element.style.transition = 'width 0.4s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.15s ease';
            this.element.style.opacity = '1';
            this.element.style.width = '0%';
            
            let width = 0;
            this.timer = setInterval(() => {
                if (width < 85) {
                    width += Math.random() * 12;
                    if (width > 85) width = 85;
                    this.element.style.width = `${width}%`;
                }
            }, 250);
        },
        done() {
            if (this.timer) clearInterval(this.timer);
            if (!this.element) this.element = document.getElementById('top-progress-bar');
            
            this.element.style.transition = 'width 0.25s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.2s ease';
            this.element.style.width = '100%';
            
            setTimeout(() => {
                this.element.style.opacity = '0';
                setTimeout(() => {
                    this.element.style.width = '0%';
                }, 200);
            }, 150);
        }
    };

    // DOM Elements
    const searchInput = document.getElementById('search-input');
    const searchActionBtn = document.getElementById('search-action-btn');
    const searchSuggestions = document.getElementById('search-suggestions');
    const movieGrid = document.getElementById('movie-grid');
    const gridTitle = document.getElementById('grid-title');
    const brandLogo = document.getElementById('brand-logo');
    
    // Page Swapping Containers
    const homePageContainer = document.getElementById('home-page-container');
    const movieDetailsPage = document.getElementById('movie-details-page');
    const backToHomeBtn = document.getElementById('back-to-home-btn');
    const detailsSearchBtn = document.getElementById('details-search-btn');
    
    const modalPoster = document.getElementById('modal-poster');
    const modalTitle = document.getElementById('modal-title');
    const modalTagline = document.getElementById('modal-tagline');
    const modalYear = document.getElementById('modal-year');
    const modalRating = document.getElementById('modal-rating');
    const modalRuntime = document.getElementById('modal-runtime');
    const modalOverview = document.getElementById('modal-overview');
    const modalHeroBg = document.getElementById('modal-hero-bg');
    const modalAwardsContainer = document.getElementById('modal-awards-container');
    
    const metaCountry = document.getElementById('meta-country');
    const metaLanguage = document.getElementById('meta-language');
    
    // TV Series Seasons Elements
    const seasonsSection = document.getElementById('seasons-section');
    const seasonsCarousel = document.getElementById('seasons-carousel');
    const seasonPrevBtn = document.getElementById('season-prev-btn');
    const seasonNextBtn = document.getElementById('season-next-btn');
    
    // Similar Releases Elements
    const similarSection = document.getElementById('similar-releases-section');
    const similarCarousel = document.getElementById('similar-carousel');
    const similarPrevBtn = document.getElementById('similar-prev-btn');
    const similarNextBtn = document.getElementById('similar-next-btn');
    
    // Filter controls
    const purposeControl = document.getElementById('purpose-control');
    const langControl = document.getElementById('lang-control');
    const languageFilterGroup = document.getElementById('language-filter-group');
    
    // Results & Progress Elements
    const crawlResultsPanel = document.getElementById('crawl-results-panel');
    const progressBox = document.getElementById('progress-box');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressStatusText = document.getElementById('progress-status-text');
    const progressPct = document.getElementById('progress-pct');
    const discoveredLinksBlock = document.getElementById('discovered-links-block');
    const discoveredLinks = document.getElementById('discovered-links');
    const linksCount = document.getElementById('links-count');

    // ==========================================================================
    // Event Listeners
    // ==========================================================================
    
    // Back to explore button navigation
    backToHomeBtn.addEventListener('click', () => {
        history.pushState({ type: 'home' }, '', '/');
        closeMovieDetails();
    });

    // Details search button click returns home and focuses input
    detailsSearchBtn.addEventListener('click', () => {
        history.pushState({ type: 'home' }, '', '/');
        closeMovieDetails();
        searchInput.focus();
    });

    // Brand click triggers back navigation to home too
    brandLogo.addEventListener('click', () => {
        searchInput.value = '';
        searchSuggestions.classList.remove('active');
        history.pushState({ type: 'home' }, '', '/');
        closeMovieDetails();
        loadPopularReleases();
    });

    // Live search suggestions listener
    let suggestionsTimeout = null;
    searchInput.addEventListener('input', () => {
        clearTimeout(suggestionsTimeout);
        const query = searchInput.value.trim();
        if (!query) {
            searchSuggestions.classList.remove('active');
            return;
        }
        suggestionsTimeout = setTimeout(() => fetchSuggestions(query), 300);
    });

    // Enter key press triggers main grid search
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            performSearch();
            searchInput.blur();
        }
    });

    // Search button click triggers main grid search
    searchActionBtn.addEventListener('click', () => {
        performSearch();
        searchInput.blur();
    });

    async function performSearch() {
        const query = searchInput.value.trim();
        clearTimeout(suggestionsTimeout);
        searchSuggestions.classList.remove('active');
        searchSuggestions.innerHTML = '';
        
        if (!query) {
            loadPopularReleases();
            return;
        }

        gridTitle.textContent = `Search Results for "${query}"`;
        
        // Show skeletons in main grid
        movieGrid.innerHTML = '';
        for (let i = 0; i < 4; i++) {
            const card = document.createElement('div');
            card.className = 'skeleton-card';
            movieGrid.appendChild(card);
        }
        
        topProgressBar.start();
        try {
            const r = await fetch(`/api/search-movies?query=${encodeURIComponent(query)}`);
            const data = await r.json();
            
            if (data.results && data.results.length > 0) {
                renderMovieGrid(data.results);
            } else {
                movieGrid.innerHTML = '<div class="grid-placeholder"><p>No matches found.</p></div>';
            }
        } catch (e) {
            movieGrid.innerHTML = `<div class="grid-placeholder"><p class="error">Search failed: ${e.message}</p></div>`;
        } finally {
            topProgressBar.done();
        }
    }

    // Close suggestions on outside clicks
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.hero-search-container')) {
            searchSuggestions.classList.remove('active');
        }
    });

    // History navigation handling to mimic separate pages
    window.addEventListener('popstate', (e) => {
        if (e.state && (e.state.type === 'movie' || e.state.type === 'tv') && e.state.movieId) {
            openMovieDetails({ id: e.state.movieId, media_type: e.state.type }, false);
        } else {
            closeMovieDetails();
        }
    });

    // Initial setup for Purpose cards & Language cards
    setupPurposeCards();
    setupLanguageCards();

    // Check for movie ID in URL on initial load to open detail page immediately
    const checkInitialRoute = async () => {
        const pathMatch = window.location.pathname.match(/\/(movie|tv)\/(\d+)/);
        if (pathMatch && pathMatch[2]) {
            const mediaType = pathMatch[1];
            const movieId = pathMatch[2];
            renderSkeletons();
            topProgressBar.start();
            try {
                const r = await fetch(`/api/movie-details/${movieId}?type=${mediaType}`);
                const movie = await r.json();
                if (movie && movie.id) {
                    openMovieDetails(movie, false);
                }
            } catch(e) {
                console.error("Route load error:", e);
            } finally {
                topProgressBar.done();
            }
        }
        loadPopularReleases();
    };

    checkInitialRoute();

    // ==========================================================================
    // Core Functions
    // ==========================================================================

    // Helper: cached image URL generator
    function getPosterUrl(posterPath, size = 'w342') {
        if (!posterPath) {
            return 'https://via.placeholder.com/342x513/121214/a1a1a6?text=No+Poster';
        }
        return `/api/image?path=${size}/${posterPath.replace(/^\//, '')}`;
    }

    // Fetch live predictions/suggestions
    async function fetchSuggestions(query) {
        try {
            const r = await fetch(`/api/search-movies?query=${encodeURIComponent(query)}`);
            const data = await r.json();
            
            // Stale check: if input query has changed, do NOT render this response!
            if (searchInput.value.trim() !== query) {
                return;
            }
            
            if (data.results && data.results.length > 0) {
                renderSuggestions(data.results.slice(0, 5), query); // show top 5 suggestions
            } else {
                searchSuggestions.innerHTML = '<div style="padding:12px 16px; color:var(--text-muted); font-size:0.9rem;">No matches found</div>';
                searchSuggestions.classList.add('active');
            }
        } catch (e) {
            console.error("Suggestions fetch error:", e);
        }
    }

    function renderSuggestions(movies, query) {
        // If the user has clicked away, or cleared input, or executed search, do NOT show!
        if (document.activeElement !== searchInput || searchInput.value.trim() !== query) {
            searchSuggestions.classList.remove('active');
            return;
        }
        
        searchSuggestions.innerHTML = '';
        
        movies.forEach(movie => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            
            const year = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
            const rating = movie.vote_average ? movie.vote_average.toFixed(1) : '0.0';

            div.innerHTML = `
                <img src="${getPosterUrl(movie.poster_path, 'w92')}" alt="" class="suggestion-poster">
                <div class="suggestion-info">
                    <span class="suggestion-title">${movie.title}</span>
                    <span class="suggestion-meta">${year} • Rating: ${rating}</span>
                </div>
            `;
            
            div.addEventListener('click', () => {
                searchSuggestions.classList.remove('active');
                searchInput.value = '';
                openMovieDetails(movie);
            });
            
            searchSuggestions.appendChild(div);
        });
        
        searchSuggestions.classList.add('active');
    }

    function renderSkeletons() {
        movieGrid.innerHTML = '';
        for (let i = 0; i < 4; i++) {
            const card = document.createElement('div');
            card.className = 'skeleton-card';
            movieGrid.appendChild(card);
        }
    }

    async function loadPopularReleases() {
        gridTitle.textContent = "Trending";
        renderSkeletons();
        
        topProgressBar.start();
        try {
            const r = await fetch('/api/trending-movies');
            const data = await r.json();
            const results = data.results || [];
            
            // Grid gets top 8 trending items
            renderMovieGrid(results.slice(0, 8));
        } catch (e) {
            movieGrid.innerHTML = `<div class="grid-placeholder"><p class="error">Failed to load releases: ${e.message}</p></div>`;
        } finally {
            topProgressBar.done();
        }
    }

    function renderMovieGrid(movies) {
        movieGrid.innerHTML = '';
        if (movies.length === 0) {
            movieGrid.innerHTML = '<div class="grid-placeholder"><p>No movies trending</p></div>';
            return;
        }

        movies.forEach(movie => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            
            const releaseYear = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
            const rating = movie.vote_average ? movie.vote_average.toFixed(1) : '0.0';

            card.innerHTML = `
                <div class="card-poster-wrapper">
                    <img src="${getPosterUrl(movie.poster_path)}" alt="${movie.title}" class="card-poster" loading="lazy">
                    <div class="card-rating">
                        <i class="fa-solid fa-star"></i>
                        <span>${rating}</span>
                    </div>
                </div>
                <div class="card-info">
                    <h3>${movie.title}</h3>
                    <span class="card-year">${releaseYear}</span>
                </div>
            `;

            card.addEventListener('click', () => openMovieDetails(movie));
            movieGrid.appendChild(card);
        });
    }

    async function openMovieDetails(movie, shouldPushState = true) {
        selectedMovie = movie;
        closeSSE();
        
        const mediaType = movie.media_type || (movie.seasons || movie.episode_count || movie.first_air_date || movie.name ? 'tv' : 'movie');
        
        if (shouldPushState && movie.id) {
            history.pushState({ type: mediaType, movieId: movie.id }, '', `/${mediaType}/${movie.id}`);
        }
        
        // Reset selections
        activeFilters.purpose = null;
        activeFilters.language = null;
        
        purposeControl.querySelectorAll('.purpose-card').forEach(c => c.classList.remove('active'));
        langControl.querySelectorAll('.lang-pill-btn').forEach(c => c.classList.remove('active'));
        languageFilterGroup.classList.remove('visible');
        crawlResultsPanel.classList.remove('active');
        
        // Hide Seasons carousel by default
        seasonsCarousel.innerHTML = '';
        seasonsSection.style.display = 'none';
        
        // Hide Similar section by default
        similarCarousel.innerHTML = '';
        similarSection.style.display = 'none';
        
        // Clear awards badge container by default
        modalAwardsContainer.innerHTML = '';
        
        // Set basic details
        modalTitle.textContent = movie.title || "Loading Movie Details...";
        modalOverview.textContent = movie.overview || "No synopsis details available.";
        
        const year = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
        const ratingVal = movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A';
        
        modalYear.textContent = year;
        modalRating.textContent = `★ ${ratingVal}`;
        modalRuntime.textContent = mediaType === 'tv' ? 'Series' : 'Movie';
        modalPoster.src = getPosterUrl(movie.poster_path, 'w342');
        modalHeroBg.style.backgroundImage = 'none';
        
        // Sane fallback meta pills
        modalTagline.textContent = '';
        metaCountry.textContent = 'USA';
        metaLanguage.textContent = 'English';

        // Swap view to separate details screen
        homePageContainer.style.display = 'none';
        movieDetailsPage.style.display = 'block';
        window.scrollTo(0, 0);
        
        // Fetch extended details
        topProgressBar.start();
        try {
            const r = await fetch(`/api/movie-details/${movie.id}?type=${mediaType}`);
            const details = await r.json();
            
            if (details.tagline) {
                modalTagline.textContent = details.tagline;
            }
            if (details.runtime) {
                modalRuntime.textContent = `${details.runtime} min`;
            } else if (details.episode_run_time && details.episode_run_time.length > 0) {
                modalRuntime.textContent = `${details.episode_run_time[0]} min`;
            } else {
                modalRuntime.textContent = 'Show';
            }
            if (details.backdrop_path) {
                modalHeroBg.style.backgroundImage = `url('${getPosterUrl(details.backdrop_path, 'original')}')`;
            }
            
            // Country spec
            if (details.production_countries && details.production_countries.length > 0) {
                metaCountry.textContent = details.production_countries[0].iso_3166_1 || details.production_countries[0].name;
            }
            
            // Primary Language spec
            if (details.spoken_languages && details.spoken_languages.length > 0) {
                metaLanguage.textContent = details.spoken_languages[0].english_name;
            }

            // TV Series Season Slider Integration
            if (details.seasons && details.seasons.length > 0) {
                renderSeasons(details.seasons);
                seasonsSection.style.display = 'block';
            }

            // OMDb Top Awards Badge Integration
            modalAwardsContainer.innerHTML = '';
            if (details.parsed_awards && details.parsed_awards.length > 0) {
                details.parsed_awards.forEach(award => {
                    const badge = document.createElement('div');
                    badge.className = `modal-awards-badge ${award.color}`;
                    badge.innerHTML = `
                        <i class="fa-solid fa-trophy"></i>
                        <span>${award.text}</span>
                    `;
                    modalAwardsContainer.appendChild(badge);
                });
            }

            // Similar Releases Integration
            if (details.similar && details.similar.length > 0) {
                renderSimilar(details.similar);
                similarSection.style.display = 'block';
            }
        } catch (e) {
            console.error("Movie details loading error:", e);
        } finally {
            topProgressBar.done();
        }
    }

    function renderSeasons(seasons) {
        seasonsCarousel.innerHTML = '';
        
        // Filter out season specials (season_number = 0) unless it's the only season
        const validSeasons = seasons.filter(s => s.season_number > 0 || seasons.length === 1);
        
        validSeasons.forEach(season => {
            const card = document.createElement('div');
            card.className = 'season-card';
            
            const releaseYear = season.air_date ? season.air_date.split('-')[0] : 'N/A';
            const progress = season.vote_average ? Math.round(season.vote_average * 10) : 85; // mock watched progress indicator
            const mockReviews = Math.round((season.vote_average || 7.8) * 200 + (season.season_number * 42));

            card.innerHTML = `
                <img src="${getPosterUrl(season.poster_path, 'w185')}" class="season-poster" alt="${season.name}">
                <div class="season-info">
                    <div class="season-header-meta">
                        <span class="season-title-text">${season.name}</span>
                        <span class="season-watched-icon"><i class="fa-solid fa-circle-check"></i></span>
                    </div>
                    <span class="season-meta-row">${releaseYear} • ${season.episode_count} Episodes</span>
                    <span class="season-reviews-meta">${mockReviews.toLocaleString()} Reviews</span>
                    <div class="season-progress-bar">
                        <div class="season-progress-fill" style="width: ${progress}%"></div>
                    </div>
                </div>
            `;
            seasonsCarousel.appendChild(card);
        });

        // Bind carousel chevron button arrows
        seasonPrevBtn.onclick = () => {
            seasonsCarousel.scrollBy({ left: -320, behavior: 'smooth' });
        };
        seasonNextBtn.onclick = () => {
            seasonsCarousel.scrollBy({ left: 320, behavior: 'smooth' });
        };
    }

    function closeMovieDetails() {
        closeSSE();
        movieDetailsPage.style.display = 'none';
        homePageContainer.style.display = 'block';
        window.scrollTo(0, 0);
    }

    function setupPurposeCards() {
        purposeControl.querySelectorAll('.purpose-card').forEach(card => {
            card.addEventListener('click', () => {
                purposeControl.querySelectorAll('.purpose-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                activeFilters.purpose = card.getAttribute('data-value');
                
                // Slide in language choices panel
                languageFilterGroup.classList.add('visible');
                
                // Reset language choices selection on changing purpose
                activeFilters.language = null;
                langControl.querySelectorAll('.lang-pill-btn').forEach(c => c.classList.remove('active'));
                
                // Scroll layout so language panel is visible
                languageFilterGroup.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            });
        });
    }

    function setupLanguageCards() {
        langControl.querySelectorAll('.lang-pill-btn').forEach(card => {
            card.addEventListener('click', () => {
                if (!activeFilters.purpose) return; // safety check
                
                langControl.querySelectorAll('.lang-pill-btn').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                activeFilters.language = card.getAttribute('data-value');
                
                // Instant Auto-Trigger search crawling!
                startCrawl();
            });
        });
    }

    function startCrawl() {
        if (!selectedMovie || !activeFilters.purpose || !activeFilters.language) return;

        topProgressBar.start();

        // Reset progress loaders to initial state
        progressBarFill.style.width = '0%';
        progressPct.textContent = '0%';
        progressStatusText.textContent = 'Locating best stream links, please wait...';
        
        // Hide stream links list initially during crawl loading
        progressBox.style.display = 'block';
        discoveredLinksBlock.style.display = 'none';
        discoveredLinks.innerHTML = '';
        linksCount.textContent = '0 found';
        
        // Reveal container
        crawlResultsPanel.classList.add('active');
        
        // Scroll layout so progress is visible
        crawlResultsPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        const movieTitleAndYear = selectedMovie.release_date
            ? `${selectedMovie.title} (${selectedMovie.release_date.split('-')[0]})`
            : selectedMovie.title;

        // SSE connection
        const sseUrl = `/api/search-links/stream?title=${encodeURIComponent(movieTitleAndYear)}&purpose=${activeFilters.purpose}&language=${activeFilters.language}`;
        eventSource = new EventSource(sseUrl);

        let totalSites = 15;
        let completedSites = 0;

        eventSource.addEventListener('log', (e) => {
            const text = e.data;
            
            const searchCountMatch = text.match(/Searching (\d+) matching sites/);
            if (searchCountMatch) {
                totalSites = parseInt(searchCountMatch[1]);
            }
            
            if (text.includes('[SITE_COMPLETE]')) {
                completedSites++;
                const pct = Math.min(95, Math.round((completedSites / totalSites) * 100));
                progressBarFill.style.width = `${pct}%`;
                progressPct.textContent = `${pct}%`;
                // Keep the text status extremely simple for the user
                progressStatusText.textContent = 'Locating best stream links, please wait...';
            }
        });

        eventSource.addEventListener('complete', (e) => {
            const data = JSON.parse(e.data);
            closeSSE();
            topProgressBar.done();
            
            progressBarFill.style.width = '100%';
            progressPct.textContent = '100%';
            
            // Wait 500ms for transition fill to finish loading smoothly, then swap
            setTimeout(() => {
                progressBox.style.display = 'none';
                
                if (data.status === 'success') {
                    renderDiscoveredLinks(data.results);
                } else {
                    discoveredLinks.innerHTML = `
                        <div class="links-placeholder">
                            <p style="color:var(--color-danger)">Search crawl error: ${data.error}</p>
                        </div>
                    `;
                }
                discoveredLinksBlock.style.display = 'block';
            }, 500);
        });

        eventSource.onerror = (err) => {
            console.error("SSE Connection Error:", err);
            progressStatusText.textContent = 'Network node connection interrupted.';
            progressBarFill.style.width = '100%';
            progressBarFill.style.background = 'var(--color-danger)';
            closeSSE();
            topProgressBar.done();
            setTimeout(() => {
                progressBox.style.display = 'none';
                discoveredLinks.innerHTML = `
                    <div class="links-placeholder">
                        <p style="color:var(--color-danger)">Connection interrupted. Try selecting configuration filters again.</p>
                    </div>
                `;
                discoveredLinksBlock.style.display = 'block';
            }, 500);
        };
    }

    // Parse movie quality information dynamically from scraped page title string
    function extractQualities(title) {
        const qualities = [];
        const t = title.toLowerCase();
        
        if (t.includes('2160p') || t.includes('4k') || t.includes('uhd')) qualities.push('4K Ultra HD');
        else if (t.includes('1080p') || t.includes('fhd')) qualities.push('1080p Full HD');
        else if (t.includes('720p') || t.includes('hd')) qualities.push('720p HD');
        else qualities.push('1080p HD'); // Sane default quality if unspecified
        
        if (t.includes('hevc') || t.includes('x265') || t.includes('10bit')) qualities.push('HEVC 10-bit');
        if (t.includes('dual') || (t.includes('hindi') && t.includes('english'))) qualities.push('Dual Audio (Hin-Eng)');
        
        return qualities.join(' • ');
    }

    function renderDiscoveredLinks(results) {
        const found = results ? results.filter(r => r.status === 'FOUND') : [];
        linksCount.textContent = `${found.length} found`;
        
        if (found.length === 0) {
            discoveredLinks.innerHTML = `
                <div class="links-placeholder">
                    <p>No compatible streams found on indexing networks.</p>
                </div>
            `;
            return;
        }

        discoveredLinks.innerHTML = '';
        
        found.forEach(item => {
            const card = document.createElement('div');
            card.className = 'link-card';
            
            const resolvedQualities = extractQualities(item.title);
            
            // Clean premium card layout: Site Name, resolved qualities, and styled Visit Button (no direct link URLs or match scores)
            card.innerHTML = `
                <div class="link-card-left">
                    <span class="link-site-name">${item.site}</span>
                    <span class="link-qualities">${resolvedQualities}</span>
                </div>
                <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn-visit">
                    Open <i class="fa-solid fa-up-right-from-square"></i>
                </a>
            `;
            
            discoveredLinks.appendChild(card);
        });
    }

    function renderSimilar(items) {
        similarCarousel.innerHTML = '';
        items.forEach(movie => {
            const card = document.createElement('div');
            card.className = 'similar-card';
            
            const year = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
            const ratingVal = movie.vote_average ? movie.vote_average.toFixed(1) : '0.0';
            
            card.innerHTML = `
                <div class="similar-poster-wrap">
                    <img src="${getPosterUrl(movie.poster_path, 'w185')}" alt="${movie.title}" class="similar-poster-img" loading="lazy">
                </div>
                <div class="similar-info">
                    <h3 class="similar-title">${movie.title}</h3>
                    <div class="similar-meta">
                        <span class="similar-year">${year}</span>
                        <span class="similar-rating"><i class="fa-solid fa-star"></i> ${ratingVal}</span>
                    </div>
                </div>
            `;
            
            card.addEventListener('click', () => {
                openMovieDetails(movie);
            });
            
            similarCarousel.appendChild(card);
        });

        // Bind carousel chevron button arrows
        similarPrevBtn.onclick = () => {
            similarCarousel.scrollBy({ left: -280, behavior: 'smooth' });
        };
        similarNextBtn.onclick = () => {
            similarCarousel.scrollBy({ left: 280, behavior: 'smooth' });
        };
    }

    function closeSSE() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    }
});
