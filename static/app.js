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
    const modalOriginalTitle = document.getElementById('modal-original-title');
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
    const lighthouseLoaderWrap = document.getElementById('lighthouse-loader-wrap');
    const discoveredLinksBlock = document.getElementById('discovered-links-block');
    const discoveredLinks = document.getElementById('discovered-links');
    const linksCount = document.getElementById('links-count');
    
    // Rare networks results elements
    const rareLinksBlock = document.getElementById('rare-links-block');
    const rareDiscoveredLinks = document.getElementById('rare-discovered-links');
    const rareLinksCount = document.getElementById('rare-links-count');

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
                movieGrid.innerHTML = `
                    <div class="grid-placeholder" style="grid-column: 1 / -1; width: 100%;">
                        <p style="font-size: 1.1rem; margin-bottom: 12px; color: var(--text-secondary);">No matches found in TMDB database.</p>
                        <div class="force-search-prompt">
                            <p>Can't find your movie/series? Try Force Search to crawl direct indexers directly using your query keyword.</p>
                            <button class="btn-force-search" id="btn-force-search-empty">
                                <i class="fa-solid fa-wand-magic-sparkles"></i> Force Search "${query}"
                            </button>
                        </div>
                    </div>
                `;
                const btn = document.getElementById('btn-force-search-empty');
                if (btn) {
                    btn.addEventListener('click', () => {
                        triggerForceSearch(query);
                    });
                }
            }
        } catch (e) {
            movieGrid.innerHTML = `
                <div class="grid-placeholder" style="grid-column: 1 / -1; width: 100%;">
                    <p class="error" style="font-size: 1.1rem; margin-bottom: 12px; color: var(--color-danger);">Search failed: ${e.message}</p>
                    <div class="force-search-prompt">
                        <p>Can't find your movie/series? Try Force Search to crawl direct indexers directly using your query keyword.</p>
                        <button class="btn-force-search" id="btn-force-search-fail">
                            <i class="fa-solid fa-wand-magic-sparkles"></i> Force Search "${query}"
                        </button>
                    </div>
                </div>
            `;
            const btn = document.getElementById('btn-force-search-fail');
            if (btn) {
                btn.addEventListener('click', () => {
                    triggerForceSearch(query);
                });
            }
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
        } else if (e.state && e.state.type === 'dash') {
            openDashboard(false);
        } else {
            closeMovieDetails();
        }
    });

    function triggerForceSearch(query) {
        const mockMovie = {
            id: -1,
            title: query,
            original_title: query,
            release_date: '',
            vote_average: 0,
            poster_path: null,
            overview: `Force search execution for "${query}". This will search the indexing networks directly using your custom keyword.`,
            media_type: 'movie',
            is_force_search: true
        };
        openMovieDetails(mockMovie);
    }

    // Initial setup for Purpose cards & Language cards
    setupPurposeCards();
    setupLanguageCards();

    // Check for movie ID in URL on initial load to open detail page immediately
    const checkInitialRoute = async () => {
        if (window.location.pathname === '/dash') {
            openDashboard(false);
            return;
        }
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
                searchSuggestions.innerHTML = `
                    <div style="padding:12px 16px; color:var(--text-muted); font-size:0.9rem;">
                        <div>No matches found in TMDB.</div>
                        <button class="btn-force-search-suggest" id="btn-force-search-suggest-btn">
                            <i class="fa-solid fa-wand-magic-sparkles"></i> Force Search "${query}"
                        </button>
                    </div>
                `;
                searchSuggestions.classList.add('active');
                const suggestBtn = document.getElementById('btn-force-search-suggest-btn');
                if (suggestBtn) {
                    suggestBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        searchSuggestions.classList.remove('active');
                        searchInput.value = '';
                        triggerForceSearch(query);
                    });
                }
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

            const hasOrigTitle = movie.original_title && movie.original_title.toLowerCase().trim() !== movie.title.toLowerCase().trim();
            const displayTitle = hasOrigTitle ? `${movie.title} (${movie.original_title})` : movie.title;

            div.innerHTML = `
                <img src="${getPosterUrl(movie.poster_path, 'w92')}" alt="" class="suggestion-poster">
                <div class="suggestion-info">
                    <span class="suggestion-title">${displayTitle}</span>
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

            const hasOrigTitle = movie.original_title && movie.original_title.toLowerCase().trim() !== movie.title.toLowerCase().trim();
            const displayTitle = hasOrigTitle ? `${movie.title} (${movie.original_title})` : movie.title;

            card.innerHTML = `
                <div class="card-poster-wrapper">
                    <img src="${getPosterUrl(movie.poster_path)}" alt="${movie.title}" class="card-poster" loading="lazy">
                    <div class="card-rating">
                        <i class="fa-solid fa-star"></i>
                        <span>${rating}</span>
                    </div>
                </div>
                <div class="card-info">
                    <h3>${displayTitle}</h3>
                    <span class="card-year">${releaseYear}</span>
                </div>
            `;

            card.addEventListener('click', () => openMovieDetails(movie));
            movieGrid.appendChild(card);
        });

        // Always show the force search trigger bar at the bottom of search result pages
        const query = searchInput.value.trim();
        const isTrending = gridTitle.textContent.includes('Trending');
        if (query && !isTrending) {
            const bottomPrompt = document.createElement('div');
            bottomPrompt.className = 'force-search-bottom-prompt';
            bottomPrompt.style.gridColumn = '1 / -1';
            bottomPrompt.innerHTML = `
                <p>Can't find the exact movie or series version you want? Try Force Search to bypass listings and search indices directly.</p>
                <button class="btn-force-search" id="btn-force-search-results-bottom">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Force Search "${query}"
                </button>
            `;
            movieGrid.appendChild(bottomPrompt);
            const btn = document.getElementById('btn-force-search-results-bottom');
            if (btn) {
                btn.addEventListener('click', () => {
                    triggerForceSearch(query);
                });
            }
        }
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
        
        // Hide Rare links block by default
        rareLinksBlock.style.display = 'none';
        rareDiscoveredLinks.innerHTML = '';
        rareLinksCount.textContent = '0 found';
        
        // Set basic details
        modalTitle.textContent = movie.title || "Loading Movie Details...";
        modalOriginalTitle.style.display = 'none';
        modalOriginalTitle.textContent = '';
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
        
        if (movie.is_force_search) {
            modalYear.textContent = 'Custom';
            modalRating.textContent = '★ N/A';
            modalRuntime.textContent = 'Force Find';
            metaCountry.textContent = 'Custom';
            metaLanguage.textContent = 'Any';
            topProgressBar.done();
            return;
        }
        
        // Fetch extended details
        topProgressBar.start();
        try {
            const r = await fetch(`/api/movie-details/${movie.id}?type=${mediaType}`);
            const details = await r.json();
            selectedMovie = { ...selectedMovie, ...details };
            
            if (details.original_title && details.original_title.toLowerCase().trim() !== details.title.toLowerCase().trim()) {
                modalOriginalTitle.textContent = `Original Title: ${details.original_title}`;
                modalOriginalTitle.style.display = 'block';
            }
            
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
        if (typeof dashboardPageContainer !== 'undefined' && dashboardPageContainer) {
            dashboardPageContainer.style.display = 'none';
        }
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
        
        // Show stream links list initially during crawl loading
        progressBox.style.display = 'block';
        lighthouseLoaderWrap.style.display = 'flex';
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
        const disabledListStr = localStorage.getItem('lighthouse_disabled_sites') || '';
        const originalTitleStr = selectedMovie.original_title || '';
        const isAnime = selectedMovie.genres && 
                        selectedMovie.genres.some(g => g.name && (g.name.toLowerCase().includes('animation') || g.name.toLowerCase().includes('animated'))) && 
                        selectedMovie.original_language === 'ja';
        const isAnimeStr = isAnime ? 'true' : 'false';
        const sseUrl = `/api/search-links/stream?title=${encodeURIComponent(movieTitleAndYear)}&purpose=${activeFilters.purpose}&language=${activeFilters.language}&exclude_sites=${encodeURIComponent(disabledListStr)}&original_title=${encodeURIComponent(originalTitleStr)}&is_anime=${isAnimeStr}`;
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
                lighthouseLoaderWrap.style.display = 'none';
                
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
            closeSSE();
            topProgressBar.done();
            
            // Only show connection error if the search didn't complete and returned no results
            if (discoveredLinks.innerHTML.trim() === '' && progressPct.textContent !== '100%') {
                progressStatusText.textContent = 'Network node connection interrupted.';
                progressBarFill.style.width = '100%';
                progressBarFill.style.background = 'var(--color-danger)';
                setTimeout(() => {
                    progressBox.style.display = 'none';
                    lighthouseLoaderWrap.style.display = 'none';
                    discoveredLinks.innerHTML = `
                        <div class="links-placeholder">
                            <p style="color:var(--color-danger)">Connection interrupted. Try selecting configuration filters again.</p>
                        </div>
                    `;
                    discoveredLinksBlock.style.display = 'block';
                }, 500);
            }
        };
    }

    // Parse movie quality information dynamically from scraped page title string
    function extractQualities(title) {
        const qualities = [];
        const t = title.toLowerCase();
        
        if (t.includes('2160p') || t.includes('4k') || t.includes('uhd')) qualities.push('4K UHD');
        else if (t.includes('1080p') || t.includes('fhd')) qualities.push('1080p FHD');
        else if (t.includes('720p') || t.includes('hd')) qualities.push('720p HD');
        else qualities.push('1080p HD'); // Sane default quality if unspecified
        
        if (t.includes('hevc') || t.includes('x265') || t.includes('10bit')) qualities.push('HEVC 10-Bit');
        if (t.includes('dual') || (t.includes('hindi') && t.includes('english'))) qualities.push('Dual Audio');
        
        return qualities;
    }

    // Render HTML spans for each parsed movie quality tag with distinct neomorphic styles
    function renderQualitiesHTML(qualities) {
        if (!qualities || qualities.length === 0) return '';
        return qualities.map(q => {
            let cls = 'tag-general';
            if (q.includes('4K')) cls = 'tag-4k';
            else if (q.includes('1080p')) cls = 'tag-1080p';
            else if (q.includes('720p')) cls = 'tag-720p';
            else if (q.includes('HEVC')) cls = 'tag-hevc';
            else if (q.includes('Dual')) cls = 'tag-dual';
            return `<span class="link-tag ${cls}">${q}</span>`;
        }).join('');
    }

    const brandColors = {
        'vegamovies': '#ff2d55',
        'movies4u-finance': '#5856d6',
        'movies4u': '#5856d6',
        'uhdmovies': '#ffcc00',
        'yomovies': '#af52de',
        'cineb': '#34c759',
        'cataz': '#007aff',
        'dopebox': '#5ac8fa',
        'seriesonline': '#ff9500',
        'skymovieshd': '#ff5e00',
        '4khdhub': '#30d158',
        'themoviesflix': '#ff375f',
        'cinego': '#64d2ff',
        'zoovie': '#0a84ff',
        'vk-video': '#2f80ed',
        'mail-ru': '#ff9f0a',
        'ok-ru': '#ff5e00',
        '1hd': '#ffcc00',
        'attackertv': '#30d158',
        'watchseries8': '#ff2d55'
    };

    function getTagStyle(type) {
        switch (type) {
            case 'orange':
                return 'background: #d84b06 !important; color: #ffffff !important;';
            case 'teal':
                return 'background: #0b8489 !important; color: #ffffff !important;';
            case 'green':
                return 'background: #0d732d !important; color: #ffffff !important;';
            case 'purple':
                return 'background: #5e5ce6 !important; color: #ffffff !important;';
            case 'blue':
                return 'background: #007aff !important; color: #ffffff !important;';
            default:
                return 'background: #8e8e93 !important; color: #ffffff !important;';
        }
    }

    function renderRareLinks(results) {
        rareDiscoveredLinks.innerHTML = '';
        const found = results ? results.filter(r => r.status === 'FOUND') : [];
        rareLinksCount.textContent = `${found.length} found`;
        
        if (found.length === 0) {
            rareLinksBlock.style.display = 'none';
            return;
        }

        // Count occurrences of each site to number them sequentially
        const siteCounters = {};
        found.forEach(item => {
            siteCounters[item.site] = (siteCounters[item.site] || 0) + 1;
        });

        const currentCounters = {};
        found.forEach(item => {
            const card = document.createElement('div');
            card.className = 'link-card rare-card';
            
            card.style.background = '#151518';
            card.style.border = '1px solid rgba(255, 255, 255, 0.08)';
            card.style.borderRadius = '12px';
            card.style.padding = '18px 24px';
            card.style.transition = 'all 0.2s ease';
            card.style.position = 'relative';
            card.style.overflow = 'hidden';
            card.style.display = 'flex';
            card.style.justifyContent = 'space-between';
            card.style.alignItems = 'center';
            card.style.gap = '20px';
            
            // Format site name to show index number if there are duplicate links (e.g. VK Video - Link 1)
            let displayName = item.site;
            if (siteCounters[item.site] > 1) {
                currentCounters[item.site] = (currentCounters[item.site] || 0) + 1;
                displayName = `${item.site} - Link ${currentCounters[item.site]}`;
            }

            const resolvedQualities = extractQualities(item.title);
            const qualitiesHTML = resolvedQualities.map(q => {
                let tagType = 'blue';
                if (q.includes('4K') || q.includes('1080p') || q.includes('720p') || q.includes('HD')) {
                    tagType = 'orange';
                } else if (q.includes('Dual') || q.includes('Audio')) {
                    tagType = 'teal';
                } else if (q.includes('HEVC') || q.includes('10-Bit')) {
                    tagType = 'green';
                }
                return `<span class="link-tag" style="${getTagStyle(tagType)} font-size: 0.72rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; white-space: nowrap; border: none !important;">${q}</span>`;
            }).join(' ');
            
            card.innerHTML = `
                <div class="link-card-left" style="display: flex; flex-direction: column; gap: 8px; align-items: flex-start; flex: 1;">
                    <span class="link-site-name" style="font-size: 1.1rem; font-weight: 600; color: #ffffff !important; line-height: 1.4; text-align: left; display: block; word-break: break-word;"><i class="fa-solid fa-circle-play" style="color: #bf5af2; margin-right: 6px;"></i> ${displayName}</span>
                    <div class="link-qualities" style="display: flex; flex-wrap: wrap; gap: 8px;">${qualitiesHTML}</div>
                </div>
                <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn-visit rare-visit-btn" style="background: rgba(255, 255, 255, 0.06) !important; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; text-decoration: none; padding: 8px 18px; border-radius: 30px; font-weight: 600; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s ease; white-space: nowrap; flex-shrink: 0; cursor: pointer;">
                    Open <i class="fa-solid fa-up-right-from-square"></i>
                </a>
            `;
            
            card.addEventListener('mouseenter', () => {
                card.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                card.style.background = 'rgba(255, 255, 255, 0.02)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                card.style.background = '#151518';
            });

            const visitBtn = card.querySelector('.btn-visit');
            visitBtn.addEventListener('mouseenter', () => {
                visitBtn.style.background = '#ffffff';
                visitBtn.style.color = '#070708';
                visitBtn.style.borderColor = '#ffffff';
            });
            visitBtn.addEventListener('mouseleave', () => {
                visitBtn.style.background = 'rgba(255, 255, 255, 0.06)';
                visitBtn.style.color = '#ffffff';
                visitBtn.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            });
            
            rareDiscoveredLinks.appendChild(card);
        });
        
        rareLinksBlock.style.display = 'block';
    }

    function renderDiscoveredLinks(results) {
        // Split rare and general results
        const generalResults = results ? results.filter(r => r.site !== 'VK Video' && r.site !== 'Mail.ru' && r.site !== 'OK.ru') : [];
        const rareResults = results ? results.filter(r => r.site === 'VK Video' || r.site === 'Mail.ru' || r.site === 'OK.ru') : [];

        const foundGeneral = generalResults.filter(r => r.status === 'FOUND');
        linksCount.textContent = `${foundGeneral.length} found`;
        
        if (foundGeneral.length === 0) {
            discoveredLinks.innerHTML = `
                <div class="links-placeholder">
                    <p>No compatible streams found on indexing networks.</p>
                </div>
            `;
        } else {
            discoveredLinks.innerHTML = '';
            foundGeneral.forEach(item => {
                const card = document.createElement('div');
                card.className = 'link-card general-card';
                
                card.style.background = '#151518';
                card.style.border = '1px solid rgba(255, 255, 255, 0.08)';
                card.style.borderRadius = '12px';
                card.style.padding = '18px 24px';
                card.style.transition = 'all 0.2s ease';
                card.style.position = 'relative';
                card.style.overflow = 'hidden';
                card.style.display = 'flex';
                card.style.justifyContent = 'space-between';
                card.style.alignItems = 'center';
                card.style.gap = '20px';
                
                const resolvedQualities = extractQualities(item.title);
                const qualitiesHTML = resolvedQualities.map(q => {
                    let tagType = 'blue';
                    if (q.includes('4K') || q.includes('1080p') || q.includes('720p') || q.includes('HD')) {
                        tagType = 'orange';
                    } else if (q.includes('Dual') || q.includes('Audio')) {
                        tagType = 'teal';
                    } else if (q.includes('HEVC') || q.includes('10-Bit')) {
                        tagType = 'green';
                    }
                    return `<span class="link-tag" style="${getTagStyle(tagType)} font-size: 0.72rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; white-space: nowrap; border: none !important;">${q}</span>`;
                }).join(' ');
                
                card.innerHTML = `
                    <div class="link-card-left" style="display: flex; flex-direction: column; gap: 8px; align-items: flex-start; flex: 1;">
                        <span class="link-site-name" style="font-size: 1.1rem; font-weight: 600; color: #ffffff !important; line-height: 1.4; text-align: left; display: block; word-break: break-word;"><i class="fa-solid fa-circle-play" style="color: #64d2ff; margin-right: 6px;"></i> ${item.site}</span>
                        <div class="link-qualities" style="display: flex; flex-wrap: wrap; gap: 8px;">${qualitiesHTML}</div>
                    </div>
                    <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn-visit" style="background: rgba(255, 255, 255, 0.06) !important; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; text-decoration: none; padding: 8px 18px; border-radius: 30px; font-weight: 600; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s ease; white-space: nowrap; flex-shrink: 0; cursor: pointer;">
                        Open <i class="fa-solid fa-up-right-from-square"></i>
                    </a>
                `;

                card.addEventListener('mouseenter', () => {
                    card.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                    card.style.background = 'rgba(255, 255, 255, 0.02)';
                });
                card.addEventListener('mouseleave', () => {
                    card.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    card.style.background = '#151518';
                });

                const visitBtn = card.querySelector('.btn-visit');
                visitBtn.addEventListener('mouseenter', () => {
                    visitBtn.style.background = '#ffffff';
                    visitBtn.style.color = '#070708';
                    visitBtn.style.borderColor = '#ffffff';
                });
                visitBtn.addEventListener('mouseleave', () => {
                    visitBtn.style.background = 'rgba(255, 255, 255, 0.06)';
                    visitBtn.style.color = '#ffffff';
                    visitBtn.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                });

                discoveredLinks.appendChild(card);
            });
        }

        // Render rare links if found
        if (rareResults.length > 0) {
            renderRareLinks(rareResults);
        } else {
            rareLinksBlock.style.display = 'none';
        }

        // Add a Scan Rare Networks button if RareMoviesFinder system has not run yet
        const containsFallback = results ? results.some(r => r.site === 'VK Video' || r.site === 'Mail.ru' || r.site === 'OK.ru') : false;
        if (!containsFallback) {
            const promptDiv = document.createElement('div');
            promptDiv.className = 'fallback-force-prompt';
            promptDiv.innerHTML = `
                <p>Still looking? Try searching our rare video indexers.</p>
                <button class="btn-deep-search" id="btn-trigger-deep-search">
                    <i class="fa-solid fa-magnifying-glass"></i> Scan Rare Networks
                </button>
            `;
            discoveredLinks.appendChild(promptDiv);
            
            document.getElementById('btn-trigger-deep-search').addEventListener('click', async (e) => {
                const btn = e.currentTarget;
                if (btn.classList.contains('loading')) return;
                
                btn.classList.add('loading');
                btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Scanning Rare Networks...`;
                
                try {
                    const movieTitleAndYear = selectedMovie.release_date
                        ? `${selectedMovie.title} (${selectedMovie.release_date.split('-')[0]})`
                        : selectedMovie.title;
                    const origTitle = selectedMovie.original_title || '';
                    
                    const res = await fetch(`/api/search-links/fallback?title=${encodeURIComponent(movieTitleAndYear)}&original_title=${encodeURIComponent(origTitle)}&t=${Date.now()}`);
                    const data = await res.json();
                    
                    if (data.status === 'success' && data.results && data.results.length > 0) {
                        promptDiv.remove();
                        const newFallbacks = data.results.map(item => ({ ...item, status: 'FOUND' }));
                        renderRareLinks(newFallbacks);
                    } else {
                        btn.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> No Links Found`;
                        setTimeout(() => {
                            btn.classList.remove('loading');
                            btn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Scan Rare Networks`;
                        }, 2500);
                    }
                } catch (err) {
                    console.error("Rare search failed:", err);
                    btn.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Scan Failed`;
                    setTimeout(() => {
                        btn.classList.remove('loading');
                        btn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Scan Rare Networks`;
                    }, 2500);
                }
            });
        }
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

    // ==========================================================================
    // Indexer Dashboard Controller
    // ==========================================================================
    const dashboardPageContainer = document.getElementById('dashboard-page-container');
    const sitesDashGrid = document.getElementById('sites-dash-grid');
    const btnPingAll = document.getElementById('btn-ping-all');
    const statTotalSites = document.getElementById('stat-total-sites');
    const statActiveSites = document.getElementById('stat-active-sites');
    const statOfflineSites = document.getElementById('stat-offline-sites');
    
    const STORAGE_DISABLED_SITES = 'lighthouse_disabled_sites';
    const STORAGE_PING_HISTORY = 'lighthouse_ping_history';
    let allSites = [];

    function getDisabledSites() {
        const list = localStorage.getItem(STORAGE_DISABLED_SITES);
        return list ? list.split(',').filter(Boolean) : [];
    }
    
    function saveDisabledSites(sites) {
        localStorage.setItem(STORAGE_DISABLED_SITES, sites.join(','));
    }

    function getPingHistory() {
        const history = localStorage.getItem(STORAGE_PING_HISTORY);
        return history ? JSON.parse(history) : {};
    }
    
    function savePingHistory(history) {
        localStorage.setItem(STORAGE_PING_HISTORY, JSON.stringify(history));
    }

    async function openDashboard(shouldPushState = true) {
        closeSSE();
        if (shouldPushState) {
            history.pushState({ type: 'dash' }, '', '/dash');
        }
        
        homePageContainer.style.display = 'none';
        movieDetailsPage.style.display = 'none';
        dashboardPageContainer.style.display = 'block';
        window.scrollTo(0, 0);
        
        topProgressBar.start();
        try {
            const r = await fetch('/api/dash/sites');
            allSites = await r.json();
            renderDashboardGrid();
        } catch(e) {
            console.error("Failed to load dashboard sites:", e);
            sitesDashGrid.innerHTML = `<div class="grid-placeholder"><p class="error">Failed to load indexers: ${e.message}</p></div>`;
        } finally {
            topProgressBar.done();
        }
    }

    function renderDashboardGrid() {
        if (!sitesDashGrid) return;
        sitesDashGrid.innerHTML = '';
        
        const disabledList = getDisabledSites();
        const pingHistory = getPingHistory();
        
        statTotalSites.textContent = allSites.length;
        
        let activeCount = 0;
        let offlineCount = 0;
        
        allSites.forEach(site => {
            const isDisabled = disabledList.includes(site.name);
            const history = pingHistory[site.name] || [];
            
            let statusClass = 'checking';
            let statusLabel = 'No Ping Status';
            if (isDisabled) {
                statusClass = 'disabled';
                statusLabel = 'Disabled';
            } else if (history.length > 0) {
                const lastStatus = history[history.length - 1];
                if (lastStatus === 'ACTIVE') {
                    statusClass = 'active';
                    statusLabel = 'Active';
                    activeCount++;
                } else {
                    statusClass = 'offline';
                    statusLabel = 'Offline';
                    offlineCount++;
                }
            } else {
                statusClass = 'active';
                statusLabel = 'Assumed Online';
                activeCount++;
            }
            
            const card = document.createElement('div');
            card.className = `site-dash-card ${isDisabled ? 'disabled' : ''}`;
            card.id = `site-card-${site.name.replace(/\s+/g, '_')}`;
            
            // Build history indicators (last 3 pings)
            let dotsHtml = '';
            for (let i = 0; i < 3; i++) {
                const stateIndex = history.length - 3 + i;
                const dotState = stateIndex >= 0 ? history[stateIndex] : null;
                
                let dotClass = '';
                if (dotState === 'ACTIVE') dotClass = 'active';
                else if (dotState === 'OFFLINE') dotClass = 'offline';
                
                dotsHtml += `<div class="ping-dot ${dotClass}" title="${dotState || 'No ping data yet'}"></div>`;
            }
            
            const purposeBadges = site.purpose.map(p => `<span class="meta-tag-badge purpose">${p}</span>`).join(' ');
            const languagePills = site.language.map(l => `<span class="meta-tag-badge">${l}</span>`).join(' ');

            card.innerHTML = `
                <div class="site-tile-left">
                    <div class="site-tile-brand">
                        <span class="site-card-name">${site.name}</span>
                        ${site.url ? `<a href="${site.url}" target="_blank" rel="noopener noreferrer" class="site-tile-url-link">${site.url}</a>` : ''}
                    </div>
                    ${site.search_endpoint ? `
                        <div class="site-tile-endpoint-wrap">
                            <span class="endpoint-label">Search Query Endpoint</span>
                            <code class="site-tile-endpoint-code" title="${site.search_endpoint}">${site.search_endpoint}</code>
                        </div>
                    ` : ''}
                </div>
                
                <div class="site-tile-meta">
                    <div class="meta-group">
                        <span class="meta-group-label">Capability</span>
                        <div class="meta-tags-row">${purposeBadges}</div>
                    </div>
                    <div class="meta-group">
                        <span class="meta-group-label">Languages</span>
                        <div class="meta-tags-row">${languagePills}</div>
                    </div>
                </div>
                
                <div class="site-tile-right">
                    <div class="ping-history-wrap">
                        <span style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase; margin-right:4px;">History:</span>
                        ${dotsHtml}
                    </div>
                    <span class="site-status-badge ${statusClass}" id="badge-${site.name.replace(/\s+/g, '_')}">${statusLabel}</span>
                    <button class="btn-toggle-site ${isDisabled ? '' : 'remove-mode'}" data-name="${site.name}">
                        <i class="fa-solid ${isDisabled ? 'fa-circle-check' : 'fa-trash-can'}"></i>
                        <span>${isDisabled ? 'Enable' : 'Remove'}</span>
                    </button>
                </div>
            `;
            
            // Toggle active state listener
            card.querySelector('.btn-toggle-site').addEventListener('click', () => {
                toggleSiteActive(site.name);
            });
            
            sitesDashGrid.appendChild(card);
        });
        
        statActiveSites.textContent = activeCount;
        statOfflineSites.textContent = offlineCount + disabledList.length;
    }

    function toggleSiteActive(siteName) {
        const disabledList = getDisabledSites();
        const index = disabledList.indexOf(siteName);
        
        if (index > -1) {
            disabledList.splice(index, 1);
        } else {
            disabledList.push(siteName);
        }
        saveDisabledSites(disabledList);
        renderDashboardGrid();
    }

    async function pingAllSites() {
        if (!btnPingAll || btnPingAll.classList.contains('loading')) return;
        
        btnPingAll.classList.add('loading');
        btnPingAll.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Checking Nodes...`;
        
        const disabledList = getDisabledSites();
        const pingHistory = getPingHistory();
        
        topProgressBar.start();
        
        const promises = allSites.map(async (site) => {
            if (disabledList.includes(site.name)) {
                return; // Don't ping disabled/removed sites
            }
            
            const badgeElement = document.getElementById(`badge-${site.name.replace(/\s+/g, '_')}`);
            if (badgeElement) {
                badgeElement.className = 'site-status-badge checking';
                badgeElement.textContent = 'Pinging...';
            }
            
            try {
                const r = await fetch(`/api/dash/ping-site?name=${encodeURIComponent(site.name)}`);
                const res = await r.json();
                
                let history = pingHistory[site.name] || [];
                history.push(res.status);
                if (history.length > 3) {
                    history = history.slice(-3);
                }
                pingHistory[site.name] = history;
            } catch (err) {
                let history = pingHistory[site.name] || [];
                history.push('OFFLINE');
                if (history.length > 3) {
                    history = history.slice(-3);
                }
                pingHistory[site.name] = history;
            }
        });
        
        await Promise.all(promises);
        
        savePingHistory(pingHistory);
        renderDashboardGrid();
        
        topProgressBar.done();
        btnPingAll.classList.remove('loading');
        btnPingAll.innerHTML = `<i class="fa-solid fa-network-wired"></i> Ping All Sites`;
    }

    if (btnPingAll) {
        btnPingAll.addEventListener('click', pingAllSites);
    }

    checkInitialRoute();
});
