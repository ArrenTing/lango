---
id: LG-015
title: Live camera text translation
status: backlog
priority: P3
milestone: M4 See and translate
mode: guided
labels: [camera, vision, investigation, privacy, realtime]
depends: [LG-006, LG-009]
---

## 🧭 The problem, in plain words

Point my phone at Vietnamese text (a menu, a sign, a recipe card, a letter, a text message on someone else's screen)
and see it in English almost immediately, overlaid on or under the live camera view. The web app asks for camera
permission the same way any site does. There's no app to install.

## 📱 Sketch

```
┌──────────────────────────────┐
│  [ live camera view ]        │
│   ┌────────────────┐         │
│   │ Phở bò tái  60k│ ◀── text the camera sees
│   └────────────────┘         │
├──────────────────────────────┤
│  Rare beef phở — 60,000₫     │ ◀── translation, updates as I move
│  ⏸ freeze   📋 copy          │
└──────────────────────────────┘
```

## ⚠️ What a web app can and can't do (verify in the investigation)

- ✅ **Camera:** `navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })`. The browser shows a
  permission prompt. It only works over **HTTPS**, so this depends on LG-008/LG-009 hosting.
- ❌ **Reading other apps' screens:** a browser tab can't see what's on screen in Messages, Zalo, and so on. Screen
  capture (`getDisplayMedia`) isn't available in mobile browsers. Workarounds: share a **screenshot** into lango
  (file picker / Web Share Target on Android), or point the camera at the other screen.
- ❓ **Background use:** the page must stay open in the foreground, and the camera stops when the tab is hidden.

## ✅ Done when

- [ ] "Camera" button asks for permission, shows the rear camera, and handles "denied" gracefully
- [ ] Frames are sampled (e.g. every ~1 s, only when the picture changed), never sent as a continuous video stream
- [ ] Detected text is translated to English and shown under the preview, updating as the view changes
- [ ] Freeze button to hold the current frame and translation for reading
- [ ] "Translate a screenshot" upload path for text from other apps
- [ ] Images are never stored or logged on the server; the camera turns off when leaving the view
- [ ] Security agent verdict: PASS

## ❓ Questions for the investigation agent

1. **Where does text recognition happen?** Compare three options on privacy, Vietnamese diacritics accuracy, latency, and cost:
   (a) send the frame to Claude vision, which reads and translates in one step;
   (b) on-device OCR in the browser (Tesseract.js with the `vie` model, or the experimental Shape Detection `TextDetector`),
   then send only the **text** to Claude;
   (c) a hybrid: on-device OCR detects "text changed", and only then a frame or text goes to Claude.
2. What frame size, sampling rate, and change detection keep it feeling real-time without a big API bill? Load the `claude-api`
   skill for image token costs.
3. iOS Safari and Android Chrome quirks: permission persistence, autofocus, torch, and "Add to Home Screen" (PWA) behaviour.
4. Can lango be an Android **share target** so "Share → lango" on a screenshot opens the translator?

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
