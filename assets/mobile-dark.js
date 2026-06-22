/* ============================================================
   MOBILE DARK JS — shared across all 5 pages
   - Matrix code rain in hero (canvas)
   - Sticky mobile CTA bar
   - Scroll reveal animations
   ============================================================ */
(function() {
  const isMobile = window.matchMedia('(max-width: 768px)').matches;
  if (!isMobile) return;

  // 1) Matrix code rain — runs in any .hero with #matrixRain canvas
  const canvas = document.getElementById('matrixRain');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    const hero = canvas.parentElement;
    let animationId = null;

    const setSize = () => {
      canvas.width = hero.offsetWidth;
      canvas.height = hero.offsetHeight;
    };
    setSize();

    const katakana = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ';
    const latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const nums = '0123456789';
    const chars = katakana + latin + nums;
    const fontSize = 14;
    let columns = Math.floor(canvas.width / fontSize);
    let drops = Array(columns).fill(0).map(() => Math.random() * -100);
    const colorHead = '#B85C2C';
    const colorBody = 'rgba(184, 92, 44,';

    const draw = () => {
      ctx.fillStyle = 'rgba(10, 18, 40, 0.08)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = fontSize + 'px "JetBrains Mono", monospace';
      for (let i = 0; i < drops.length; i++) {
        const ch = chars.charAt(Math.floor(Math.random() * chars.length));
        const y = drops[i] * fontSize;
        ctx.fillStyle = i % 7 === 0 ? colorHead : colorBody + (0.5 + Math.random() * 0.4) + ')';
        ctx.fillText(ch, i * fontSize, y);
        if (y > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i] += 0.6;
      }
      animationId = requestAnimationFrame(draw);
    };
    draw();

    const resetDrops = () => {
      columns = Math.floor(canvas.width / fontSize);
      drops = Array(columns).fill(0).map(() => Math.random() * -100);
    };
    window.addEventListener('resize', () => { setSize(); resetDrops(); });

    // Pause when not in view (battery)
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        if (!animationId) draw();
      } else {
        if (animationId) { cancelAnimationFrame(animationId); animationId = null; }
      }
    });
    observer.observe(hero);
  }

  // 2) Sticky mobile CTA bar
  const ctaConfig = document.querySelector('[data-mobile-cta]');
  const ctaText = ctaConfig ? ctaConfig.dataset.mobileCta : 'https://adam-prism.online';
  const ctaBar = document.createElement('div');
  ctaBar.className = 'mobile-cta-bar';
  ctaBar.innerHTML = '<a href="' + ctaText + '" target="_blank" rel="noopener" data-ar="← جرب آدم" data-en="Try Adam →">Try Adam →</a>';
  document.body.appendChild(ctaBar);

  const updateCtaText = () => {
    const lang = document.documentElement.lang || 'ar';
    const a = ctaBar.querySelector('a');
    a.textContent = lang === 'ar' ? '← جرب آدم' : 'Try Adam →';
  };
  updateCtaText();
  document.querySelectorAll('.lang-toggle button').forEach(b => b.addEventListener('click', updateCtaText));

  // Hide CTA bar when scrolled to bottom (footer)
  const footer = document.querySelector('.footer');
  if (footer) {
    const footerObserver = new IntersectionObserver(entries => {
      ctaBar.style.display = entries[0].isIntersecting ? 'none' : 'block';
    });
    footerObserver.observe(footer);
  }

  // 3) Scroll reveal — fade in sections as they enter viewport
  const revealTargets = document.querySelectorAll('section, .big-number, .carnegie-cta, .industries, .compliance, .contact, header.hero, .manifesto, .contribute, .story-stage, .timeline, .production-grid, .contact-section, .allocation, .main');
  revealTargets.forEach(el => el.classList.add('reveal'));
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
  revealTargets.forEach(el => revealObserver.observe(el));
  setTimeout(() => document.querySelector('header.hero, .main')?.classList.add('is-visible'), 80);
})();
