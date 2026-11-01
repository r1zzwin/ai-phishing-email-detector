# Architecture

## System architecture

```mermaid
flowchart LR
    U[User in browser] -->|form| F[Flask routes]
    F --> V[Input validation]
    V --> R[Rule engine]
    V --> O[Ollama client]
    O -->|HTTP localhost 11434| M[(Ollama with llama3.2:3b)]
    R --> S[Scoring]
    O --> S
    S --> D[(SQLite scans.db)]
    S --> F
    F -->|HTML result| U
```

| Part | Responsibility |
|------|----------------|
| Frontend (templates, CSS, JS) | Form, result page, history page, confirmation boxes, copy button |
| Flask routes | Receive requests, call the other parts, render pages, send downloads |
| Validation | Trim input, check required fields and length limits |
| Rule engine | Five documented indicators, deterministic, capped at 60 points |
| Ollama client | Status check, prompt, timeout handling, validation of the model's JSON |
| Scoring | Rules (0-60) plus AI verdict (0-40), clamped to 0-100, mapped to a category |
| SQLite | Saves scan history. The email body is never stored |

## Request flow

```mermaid
flowchart TD
    A[User enters sender, subject and body] --> B[Validate and normalize input]
    B -->|invalid| C[Show error messages]
    B -->|valid| D[Rule-based checks]
    D --> E[Send email text to Ollama]
    E -->|Ollama off or bad output| F[Use rules only]
    E -->|valid JSON| G[Validate AI result]
    F --> H[Calculate score and category]
    G --> H
    H --> I[Save scan to SQLite without the body]
    I --> J[Show score, evidence and safe next steps]
```