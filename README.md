# Safe2Peak — Altitude Sickness Risk Analyzer

Safe2Peak is a responsive educational decision-support app for altitude trip planning and symptom screening. This React/Vite edition combines the clinical logic of the original Streamlit application with the visual system of the Safe2peak UI concept.

## Features

- Altitude categories from low altitude through the death zone
- Personal history and ascent-rate risk factors
- Simplified four-domain AMS symptom screen
- Explicit HACE/HAPE red-flag screening and emergency descent advice
- Responsive, mobile-first dashboard
- Conservative day-by-day sleeping-altitude and rest-day planner
- Pre-departure, medication-safety and field-action guidance
- No client-side API keys, accounts, tracking, or simulated “live” weather

## Run locally

```bash
npm install
npm run dev
```

## Verify and build

```bash
npm run build
```

## Deploy to Vercel

Import this repository in Vercel. Framework preset, build command, output directory, and SPA fallback are declared in `vercel.json`.

## Safety

This application is educational and is not a diagnostic device. Severe or worsening symptoms require immediate descent and urgent medical/rescue assistance.
