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
