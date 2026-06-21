// ============================================================================
// AI GYM COACH - Enhanced Landing Page JavaScript
// Developer: NIKHIL MALI
// ============================================================================
// Features: Preloader, Scroll Progress, Particle System, 3D Card Tilt,
//           Scroll Reveal, Animated Counters, Smooth Scroll, Scroll Spy,
//           Mobile Menu, Cursor Glow, Typing Effect, Navbar Scroll, Parallax
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // ==========================================================================
  // UTILITY FUNCTIONS
  // ==========================================================================

  /** Throttle function — limits execution to once per `limit` ms */
  function throttle(fn, limit) {
    let lastCall = 0;
    let scheduled = null;
    return function (...args) {
      const now = performance.now();
      const remaining = limit - (now - lastCall);
      if (remaining <= 0) {
        if (scheduled) { cancelAnimationFrame(scheduled); scheduled = null; }
        lastCall = now;
        fn.apply(this, args);
      } else if (!scheduled) {
        scheduled = requestAnimationFrame(() => {
          lastCall = performance.now();
          scheduled = null;
          fn.apply(this, args);
        });
      }
    };
  }

  /** Debounce function — delays execution until `delay` ms after last call */
  function debounce(fn, delay) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  /** Check if the device supports touch */
  const isTouchDevice = () =>
    'ontouchstart' in window || navigator.maxTouchPoints > 0;

  /** Check if the user prefers reduced motion */
  const prefersReducedMotion = () =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /** Clamp a value between min and max */
  const clamp = (val, min, max) => Math.min(Math.max(val, min), max);

  /** Linear interpolation */
  const lerp = (start, end, factor) => start + (end - start) * factor;

  /** Ease-out exponential curve (for counter animation) */
  const easeOutExpo = (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));


  // ==========================================================================
  // 1. PRELOADER
  // ==========================================================================

  const preloader = document.getElementById('preloader');

  function hidePreloader() {
    if (!preloader) return;

    // Delay slightly so assets finish painting
    setTimeout(() => {
      preloader.classList.add('preloader-hidden');

      // After CSS transition completes, fully remove from flow
      preloader.addEventListener('transitionend', () => {
        preloader.style.display = 'none';
      }, { once: true });

      // Fallback: force hide if transitionend never fires
      setTimeout(() => {
        if (preloader.style.display !== 'none') {
          preloader.style.display = 'none';
        }
      }, 1500);
    }, 1500);
  }

  window.addEventListener('load', hidePreloader);


  // ==========================================================================
  // 2. SCROLL PROGRESS BAR
  // ==========================================================================

  const scrollProgressBar = document.querySelector('.scroll-progress');

  function updateScrollProgress() {
    if (!scrollProgressBar) return;

    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;

    scrollProgressBar.style.width = scrollPercent + '%';
  }


  // ==========================================================================
  // 3. PARTICLE SYSTEM
  // ==========================================================================

  const particleCanvas = document.getElementById('particles-canvas');
  let particles = [];
  let particleCtx = null;
  let particleAnimId = null;

  // Particle color palette — amber, cyan, white
  const PARTICLE_COLORS = [
    'rgba(245, 158, 11, ',  // amber
    'rgba(6, 182, 212, ',   // cyan
    'rgba(255, 255, 255, ', // white
  ];

  class Particle {
    constructor(canvasW, canvasH) {
      this.canvasW = canvasW;
      this.canvasH = canvasH;
      this.reset(true);
    }

    /** Reset particle to a random position (or bottom if recycling) */
    reset(randomY = false) {
      this.x = Math.random() * this.canvasW;
      this.y = randomY
        ? Math.random() * this.canvasH
        : this.canvasH + Math.random() * 40;
      this.radius = 1 + Math.random() * 2;
      this.speedY = 0.2 + Math.random() * 0.6;        // upward drift
      this.speedX = (Math.random() - 0.5) * 0.3;       // slight horizontal drift
      this.sinAmplitude = 0.3 + Math.random() * 0.7;   // sin wave amplitude
      this.sinFrequency = 0.005 + Math.random() * 0.01; // sin wave frequency
      this.phase = Math.random() * Math.PI * 2;
      this.opacity = 0.15 + Math.random() * 0.55;
      this.colorBase = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
      this.life = 0;
    }

    update() {
      this.life++;
      this.y -= this.speedY;
      this.x += this.speedX + Math.sin(this.life * this.sinFrequency + this.phase) * this.sinAmplitude;

      // Recycle when off-screen (top, left, or right)
      if (this.y < -10 || this.x < -10 || this.x > this.canvasW + 10) {
        this.reset(false);
      }
    }

    draw(ctx) {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = this.colorBase + this.opacity + ')';
      ctx.fill();
    }
  }

  function initParticles() {
    if (!particleCanvas) return;

    particleCtx = particleCanvas.getContext('2d');
    resizeParticleCanvas();

    // Determine particle count based on screen width
    const isMobile = window.innerWidth < 768;
    const count = isMobile
      ? 40 + Math.floor(Math.random() * 11) // 40-50
      : 80 + Math.floor(Math.random() * 21); // 80-100

    particles = [];
    for (let i = 0; i < count; i++) {
      particles.push(new Particle(particleCanvas.width, particleCanvas.height));
    }

    // Start animation loop
    if (particleAnimId) cancelAnimationFrame(particleAnimId);
    animateParticles();
  }

  function resizeParticleCanvas() {
    if (!particleCanvas) return;
    particleCanvas.width = window.innerWidth;
    particleCanvas.height = window.innerHeight;

    // Update existing particles with new dimensions
    particles.forEach((p) => {
      p.canvasW = particleCanvas.width;
      p.canvasH = particleCanvas.height;
    });
  }

  /** Draw connecting lines between nearby particles */
  function drawConnections(ctx) {
    const maxDist = 100;
    const maxDistSq = maxDist * maxDist;

    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const distSq = dx * dx + dy * dy;

        if (distSq < maxDistSq) {
          const dist = Math.sqrt(distSq);
          const opacity = (1 - dist / maxDist) * 0.15;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(245, 158, 11, ${opacity})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animateParticles() {
    if (!particleCtx) return;

    particleCtx.clearRect(0, 0, particleCanvas.width, particleCanvas.height);

    // Update & draw particles
    particles.forEach((p) => {
      p.update();
      p.draw(particleCtx);
    });

    // Draw connecting lines (skip on low-end / mobile if many particles)
    if (particles.length <= 60 || window.innerWidth >= 768) {
      drawConnections(particleCtx);
    }

    particleAnimId = requestAnimationFrame(animateParticles);
  }


  // ==========================================================================
  // 4. 3D CARD TILT EFFECT
  // ==========================================================================

  const tiltElements = document.querySelectorAll('[data-tilt]');
  const MAX_TILT = 15; // degrees

  function initTiltEffect() {
    if (isTouchDevice() || prefersReducedMotion()) return;

    tiltElements.forEach((card) => {
      // Create glare overlay
      const glare = document.createElement('div');
      glare.classList.add('tilt-glare');
      Object.assign(glare.style, {
        position: 'absolute',
        top: '0',
        left: '0',
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        borderRadius: 'inherit',
        opacity: '0',
        background:
          'linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0) 60%)',
        transition: 'opacity 0.3s ease',
        zIndex: '2',
      });

      // Ensure card can contain the glare
      if (getComputedStyle(card).position === 'static') {
        card.style.position = 'relative';
      }
      card.style.overflow = 'hidden';
      card.appendChild(glare);

      // Smooth transition baseline
      card.style.transition = 'transform 0.15s ease-out';
      card.style.willChange = 'transform';

      let tiltRAF = null;

      card.addEventListener('mousemove', (e) => {
        if (tiltRAF) cancelAnimationFrame(tiltRAF);

        tiltRAF = requestAnimationFrame(() => {
          const rect = card.getBoundingClientRect();
          const centerX = rect.left + rect.width / 2;
          const centerY = rect.top + rect.height / 2;

          // Normalized position: -1 to 1
          const normX = (e.clientX - centerX) / (rect.width / 2);
          const normY = (e.clientY - centerY) / (rect.height / 2);

          const tiltX = clamp(normX * MAX_TILT, -MAX_TILT, MAX_TILT);
          const tiltY = clamp(-normY * MAX_TILT, -MAX_TILT, MAX_TILT);

          card.style.transform =
            `perspective(1000px) rotateX(${tiltY}deg) rotateY(${tiltX}deg) scale3d(1.03, 1.03, 1.03)`;

          // Move glare based on mouse position
          const glareX = ((e.clientX - rect.left) / rect.width) * 100;
          const glareY = ((e.clientY - rect.top) / rect.height) * 100;
          glare.style.background =
            `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 60%)`;
          glare.style.opacity = '1';

          tiltRAF = null;
        });
      });

      card.addEventListener('mouseleave', () => {
        if (tiltRAF) { cancelAnimationFrame(tiltRAF); tiltRAF = null; }
        card.style.transform =
          'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        glare.style.opacity = '0';
      });

      card.addEventListener('mouseenter', () => {
        card.style.transition = 'transform 0.15s ease-out';
      });
    });
  }


  // ==========================================================================
  // 5. SCROLL REVEAL ANIMATION (IntersectionObserver)
  // ==========================================================================

  function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal');
    if (!revealElements.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            el.classList.add('active');

            // Stagger children with data-stagger attribute
            const staggerChildren = el.querySelectorAll('[data-stagger]');
            staggerChildren.forEach((child, i) => {
              child.style.transitionDelay = `${i * 100}ms`;
              child.classList.add('active');
            });

            // Unobserve — animate only once
            observer.unobserve(el);
          }
        });
      },
      {
        threshold: 0.15,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    revealElements.forEach((el) => observer.observe(el));
  }


  // ==========================================================================
  // 6. ANIMATED COUNTERS
  // ==========================================================================

  let countersTriggered = false;

  function animateCounters() {
    const metricVals = document.querySelectorAll('.metric-val');
    if (!metricVals.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !countersTriggered) {
            countersTriggered = true;
            observer.disconnect();

            metricVals.forEach((el) => {
              const rawText = el.textContent.trim();

              // Separate numeric part from suffix (e.g. '98%' → 98, '%')
              const match = rawText.match(/^([\d.]+)(.*)$/);
              if (!match) return;

              const targetVal = parseFloat(match[1]);
              const suffix = match[2] || '';
              const isFloat = rawText.includes('.');
              const duration = 2000; // ms
              const startTime = performance.now();

              el.textContent = '0' + suffix;

              function tick(now) {
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easedProgress = easeOutExpo(progress);
                const current = targetVal * easedProgress;

                el.textContent = (isFloat ? current.toFixed(1) : Math.floor(current)) + suffix;

                if (progress < 1) {
                  requestAnimationFrame(tick);
                } else {
                  el.textContent = (isFloat ? targetVal.toFixed(1) : targetVal) + suffix;
                }
              }

              requestAnimationFrame(tick);
            });
          }
        });
      },
      { threshold: 0.3 }
    );

    // Observe the parent container of metrics (or each metric directly)
    const metricsStrip =
      document.querySelector('.metrics-strip') ||
      document.querySelector('.metrics');
    if (metricsStrip) {
      observer.observe(metricsStrip);
    } else {
      metricVals.forEach((el) => observer.observe(el));
    }
  }


  // ==========================================================================
  // 7. SMOOTH SCROLL
  // ==========================================================================

  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener('click', (e) => {
        const href = anchor.getAttribute('href');
        if (!href || href === '#') return;

        const target = document.querySelector(href);
        if (!target) return;

        e.preventDefault();

        // Close mobile menu if open
        closeMobileMenu();

        // Calculate offset for fixed nav
        const nav = document.querySelector('.nav') || document.querySelector('nav');
        const navHeight = nav ? nav.offsetHeight : 0;
        const targetTop = target.getBoundingClientRect().top + window.scrollY - navHeight - 20;

        window.scrollTo({
          top: targetTop,
          behavior: prefersReducedMotion() ? 'auto' : 'smooth',
        });
      });
    });
  }


  // ==========================================================================
  // 8. SCROLL SPY
  // ==========================================================================

  function initScrollSpy() {
    const navLinks = document.querySelectorAll('.nav-link, .nav a[href^="#"]');
    if (!navLinks.length) return;

    // Gather all section IDs referenced by nav links
    const sections = [];
    navLinks.forEach((link) => {
      const href = link.getAttribute('href');
      if (href && href.startsWith('#') && href.length > 1) {
        const section = document.querySelector(href);
        if (section) sections.push({ id: href, el: section });
      }
    });

    if (!sections.length) return;

    function updateSpy() {
      const scrollY = window.scrollY;
      const nav = document.querySelector('.nav') || document.querySelector('nav');
      const offset = nav ? nav.offsetHeight + 60 : 100;
      let currentId = '';

      sections.forEach(({ id, el }) => {
        const top = el.offsetTop - offset;
        const bottom = top + el.offsetHeight;
        if (scrollY >= top && scrollY < bottom) {
          currentId = id;
        }
      });

      // If scrolled to bottom of page, highlight last section
      if (window.innerHeight + scrollY >= document.documentElement.scrollHeight - 50) {
        currentId = sections[sections.length - 1].id;
      }

      navLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (href === currentId) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      });
    }

    // Throttled scroll handler
    window.addEventListener('scroll', throttle(updateSpy, 100), { passive: true });
    updateSpy(); // initial check
  }


  // ==========================================================================
  // 9. MOBILE HAMBURGER MENU
  // ==========================================================================

  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');

  function closeMobileMenu() {
    if (hamburger) hamburger.classList.remove('active');
    if (mobileMenu) mobileMenu.classList.remove('active');
    document.body.style.overflow = '';
  }

  function initMobileMenu() {
    if (!hamburger) return;

    hamburger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = hamburger.classList.toggle('active');
      if (mobileMenu) mobileMenu.classList.toggle('active');

      // Prevent body scroll when menu is open
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    // Close on menu link click
    if (mobileMenu) {
      mobileMenu.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', closeMobileMenu);
      });
    }

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (
        hamburger.classList.contains('active') &&
        mobileMenu &&
        !mobileMenu.contains(e.target) &&
        !hamburger.contains(e.target)
      ) {
        closeMobileMenu();
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeMobileMenu();
    });
  }


  // ==========================================================================
  // 10. CURSOR GLOW EFFECT
  // ==========================================================================

  function initCursorGlow() {
    if (isTouchDevice()) return;

    const cursorGlow = document.querySelector('.cursor-glow');
    if (!cursorGlow) return;

    let mouseX = 0;
    let mouseY = 0;
    let glowX = 0;
    let glowY = 0;

    document.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    });

    function updateGlow() {
      // Smooth follow with lerp
      glowX = lerp(glowX, mouseX, 0.15);
      glowY = lerp(glowY, mouseY, 0.15);

      cursorGlow.style.transform = `translate(${glowX}px, ${glowY}px) translate(-50%, -50%)`;

      requestAnimationFrame(updateGlow);
    }

    requestAnimationFrame(updateGlow);
  }


  // ==========================================================================
  // 11. TYPING EFFECT
  // ==========================================================================

  function initTypingEffect() {
    const typingEl = document.querySelector('.typing-text');
    if (!typingEl) return;

    const phrases = [
      'Your form. Analyzed.',
      'Every rep. Perfected.',
      'Real-time. AI-powered.',
    ];

    let phraseIndex = 0;
    let charIndex = 0;
    let isDeleting = false;

    const TYPING_SPEED = 60;   // ms per character when typing
    const DELETING_SPEED = 30; // ms per character when deleting
    const PAUSE_AFTER_TYPE = 2000; // ms pause after finishing a phrase
    const PAUSE_AFTER_DELETE = 400; // ms pause before typing next phrase

    function tick() {
      const currentPhrase = phrases[phraseIndex];

      if (isDeleting) {
        charIndex--;
        typingEl.textContent = currentPhrase.substring(0, charIndex);

        if (charIndex === 0) {
          isDeleting = false;
          phraseIndex = (phraseIndex + 1) % phrases.length;
          setTimeout(tick, PAUSE_AFTER_DELETE);
          return;
        }

        setTimeout(tick, DELETING_SPEED);
      } else {
        charIndex++;
        typingEl.textContent = currentPhrase.substring(0, charIndex);

        if (charIndex === currentPhrase.length) {
          isDeleting = true;
          setTimeout(tick, PAUSE_AFTER_TYPE);
          return;
        }

        setTimeout(tick, TYPING_SPEED);
      }
    }

    // Ensure element has blinking cursor via CSS class
    typingEl.classList.add('typing-cursor');
    tick();
  }


  // ==========================================================================
  // 12. NAVBAR SCROLL EFFECT
  // ==========================================================================

  const nav = document.querySelector('.nav') || document.querySelector('nav');

  function updateNavScroll() {
    if (!nav) return;

    if (window.scrollY > 50) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  }


  // ==========================================================================
  // 13. PARALLAX EFFECT FOR FLOATING SHAPES
  // ==========================================================================

  function initParallax() {
    const shapes = document.querySelectorAll('.floating-shape');
    if (!shapes.length || prefersReducedMotion()) return;

    // Assign each shape a random speed factor
    const speedFactors = Array.from(shapes).map(
      () => 0.05 + Math.random() * 0.15  // 5-20% of scroll distance
    );

    function updateParallax() {
      const scrollY = window.scrollY;

      shapes.forEach((shape, i) => {
        const yOffset = scrollY * speedFactors[i];
        shape.style.transform = `translateY(${yOffset}px)`;
      });
    }

    window.addEventListener('scroll', throttle(updateParallax, 16), { passive: true });
    updateParallax(); // initial position
  }


  // ==========================================================================
  // UNIFIED SCROLL HANDLER (performance — single listener, multiple updates)
  // ==========================================================================

  const handleScroll = throttle(() => {
    updateScrollProgress();
    updateNavScroll();
  }, 16); // ~60fps

  window.addEventListener('scroll', handleScroll, { passive: true });


  // ==========================================================================
  // RESIZE HANDLER
  // ==========================================================================

  const handleResize = debounce(() => {
    resizeParticleCanvas();

    // Reinitialize particles on significant resize to adjust count
    if (
      (window.innerWidth < 768 && particles.length > 55) ||
      (window.innerWidth >= 768 && particles.length < 60)
    ) {
      if (particleAnimId) cancelAnimationFrame(particleAnimId);
      initParticles();
    }
  }, 250);

  window.addEventListener('resize', handleResize);


  // ==========================================================================
  // INITIALIZATION — Boot all features
  // ==========================================================================

  function init() {
    initParticles();
    initTiltEffect();
    initScrollReveal();
    animateCounters();
    initSmoothScroll();
    initScrollSpy();
    initMobileMenu();
    initCursorGlow();
    initTypingEffect();
    initParallax();

    // Run scroll-dependent updates once on load
    updateScrollProgress();
    updateNavScroll();
  }

  init();

  // Log confirmation (remove in production)
  console.log(
    '%c⚡ AI GYM COACH — All systems go.',
    'color: #f59e0b; font-size: 14px; font-weight: bold;'
  );
});
