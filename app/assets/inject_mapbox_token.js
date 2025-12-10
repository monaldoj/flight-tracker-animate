// Fetch Mapbox token at runtime and expose it globally
// fetch('/mapbox_token')
//   .then(response => response.json())
//   .then(data => {
//       console.log("Mapbox token injected at runtime.");
//       window.__MAPBOX_TOKEN__ = data.token;
//   })
//   .catch(err => console.error("Error injecting Mapbox token:", err));
fetch('/mapbox_token')
  .then(r => r.json())
  .then(data => {
      window.__MAPBOX_TOKEN__ = data.token;

      // Patch Kepler.gl runtime config when it becomes available
      const patchMapbox = () => {
          // Wait until Kepler is fully loaded
          if (window.keplerGl && window.keplerGl.map) {
              window.keplerGl.map.setAccessToken(data.token);
              console.log("Kepler GL token patched.");
          } else {
              setTimeout(patchMapbox, 50);
          }
      };

      patchMapbox();
  });