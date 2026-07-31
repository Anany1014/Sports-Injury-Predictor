"""
backend.app.services.llm_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
OpenRouter AI LLM integration using model: nvidia/nemotron-nano-9b-v2:free
Generates personalized sports-science recovery prescriptions and streaming SSE responses.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, Any

import httpx

from backend.app.core.config import settings
from backend.app.schemas.prediction import AthleteRecord, PredictionResponse

logger = get_logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMRecoveryService:
    """Service to query OpenRouter LLM (Nvidia Nemotron Nano 9B) for Athletic Recovery Prescriptions."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model or "nvidia/nemotron-nano-9b-v2:free"

    def _build_prompt(self, record: AthleteRecord, prediction: PredictionResponse) -> list[dict[str, str]]:
        system_prompt = (
            "You are an elite Sports Science & Athletic Recovery AI Specialist. "
            "Your job is to analyze an athlete's biometrics, training load, and ML injury risk prediction, "
            "and output a structured 4-part athletic recovery and workload prescription. "
            "Be clear, concise, evidence-based, and professional."
        )

        user_prompt = f"""
Athlete Metadata:
- Athlete ID: {record.athlete_id}
- Sport: {record.sport} | Playing Position: {record.position}
- Demographics: Age {record.age}, Weight {record.weight_kg}kg, Height {record.height_cm}cm

Training & Recovery Metrics:
- Weekly Volume: {record.weekly_volume_hrs} hours
- Weekly Intensity (RPE): {record.weekly_intensity_score}/10
- Sleep Duration: {record.sleep_hours} hrs/night
- Heart Rate Variability (HRV): {record.hrv_ms} ms
- Soreness Rating: {record.soreness_score}/10
- Rest Days (Past Week): {record.rest_days} days
- Prior Injuries: {record.prior_injuries} (Last injury: {record.days_since_last_injury} days ago)

ML Injury Risk Output:
- Predicted Injury Probability: {prediction.injury_probability * 100:.1f}%
- Risk Category Label: {prediction.injury_risk_label}
- Top Contributing Risk Factors: {', '.join(prediction.top_contributing_factors)}

Please provide a structured Athletic Recovery Prescription in markdown with 4 sections:
1. 🚨 **Immediate Safety & Load Reduction Protocol**
2. 📉 **Next 3-Day RPE & Workload Target Caps**
3. 🧊 **Targeted Therapy & Mobility Routine**
4. 💤 **Sleep & Nutritional Recovery Optimization**
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()},
        ]

    def _build_recovery_tips_prompt(self, record: AthleteRecord, prediction: PredictionResponse) -> list[dict[str, str]]:
        """Build a short, natural, conversational recovery tips prompt."""
        system_prompt = (
            "You are a knowledgeable sports coach who gives honest, practical recovery advice. "
            "Write in a direct, friendly tone — like a coach talking to their athlete. "
            "Do NOT use formal markdown headers or corporate-sounding language. "
            "Do NOT start sentences with 'It is recommended' or 'Ensure that'. "
            "Write short, specific sentences. Be conversational and human."
        )

        risk = prediction.injury_risk_label
        prob = prediction.injury_probability * 100
        factors = ', '.join(prediction.top_contributing_factors[:3])

        user_prompt = f"""
Here is today's data for a {record.sport} {record.position}, age {record.age}:

- Sleep last night: {record.sleep_hours} hours
- HRV: {record.hrv_ms} ms
- Muscle soreness: {record.soreness_score}/10
- Training volume this week: {record.weekly_volume_hrs} hrs at RPE {record.weekly_intensity_score}/10
- Rest days this week: {record.rest_days}
- Injury history: {record.prior_injuries} past injuries, last one {record.days_since_last_injury:.0f} days ago
- ML model injury risk: {risk} ({prob:.0f}% probability)
- Key risk drivers: {factors}

Give 5 short, specific recovery tips for today based on this data. Each tip should be 1-2 sentences max. 
Write them as plain numbered points (1. 2. 3. etc.) with no sub-bullets or headings. 
Focus on what's most urgent given the data — don't give generic advice."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()},
        ]

    async def generate_recovery_plan(
        self, record: AthleteRecord, prediction: PredictionResponse
    ) -> dict[str, Any]:
        """Fetch non-streaming JSON response from OpenRouter API."""
        messages = self._build_prompt(record, prediction)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Sports Injury Predictor",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "stream": False,
            "messages": messages,
            "temperature": 0.5,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(OPENROUTER_URL, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()

                choice = data["choices"][0]["message"]
                content = choice.get("content", "").strip()

                return {
                    "status": "success",
                    "model": self.model,
                    "provider": data.get("provider", "Nvidia OpenRouter"),
                    "plan_markdown": content,
                }
        except Exception as e:
            logger.error(f"OpenRouter LLM query failed: {e}")
            # Fallback prescription generator
            return {
                "status": "fallback",
                "model": "Domain-Specific Sports Science AI Fallback Engine",
                "provider": "Local Fallback Engine",
                "plan_markdown": self._generate_fallback_markdown(record, prediction),
            }

    async def stream_recovery_plan(
        self, record: AthleteRecord, prediction: PredictionResponse
    ) -> AsyncGenerator[str, None]:
        """Stream SSE chunks from OpenRouter API ("stream": true)."""
        messages = self._build_prompt(record, prediction)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Sports Injury Predictor",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "stream": True,
            "messages": messages,
            "temperature": 0.5,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream("POST", OPENROUTER_URL, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(raw_data)
                                delta = json_data["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield f"data: {json.dumps({'content': delta})}\n\n"
                            except Exception:
                                pass
        except Exception as err:
            logger.error(f"Streaming error: {err}")
            fallback_text = self._generate_fallback_markdown(record, prediction)
            yield f"data: {json.dumps({'content': fallback_text})}\n\n"

    def _generate_fallback_markdown(self, record: AthleteRecord, prediction: PredictionResponse) -> str:
        label = prediction.injury_risk_label
        sport = record.sport
        pos = record.position
        return f"""
### 🏃‍♂️ Dynamic Warm-Up & Movement Activation
- **World's Greatest Stretch**: 2 sets × 6 reps per side (activates hip flexors, hamstrings, and thoracic spine).
- **Glute & Core Prep**: 2 sets × 12 reps of Banded Monster Walks and Single-Leg Glute Bridges for joint stabilization.
- **Sport-Specific Movement**: 5 minutes of progressive linear acceleration & low-intensity directional footwork for {sport} {pos}.

### 🧘‍♂️ Active Recovery & Mobility Exercises
- **90/90 Hip Mobility**: 3 minutes per side to open hip capsule and relieve groin tightness.
- **Hamstring & Calf PNF Stretch**: Hold 10s contract / 20s relax for 3 cycles targeting posterior chain.
- **Thoracic Extension & Foam Rolling**: 8 minutes targeting upper back and IT band tissue release.

### 🥗 Whole-Food Performance Diet & Meals
- **Recovery Lunch**: Grilled salmon or chicken breast with quinoa, steamed broccoli, and avocado slices for healthy fats.
- **Anti-Inflammatory Snack**: 250ml tart cherry juice mixed with blueberries and walnuts to accelerate muscle recovery.
- **Evening Dinner**: Lean turkey or tofu stir-fry with sweet potato and leafy spinach.

### 🛡️ Biometric Re-Entry & Safety Thresholds
- **HRV Baseline Check**: Morning HRV must recover above {record.hrv_ms + 5:.0f}ms before resuming RPE > 7 sessions.
- **Soreness Threshold**: Soreness score must drop below 4/10 before high-speed sprints.
- **Pain Warning**: Discontinue drill immediately if localized sharp joint or tendon discomfort occurs.
"""

    async def stream_recovery_tips(
        self, record: AthleteRecord, prediction: PredictionResponse
    ) -> AsyncGenerator[str, None]:
        """Stream short, conversational recovery tips via SSE."""
        messages = self._build_recovery_tips_prompt(record, prediction)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Sports Injury Predictor",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "stream": True,
            "messages": messages,
            "temperature": 0.75,
            "max_tokens": 512,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream("POST", OPENROUTER_URL, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(raw_data)
                                delta = json_data["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield f"data: {json.dumps({'content': delta})}\n\n"
                            except Exception:
                                pass
        except Exception as err:
            logger.error(f"Recovery tips streaming error: {err}")
            fallback = self._generate_fallback_tips(record, prediction)
            yield f"data: {json.dumps({'content': fallback})}\n\n"

    def _generate_fallback_tips(self, record: AthleteRecord, prediction: PredictionResponse) -> str:
        label = prediction.injury_risk_label
        sleep_msg = f"You only got {record.sleep_hours:.1f} hours — try to hit at least 8 tonight." if record.sleep_hours < 7.5 else f"Sleep was decent at {record.sleep_hours:.1f} hours. Keep that going."
        soreness = "High soreness" if record.soreness_score >= 7 else "Moderate soreness" if record.soreness_score >= 4 else "Low soreness"
        load_note = "Pull back on intensity for the next 2 days." if label == "HIGH" else "Keep sessions controlled this week." if label == "MEDIUM" else "You're managing load well."

        return (
            f"1. {sleep_msg}\n"
            f"2. {soreness} at {record.soreness_score}/10 — spend 15 minutes foam rolling before your next session.\n"
            f"3. Your HRV is at {record.hrv_ms} ms. {load_note}\n"
            f"4. Drink at least 500ml of water in the next hour and include electrolytes post-training.\n"
            f"5. {'Skip today\'s session — your body needs a full rest day.' if label == 'HIGH' else 'Stick to zone 1-2 cardio today if you must train — nothing above RPE 5.'}"
        )

    def _build_prescription_prompt(self, record: AthleteRecord, prediction: PredictionResponse) -> list[dict[str, str]]:
        """Build structured prescription prompt that returns 4 labeled parseable cards."""
        system_prompt = (
            "You are a precision sports science AI. Output ONLY the 4 labeled sections below, nothing else. "
            "No preamble, no summary. Each section MUST start with its exact label on its own line. "
            "Be specific with numbers. Use real physiological reasoning based on the athlete's data."
        )

        risk = prediction.injury_risk_label
        prob = prediction.injury_probability * 100
        factors = ", ".join(prediction.top_contributing_factors[:4])
        sleep_deficit = max(0, 8.0 - record.sleep_hours)
        rpe_cap = 4.0 if risk == "HIGH" else 5.5 if risk == "MEDIUM" else 7.0
        protein_g = round(record.weight_kg * 0.35)

        user_prompt = f"""Athlete: {record.sport} {record.position}, age {record.age}, {record.weight_kg}kg
Injury Risk: {risk} ({prob:.0f}%) | Risk factors: {factors}
Sleep: {record.sleep_hours}h | HRV: {record.hrv_ms}ms | Soreness: {record.soreness_score}/10
Weekly load: {record.weekly_volume_hrs}h @ RPE {record.weekly_intensity_score}/10 | Rest days: {record.rest_days}
Prior injuries: {record.prior_injuries} (last: {record.days_since_last_injury:.0f} days ago)

Respond with EXACTLY this structure, no extra text:

SLEEP_HEADLINE: [one sentence target, e.g. "Sleep deficit detected → extend by +{sleep_deficit:.1f}h tonight"]
SLEEP_TARGET: [specific hours target as a number, e.g. "9.0"]
SLEEP_DETAIL: [2 sentences max explaining why and how — specific to HRV {record.hrv_ms}ms and sleep {record.sleep_hours}h]

WORKLOAD_HEADLINE: [one sentence cap, e.g. "Cap RPE at {rpe_cap}/10 for next 48 hours"]
WORKLOAD_TARGET: [RPE cap as a number e.g. "{rpe_cap}"]
WORKLOAD_DETAIL: [2 sentences max — reference actual training load {record.weekly_volume_hrs}h and soreness {record.soreness_score}/10]

THERAPY_HEADLINE: [one sentence protocol name and duration]
THERAPY_TARGET: [duration in minutes as a number]
THERAPY_DETAIL: [2 sentences — specific body areas for this {record.sport} {record.position}, reference soreness {record.soreness_score}/10]

NUTRITION_HEADLINE: [one sentence protein + hydration directive]
NUTRITION_TARGET: [{protein_g}g protein + hydration target in ml]
NUTRITION_DETAIL: [2 sentences — specific timing windows and electrolyte reasoning for this athlete]"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()},
        ]

    async def stream_prescription(
        self, record: AthleteRecord, prediction: PredictionResponse
    ) -> AsyncGenerator[str, None]:
        """Stream structured 4-card prescription via SSE."""
        messages = self._build_prescription_prompt(record, prediction)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Sports Injury Predictor",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "stream": True,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 700,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream("POST", OPENROUTER_URL, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(raw_data)
                                delta = json_data["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield f"data: {json.dumps({'content': delta})}\n\n"
                            except Exception:
                                pass
        except Exception as err:
            logger.error(f"Prescription streaming error: {err}")
            yield f"data: {json.dumps({'content': self._generate_fallback_prescription(record, prediction)})}\n\n"

    def _generate_fallback_prescription(self, record: AthleteRecord, prediction: PredictionResponse) -> str:
        risk = prediction.injury_risk_label
        sleep_deficit = max(0, 8.5 - record.sleep_hours)
        rpe_cap = 4.0 if risk == "HIGH" else 5.5 if risk == "MEDIUM" else 7.0
        protein_g = round(record.weight_kg * 0.35)
        therapy_min = 25 if risk == "HIGH" else 20 if risk == "MEDIUM" else 15
        water_ml = 800 if risk == "HIGH" else 600

        return (
            f"SLEEP_HEADLINE: Sleep deficit detected → extend by +{sleep_deficit:.1f}h tonight\n"
            f"SLEEP_TARGET: {min(9.5, record.sleep_hours + sleep_deficit):.1f}\n"
            f"SLEEP_DETAIL: HRV at {record.hrv_ms}ms suggests incomplete recovery. Aim for {min(9.5, record.sleep_hours + sleep_deficit):.1f}h uninterrupted. Avoid screens 45min before bed.\n\n"
            f"WORKLOAD_HEADLINE: Cap training RPE at {rpe_cap}/10 for next 48 hours\n"
            f"WORKLOAD_TARGET: {rpe_cap}\n"
            f"WORKLOAD_DETAIL: Weekly volume at {record.weekly_volume_hrs}h is {'elevated' if record.weekly_volume_hrs > 15 else 'moderate'} with soreness {record.soreness_score}/10. No high-intensity sessions until HRV recovers above baseline.\n\n"
            f"THERAPY_HEADLINE: {therapy_min}-min cryotherapy + lower limb mobility protocol\n"
            f"THERAPY_TARGET: {therapy_min}\n"
            f"THERAPY_DETAIL: Foam roll hamstrings, calves and hip flexors for 12 minutes. Follow with 10-min cold water immersion at 10–12°C to reduce inflammation markers.\n\n"
            f"NUTRITION_HEADLINE: {protein_g}g protein + {water_ml}ml water within 30min post-session\n"
            f"NUTRITION_TARGET: {protein_g}g protein + {water_ml}ml\n"
            f"NUTRITION_DETAIL: At {record.weight_kg}kg bodyweight target {protein_g}g fast-digesting protein immediately post-session. Add sodium electrolytes to first {water_ml}ml of post-session fluid.\n"
        )

    # ─────────────────────────────────────────────────────────
    # Unified Full Prescription: 4 Cards + Detailed Narrative
    # ─────────────────────────────────────────────────────────

    def _build_full_prescription_prompt(self, record: AthleteRecord, prediction: PredictionResponse) -> list[dict[str, str]]:
        """Build a single unified prompt that returns 4 metric cards + a detailed narrative plan."""
        system_prompt = (
            "You are a Head Strength & Conditioning Coach and Sports Scientist at a Premier High-Performance Center. "
            "Your output has two parts separated by '---DETAIL---' on its own line.\n"
            "PART 1: Exactly 12 lines for the 4 labeled metric blocks. No extra text before them.\n"
            "PART 2: Practical athletic execution directives written in direct, tactical coaching language. "
            "IMPORTANT DIRECTIVE: DO NOT REPEAT the sleep targets, RPE cap numbers, therapy minutes, or protein/water quantities "
            "already stated in Part 1. Instead, provide NEW practical protocols: (1) Dynamic Warm-Up Exercises, "
            "(2) Active Recovery & Mobility Drills, (3) Whole-Food Performance Diet & Meals, and (4) Biometric Re-Entry Thresholds. "
            "Be specific with real exercise names, stretches, and whole food choices tailored for this athlete (~60-80 words per section)."
        )

        risk = prediction.injury_risk_label
        prob = prediction.injury_probability * 100
        factors = ", ".join(prediction.top_contributing_factors[:4])
        sleep_deficit = max(0.0, 8.5 - record.sleep_hours)
        rpe_cap = 4.0 if risk == "HIGH" else 5.5 if risk == "MEDIUM" else 7.0
        protein_g = round(record.weight_kg * 0.35)
        water_ml = 750 if risk == "HIGH" else 600
        therapy_min = 25 if risk == "HIGH" else 20 if risk == "MEDIUM" else 15

        user_prompt = f"""Athlete: {record.sport} {record.position}, age {record.age}, {record.weight_kg}kg, {record.height_cm}cm
Injury Risk: {risk} ({prob:.0f}%) | Key drivers: {factors}
Sleep: {record.sleep_hours}h | HRV: {record.hrv_ms}ms | Soreness: {record.soreness_score}/10
Weekly load: {record.weekly_volume_hrs}h @ RPE {record.weekly_intensity_score}/10 | Rest days: {record.rest_days}
Injury history: {record.prior_injuries} prior injuries (last: {record.days_since_last_injury:.0f} days ago)

PART 1 — output EXACTLY these 12 lines, nothing else before '---DETAIL---':

SLEEP_HEADLINE: Sleep {"deficit detected → extend by +" + f"{sleep_deficit:.1f}h tonight" if sleep_deficit > 0 else "adequate — maintain current schedule"}
SLEEP_TARGET: {min(9.5, record.sleep_hours + sleep_deficit):.1f}
SLEEP_DETAIL: [2 sentences specific to HRV {record.hrv_ms}ms and {record.sleep_hours}h sleep]

WORKLOAD_HEADLINE: Cap RPE at {rpe_cap}/10 for next 48 hours
WORKLOAD_TARGET: {rpe_cap}
WORKLOAD_DETAIL: [2 sentences on {record.weekly_volume_hrs}h weekly load and soreness {record.soreness_score}/10]

THERAPY_HEADLINE: [specific therapy protocol and total duration for {record.sport} {record.position}]
THERAPY_TARGET: {therapy_min}
THERAPY_DETAIL: [2 sentences — specific body areas and modalities for this athlete]

NUTRITION_HEADLINE: {protein_g}g protein + {water_ml}ml hydration within 30min post-session
NUTRITION_TARGET: {protein_g}g + {water_ml}ml
NUTRITION_DETAIL: [2 sentences on protein timing and electrolyte strategy for {record.weight_kg}kg athlete]

---DETAIL---

PART 2 — Write 4 NEW practical sections with these exact headings (DO NOT repeat Part 1 numbers; give exercises, warm-ups, meals, re-entry rules):

### 🏃‍♂️ Dynamic Warm-Up & Movement Activation
### 🧘‍♂️ Active Recovery & Mobility Exercises
### 🥗 Whole-Food Performance Diet & Meals
### 🛡️ Biometric Re-Entry & Safety Thresholds"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()},
        ]

    async def stream_full_prescription(
        self, record: AthleteRecord, prediction: PredictionResponse
    ) -> AsyncGenerator[str, None]:
        """Stream unified prescription: 4 metric cards + detailed narrative in one SSE stream."""
        messages = self._build_full_prescription_prompt(record, prediction)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Sports Injury Predictor",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "stream": True,
            "messages": messages,
            "temperature": 0.45,
            "max_tokens": 1600,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", OPENROUTER_URL, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(raw_data)
                                delta = json_data["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield f"data: {json.dumps({'content': delta})}\n\n"
                            except Exception:
                                pass
        except Exception as err:
            logger.error(f"Full prescription streaming error: {err}")
            # Fallback: combine both fallback generators
            fb_cards = self._generate_fallback_prescription(record, prediction)
            fb_detail = self._generate_fallback_markdown(record, prediction)
            yield f"data: {json.dumps({'content': fb_cards + chr(10) + '---DETAIL---' + chr(10) + fb_detail})}\n\n"


