---
id: LG-011
title: Split-screen conversation view
status: todo
priority: P1
milestone: M3 Conversation mode
mode: guided
labels: [ux, frontend, langgraph]
depends: [LG-006]
---

## 🧭 The problem, in plain words

When I'm talking with my mother-in-law, I want one screen that shows both sides of the conversation at once.
Her Vietnamese appears in **English** for me, and what I say appears in **Vietnamese** for her. Nobody has to
scroll or switch modes; we just read our own half.

## 📱 Sketch

Phone lies flat on the table between us. Her half is **upside down (rotated 180°)** so it reads the right way
up from her side of the table.

```
        she sits here ▼
┌──────────────────────────────┐
│    (rotated 180° — upside    │
│     down from where I sit)   │
│  "Mẹ khỏe không ạ?"          │  ← what I said, translated to Vietnamese
│  "Con ăn cơm chưa?"          │     newest line nearest HER edge
│  🇻🇳  HER HALF (Vietnamese)    │
├──────────── lango ───────────┤  ← input: type (voice later, LG-014)
│  "Have you eaten yet?"       │  ← what she said, translated to English
│  "I made phở today."         │     newest line nearest MY edge
│  🇬🇧  MY HALF (English)        │
└──────────────────────────────┘
        I sit here ▲
```

## ✅ Done when

- [ ] Portrait split screen: top half = Vietnamese (her side), bottom half = English (my side)
- [ ] Her half is rotated 180° **by default**, so she can read it from across the table without moving
- [ ] Mirrored layout: each half's newest message sits nearest its reader's edge and scrolls toward them
- [ ] Each message shows up in the reader's half in their language: my English → her half in Vietnamese,
      her Vietnamese → my half in English
- [ ] Language is detected per message, so neither of us taps a "who's speaking" button
- [ ] Each half auto-scrolls to its newest line independently, with large readable text
- [ ] Toggle to turn the rotation off (e.g. when we're side by side instead of across the table)
- [ ] Screen stays awake while in conversation mode (Wake Lock API), and the rotation doesn't fight the phone's auto-rotate
- [ ] Optional: small grey original text under each translation (on by default for my half, so I can learn)
- [ ] Streams word by word once LG-007 exists; until then, whole-message updates are fine
- [ ] Tested on my phone in a real conversation

## ❓ Open questions (decide at ticket start)

- Can she type on the phone too, or do I type everything she says? Voice (LG-014) makes this much easier.
- Should my half also show the Vietnamese I just "sent", so I can check it before she reads it?

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
