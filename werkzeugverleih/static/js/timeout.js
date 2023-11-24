(function() {
  const idleDurationSecs = 60;    // X number of seconds
  const redirectUrl = '/index';  // Redirect idle users to this URL
  let idleTimeout; // variable to hold the timeout, do not modify

  const resetIdleTimeout = function() {
    // Clears the existing timeout
    if(idleTimeout) clearTimeout(idleTimeout);
    // Set a new idle timeout to load the redirectUrl after idleDurationSecs
    idleTimeout = setTimeout(() => location.href = redirectUrl, idleDurationSecs * 1000);
  };
  // Init on page load
  resetIdleTimeout();
  // Reset the idle timeout on any of the events listed below
  ['click', 'touchstart', 'mousemove', 'input', 'keydown'].forEach(evt =>
    document.addEventListener(evt, resetIdleTimeout, false)
  );
})();
/* based on: Samuel Liew 2018 https://stackoverflow.com/a/52142007 */
