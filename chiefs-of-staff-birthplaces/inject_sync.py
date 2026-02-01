#!/usr/bin/env python3
# Inject iframe sync script into the map HTML

with open('docs/commanders-map.html', 'r', encoding='utf-8') as f:
    html = f.read()

sync_script = '''
<script>
window.addEventListener("message", function(event) {
  if (event.data.type === "changeLayer") {
    var layerMap = {
      "All": "Combined Summary",
      "Chiefs": "Chiefs of General Staff",
      "Army": "Army Commanders",
      "Navy": "Naval Commanders",
      "Air Force": "Air Force Commanders"
    };
    var targetLayer = layerMap[event.data.layer];
    if (!targetLayer) return;
    setTimeout(function() {
      var radios = document.querySelectorAll(".leaflet-control-layers-base input[type=radio]");
      radios.forEach(function(radio) {
        var label = radio.nextSibling ? radio.nextSibling.textContent.trim() : "";
        if (label.indexOf(targetLayer) >= 0 && !radio.checked) {
          radio.click();
        }
      });
    }, 100);
  }
});
</script>
'''

html = html.replace('</body>', sync_script + '</body>')

with open('docs/commanders-map.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✓ Iframe sync script injected into map")
