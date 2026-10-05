# Own images for cases / Eigene Bilder für Fälle

Put PNG, JPEG or WebP images (max. 400 kB each) in this folder and list them in `data/case-media.json`. `python scripts/manage.py build` embeds them into `assets/catalog.js` and `standalone.html`. The game shows them in the explanation of the case, after the player has answered.

```json
[
  {
    "case": "ed-torsion",
    "file": "media/torsion-sketch.png",
    "alt": {"en": "Sketch of a twisted spermatic cord", "de": "Skizze eines verdrehten Samenstrangs", "es": "Esquema de un cordón espermático torcido"},
    "caption": {"en": "Torsion twists the cord.", "de": "Bei der Torsion verdreht sich der Samenstrang.", "es": "La torsión retuerce el cordón."},
    "credit": "Own drawing, Dr. Example",
    "license": "CC BY 4.0"
  }
]
```

**Rights and privacy.** Use only images you made yourself, or images with a licence that permits redistribution, such as CC BY or CC0. Name the source in `credit` and the licence in `license`; the build refuses an image without them. Never add identifiable patient images or anything without documented consent. Wikimedia Commons lets you filter by licence. Many radiology teaching sites do **not** allow redistribution.

**Rechte und Datenschutz.** Nur eigene Bilder oder Bilder mit weiterverbreitbarer Lizenz (z. B. CC BY, CC0) verwenden; Quelle in `credit`, Lizenz in `license` eintragen – ohne beides bricht der Build ab. Keine identifizierbaren Patientenbilder und nichts ohne dokumentierte Einwilligung.

SVG files are not accepted here, because SVG can contain scripts. Teaching drawings in SVG belong in `data/schemas.json`, which allows only plain drawing elements.
