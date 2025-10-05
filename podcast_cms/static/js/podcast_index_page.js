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
