function handleScrollOrTouchEvents(path) {
    "ontouchstart" in window
      ? handleLogoVisibility("scroll")
      : handleLogoVisibility("mousemove");
}
handleScrollOrTouchEvents();

function handleLogoVisibility(eventType) {
  let x;
  try {
    document.addEventListener(
      eventType,
      function () {
        let logo = document.querySelector(".logo");
        if (x) {
          clearTimeout(x);
          removeLogo(logo);
        }
        x = setTimeout(() => {
          showLogo(logo);
        }, 1200);
      },
      false
    );
  } catch (e) {
    console.info(`TypeError: ${e}`);
  }
}
function removeLogo(logo) {
  if (!logo) return;
  try {
    logo.classList.add("hide");
    setTimeout(() => {
      logo.classList.add("hidden");
    }, 400);
  } catch (e) {
    console.info(`Can't remove ${logo} because it doesn't exist! (${e}).`);
  }
}
function showLogo(logo) {
  if (!logo) return;
  logo.classList.remove("hidden");
  setTimeout(() => {
    logo.classList.remove("hide");
  }, 100);
}

function setupProgressiveImageLoading() {
  const images = document.querySelectorAll('.episode-player-image img.placeholder');

  // Set up placeholders immediately
  images.forEach(img => {
    const placeholderUrl = img.dataset.placeholder;
    if (placeholderUrl) {
      const originalSrc = img.src;
      img.dataset.src = originalSrc; // Store original src
      img.src = placeholderUrl; // Set placeholder immediately
    }
  });

  // Use Intersection Observer for proper lazy loading
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          loadHighResImage(img);
          observer.unobserve(img);
        }
      });
    }, {
      rootMargin: '50px 0px' // Start loading 50px before entering viewport
    });

    images.forEach(img => {
      if (img.dataset.src) {
        imageObserver.observe(img);
      }
    });
  } else {
    // Fallback for browsers without IntersectionObserver
    images.forEach(img => {
      if (img.dataset.src) {
        loadHighResImage(img);
      }
    });
  }
}

function loadHighResImage(img) {
  const highResSrc = img.dataset.src;
  if (!highResSrc) return;

  const highResImg = new Image();
  highResImg.onload = function() {
    img.src = highResSrc;
    img.classList.remove('placeholder');
    img.classList.add('loaded');
  };

  highResImg.onerror = function() {
    img.classList.remove('placeholder');
    img.classList.add('loaded');
  };

  highResImg.src = highResSrc;
}

document.addEventListener('DOMContentLoaded', setupProgressiveImageLoading);

function setupSiteMenu() {
  const button = document.querySelector('.menu-button');
  const menu = document.getElementById('site-menu');
  if (!button || !menu) return;

  function closeMenu() {
    menu.hidden = true;
    button.setAttribute('aria-expanded', 'false');
  }

  function openMenu() {
    menu.hidden = false;
    button.setAttribute('aria-expanded', 'true');
  }

  button.addEventListener('click', (event) => {
    event.stopPropagation();
    menu.hidden ? openMenu() : closeMenu();
  });

  document.addEventListener('click', (event) => {
    if (!menu.hidden && !menu.contains(event.target) && event.target !== button) {
      closeMenu();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  const copyFeedButton = document.querySelector('.copy-feed-link');
  const toast = document.querySelector('.copy-toast');

  function showToast() {
    if (!toast) return;
    toast.hidden = false;
    clearTimeout(showToast._timeout);
    showToast._timeout = setTimeout(() => {
      toast.hidden = true;
    }, 3000);
  }

  function copyTextFallback(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
    } catch (e) {
      console.info(`Couldn't copy feed URL: ${e}`);
    }
    document.body.removeChild(textarea);
  }

  if (copyFeedButton) {
    copyFeedButton.addEventListener('click', (event) => {
      event.stopPropagation();
      const feedUrl = copyFeedButton.dataset.feedUrl;

      const done = () => {
        closeMenu();
        showToast();
      };

      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(feedUrl).then(done).catch(() => {
          copyTextFallback(feedUrl);
          done();
        });
      } else {
        copyTextFallback(feedUrl);
        done();
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', setupSiteMenu);
