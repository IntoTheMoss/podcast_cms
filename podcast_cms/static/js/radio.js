/* Player for the live Icecast stream at radio.intothemoss.com.
 *
 * The waveform is drawn from a Web Audio AnalyserNode where it can be, and
 * from a synthetic squiggle where it cannot. Reading the stream through Web
 * Audio needs the Icecast response to be CORS-approved; if it ever stops
 * being so the browser silently feeds the analyser a flat line AND silences
 * playback, so there is a detector below that rebuilds the element without
 * Web Audio rather than leaving a player that looks alive but makes no sound.
 */
(function () {
  'use strict';

  var canvas = document.getElementById('radio-wave');
  var toggle = document.getElementById('radio-toggle');
  var muteButton = document.getElementById('radio-mute');
  var nowPlaying = document.getElementById('radio-now');
  var audio = document.getElementById('radio-audio');
  if (!canvas || !toggle || !audio) return;

  var streamUrl = audio.dataset.streamUrl;
  var statusUrl = audio.dataset.statusUrl;
  var reduceMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  var ctx = canvas.getContext('2d');
  var audioCtx = null;
  var analyser = null;
  var analyserData = null;
  var webAudioDisabled = false;
  var flatFrames = 0;

  var POINTS = 72;
  var energy = 0;       // eased 0..1: how far the line has opened up
  var targetEnergy = 0;
  var level = 0;        // eased peak amplitude from the analyser
  var looping = false;

  /* ---------------------------------------------------------------- canvas */

  function resize() {
    var ratio = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.round(rect.width * ratio));
    canvas.height = Math.max(1, Math.round(rect.height * ratio));
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  // Idle shape: three sines drifting against each other so the line never
  // repeats on an obvious beat. Kept to a few cycles across the width, well
  // under the sample count, or it aliases into noise instead of a squiggle.
  function synthetic(p, t) {
    return (
      Math.sin(p * 7.0 + t * 1.1) * 0.55 +
      Math.sin(p * 12.3 - t * 0.74) * 0.28 +
      Math.sin(p * 21.7 + t * 1.63) * 0.17
    );
  }

  function draw(now) {
    var t = now / 1000;
    var width = canvas.clientWidth;
    var height = canvas.clientHeight;
    var mid = height / 2;
    var i;

    var live = analyser && !audio.paused && !audio.muted;
    if (live) {
      analyser.getByteTimeDomainData(analyserData);
      var peak = 0;
      var flat = true;
      for (i = 0; i < analyserData.length; i += 4) {
        var v = Math.abs(analyserData[i] - 128);
        if (v > peak) peak = v;
        if (v > 1) flat = false;
      }
      // A perfectly flat signal for several seconds means a tainted graph,
      // not quiet music: recover rather than go on playing silence.
      if (flat && audio.currentTime > 3) {
        if (++flatFrames > 300) dropWebAudio();
      } else {
        flatFrames = 0;
      }
      level += (Math.min(1, peak / 90) - level) * 0.12;
    } else {
      level += (0 - level) * 0.06;
    }

    if (reduceMotion) {
      energy = targetEnergy;
    } else {
      energy += (targetEnergy - energy) * 0.05;
    }

    // Idle keeps a faint drift so the line always reads as a signal; playing
    // opens it up, with the analyser adding the detail on top. The constants
    // are chosen so a full-scale sample lands just inside the canvas.
    var amplitude = mid * (0.06 + energy * (0.13 + level * 0.28));

    ctx.clearRect(0, 0, width, height);

    var points = [];
    for (var n = 0; n <= POINTS; n++) {
      var p = n / POINTS;
      // Taper both ends so the line fades into the page instead of stopping.
      var taper = Math.sin(p * Math.PI);
      var value = synthetic(p * 2.0, reduceMotion ? 0 : t) * 0.4;
      if (live) {
        value += ((analyserData[Math.floor(p * (analyserData.length - 1))] - 128) / 128) * 1.6;
      }
      points.push({ x: p * width, y: mid + value * amplitude * taper });
    }

    var gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, 'rgba(143, 208, 122, 0)');
    gradient.addColorStop(0.15, 'rgba(143, 208, 122, 0.85)');
    gradient.addColorStop(0.5, 'rgba(216, 232, 207, 0.95)');
    gradient.addColorStop(0.85, 'rgba(143, 208, 122, 0.85)');
    gradient.addColorStop(1, 'rgba(143, 208, 122, 0)');

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = gradient;
    ctx.shadowColor = 'rgba(143, 208, 122, ' + (0.25 + energy * 0.35) + ')';
    ctx.shadowBlur = 14;
    ctx.lineWidth = 2.2;

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (var k = 1; k < points.length - 1; k++) {
      // Quadratic through the midpoints keeps the curve smooth and organic
      // rather than showing every sample point as a corner.
      var mx = (points[k].x + points[k + 1].x) / 2;
      var my = (points[k].y + points[k + 1].y) / 2;
      ctx.quadraticCurveTo(points[k].x, points[k].y, mx, my);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  function frame(now) {
    draw(now || 0);
    if (reduceMotion) {
      looping = false; // one-shot: redraw only when the state changes
      return;
    }
    window.requestAnimationFrame(frame);
  }

  function ensureFrame() {
    if (looping) return;
    looping = true;
    window.requestAnimationFrame(frame);
  }

  /* ------------------------------------------------------------ web audio */

  function setupAnalyser() {
    if (analyser || webAudioDisabled) return;
    var Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    try {
      audioCtx = new Ctx();
      var source = audioCtx.createMediaElementSource(audio);
      analyser = audioCtx.createAnalyser();
      // Small window on purpose: ~6ms of audio spread over the width reads as
      // a rolling wave, where a long window would alias into a fuzzy band.
      analyser.fftSize = 512;
      analyserData = new Uint8Array(analyser.fftSize);
      source.connect(analyser);
      analyser.connect(audioCtx.destination);
    } catch (e) {
      analyser = null;
      webAudioDisabled = true;
    }
  }

  // Once an element is routed through a MediaElementSource that routing is
  // permanent, so recovering means starting again with a fresh element.
  function dropWebAudio() {
    webAudioDisabled = true;
    analyser = null;
    flatFrames = 0;
    if (audioCtx) {
      audioCtx.close();
      audioCtx = null;
    }
    var fresh = audio.cloneNode(false);
    fresh.removeAttribute('crossorigin');
    fresh.removeAttribute('src');
    audio.pause();
    audio.parentNode.replaceChild(fresh, audio);
    audio = fresh;
    bindAudioEvents();
    start();
  }

  /* -------------------------------------------------------------- controls */

  function setIcons(playing) {
    toggle.querySelector('.icon-play').hidden = playing;
    toggle.querySelector('.icon-pause').hidden = !playing;
    toggle.setAttribute('aria-label', playing ? 'Pause the radio' : 'Play the radio');
    toggle.classList.toggle('is-playing', playing);
    ensureFrame();
  }

  function setStatus(text) {
    if (nowPlaying) nowPlaying.textContent = text;
  }

  function start() {
    audio.src = streamUrl;
    setupAnalyser();
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
    setStatus('Tuning in…');
    targetEnergy = 1;
    setIcons(true);
    var played = audio.play();
    if (played && played.catch) {
      played.catch(function () {
        targetEnergy = 0;
        setIcons(false);
        setStatus('Could not start the stream');
      });
    }
  }

  // A live stream has no meaningful paused position: drop the connection so
  // the next play reconnects at the live edge rather than behind it.
  function stop() {
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    targetEnergy = 0;
    setIcons(false);
    setStatus('Off air');
    pollNowPlaying();
  }

  function bindAudioEvents() {
    audio.addEventListener('playing', function () {
      targetEnergy = 1;
      setIcons(true);
      pollNowPlaying();
    });
    audio.addEventListener('waiting', function () {
      setStatus('Buffering…');
    });
    audio.addEventListener('error', function () {
      if (!audio.currentSrc) return; // fired by the deliberate teardown in stop()
      targetEnergy = 0;
      setIcons(false);
      setStatus('Stream unavailable');
    });
  }

  toggle.addEventListener('click', function () {
    if (audio.paused) start();
    else stop();
  });

  if (muteButton) {
    muteButton.addEventListener('click', function () {
      audio.muted = !audio.muted;
      muteButton.querySelector('.icon-unmuted').hidden = audio.muted;
      muteButton.querySelector('.icon-muted').hidden = !audio.muted;
      muteButton.setAttribute('aria-pressed', audio.muted ? 'true' : 'false');
      muteButton.setAttribute('aria-label', audio.muted ? 'Unmute' : 'Mute');
      ensureFrame();
    });
  }

  /* ----------------------------------------------------------- now playing */

  var pollTimer = null;

  function pollNowPlaying() {
    if (!statusUrl || !window.fetch) return;
    window.clearTimeout(pollTimer);
    fetch(statusUrl, { cache: 'no-store' })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        var source = data && data.icestats && data.icestats.source;
        if (Array.isArray(source)) source = source[0];
        var title = source && source.title;
        // Icecast prefixes every title with the artist, and the whole station
        // is Into the Moss, so the prefix is noise here.
        if (title) setStatus(title.replace(/^Into the Moss\s*[-–]\s*/i, ''));
      })
      .catch(function () {
        /* leave whatever the player state last set */
      })
      .then(function () {
        if (!audio.paused) pollTimer = window.setTimeout(pollNowPlaying, 15000);
      });
  }

  /* ----------------------------------------------------------------- init */

  window.addEventListener('resize', function () {
    resize();
    ensureFrame();
  });
  resize();
  bindAudioEvents();
  setIcons(false);
  setStatus('Off air');
  pollNowPlaying();
  ensureFrame();
})();
