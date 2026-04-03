Yoga Form Coach

Product vision:
Build a web app that acts like an at-home yoga form coach. A user opens the site, starts a guided practice session, grants camera and microphone access, and receives live spoken feedback on posture, balance, pacing, and breath-related cues while moving through poses.

Core user experience:
- User lands on a homepage that explains the product and starts a session.
- User can choose a short routine or free-practice mode.
- App captures live webcam video during the session.
- App sends live multimodal context to the Gemini Live API.
- App delivers short, low-latency spoken coaching responses through the user's current audio output.
- App avoids constant interruption and only speaks when a cue is useful.
- At the end of the session, the app saves notes in three sections:
  - what you did well
  - what to keep working on
  - what you learned today

Product requirements:
- Primary platform is the web.
- User should be able to start and stop a live coaching session easily.
- Live coaching should focus on form and alignment, not medical diagnosis.
- Feedback should be supportive, concise, and specific to visible body position.
- The app should maintain a per-session notes history.
- The app should feel feasible for a hackathon MVP while leaving room for a stronger post-hackathon architecture.

Implementation expectations:
- Use the Gemini Live API rather than a generic chat API.
- Treat live video observation and spoken feedback as first-class features.
- Include a realistic browser + backend architecture.
- Include session lifecycle handling, model prompting strategy, note persistence, and guardrails.
- Call out any browser or platform constraints around audio routing, latency, and session duration.

Output expectations:
Produce an implementation-ready plan for the product, with enough detail that an engineer could scaffold the app immediately after reading it.
