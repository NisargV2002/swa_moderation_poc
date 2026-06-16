# SWA Moderation POC
### AI-Powered Content Moderation Pipeline — Sustainable World Alliance

> Automated moderation engine for sustainability project submissions, built on a modular Azure-native pipeline combining rule-based logic and LLM reasoning.

---

## Overview

The **SWA Moderation POC** is a cloud-native backend system that automatically analyses project submissions on the **SDGicity / Sustainable World Alliance (SWA)** platform against a suite of moderation policies. It uses a shared 17-module pipeline to evaluate submissions across 6 policy domains, combining deterministic rule-based checks with Azure OpenAI (GPT) for semantic analysis.

Built as part of a university capstone project under **Top Layer Solutions**.

---

## Key Features

- **17-module shared processing pipeline** — runs once per submission, feeds all policies simultaneously
- **6 policy domains** — Legal, Regulatory, Offensive Content, Malicious Intent, Nuisance, and Project Type
- **LLM-driven semantic analysis** — Azure OpenAI (GPT) for contextual reasoning, claim detection, and policy interpretation
- **Config-driven policy expansion** — new policies added with zero changes to shared module code
- **Per-policy fault isolation** — a single module failure never aborts the full pipeline
- **Tier-based decision engine** — structured Approve / Approve with Advisory / Request Amendment / Reject / Escalate outcomes
- **Full audit trail** — all intermediate and final outputs persisted to Azure SQL
- **80+ case labelled test suite** — accuracy benchmarked per policy group

---

##  Architecture

```
Moderation UI
    └──▶ FastAPI / Azure Functions Orchestrator
              └──▶ Project Data Access Layer (Azure SQL)
                        └──▶ Core Moderation Pipeline (M01–M15)
                                  ├── Shared Artifacts (normalised text, entities, claims)
                                  └── Policy Workspaces (per-policy outcomes)
                                            └──▶ M16 Severity & Action Engine
                                                      └──▶ M17 Result Packaging & Persistence
                                                                └──▶ Results UI
```

### Module Summary

| Module | Purpose |
|--------|---------|
| M01 | Project Data Assembly |
| M02 | Text Normalisation & Span Mapping |
| M03 | Structural & Rule-Based Signals |
| M04 | Link & Domain Extraction |
| M05 | Entity & PII Extraction |
| M06 | Semantic Content Classification *(Azure OpenAI)* |
| M07 | Claim Detection & Structuring |
| M08 | Evidence, Attribution & Disclosure Detection |
| M09 | Context & Exception Reasoning *(Azure OpenAI)* |
| M10 | Privacy, Consent & Exposure Reasoning |
| M11 | Threat, Harm & Allegation Reasoning |
| M12 | Malicious Delivery & Identity Abuse |
| M13 | Historical Comparison *(optional)* |
| M14 | Text Similarity & Copy-Paste Risk *(optional)* |
| M15 | Attachment / Media Analysis *(optional)* |
| M16 | Policy Aggregation, Severity & Action Engine |
| M17 | Result Packaging & Persistence |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| API Framework | FastAPI + Uvicorn |
| Serverless | Azure Functions v4 |
| Database | Azure SQL Server (pyodbc) |
| AI / LLM | Azure OpenAI — `gpt-5.4-mini` |
| Secrets | Azure Key Vault (Managed Identity) |
| Frontend | HTML / JS — served via `python -m http.server` |

---

## Project Structure

```
swa_moderation_poc/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── moderation_engine.py       # Core pipeline orchestrator
│   ├── db.py                      # Azure SQL connection layer
│   └── modules/                   # M01–M17 module implementations
├── config/
│   ├── settings.py                # Environment config
│   └── policies/                  # Per-policy config files (LEGAL, REG, MAL, OFF, NUIS, TYPE)
├── policy_registry.py             # Policy registration — add new policies here
├── generic_policy_runner.py       # Shared policy execution logic
├── prompt_library/                # Structured prompts per policy/module
├── function_app.py                # Azure Functions entry point
├── frontend/
│   └── index.html                 # Standalone moderation UI
└── tests/
    └── LEGAL_PolicyTestSuite/     # 80+ labelled test cases
```

---

## Getting Started

### Prerequisites

- Python 3.12
- Azure account with the following services provisioned:
  - Azure SQL Server
  - Azure OpenAI (with a GPT deployment)
  - Azure Key Vault
  - Azure Functions (for production deployment)

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/swa-moderation-poc.git
cd swa-moderation-poc

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your Azure credentials (see Configuration section below)

# 5. Start the API server
uvicorn app.main:app --reload --port 8000

# 6. Serve the frontend (in a separate terminal)
cd frontend
python -m http.server 3000
```

Then open `http://localhost:3000` in your browser.

>  **Note:** Do not open `index.html` directly via `file://` — it will fail due to CORS restrictions. Always serve it via `http.server`.

---

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Azure SQL
AZURE_SQL_SERVER=<your-server>.database.windows.net
AZURE_SQL_DATABASE=<your-database>
AZURE_SQL_USERNAME=<your-username>
AZURE_SQL_PASSWORD=<your-password>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_VERSION=2025-04-01-preview
AZURE_OPENAI_API_KEY=<your-api-key>

# Azure Key Vault (optional for local dev)
AZURE_KEY_VAULT_URL=https://<your-keyvault>.vault.azure.net/
```

>  **Security:** Never commit `.env` to version control. In production, credentials are managed via Azure Key Vault with Managed Identity — no secrets in code or config files.

---

## Adding a New Policy

The architecture is designed for zero-touch policy expansion:

1. Create a new config file in `config/policies/` (e.g., `REG-05.json`)
2. Add a prompt entry to `prompt_library/`
3. Register the policy in `policy_registry.py`

No shared module code needs to be modified.

---

## Database Schema

Results are persisted across four Azure SQL tables:

| Table | Contents |
|-------|---------|
| `ModerationRun` | Run metadata (ID, timestamp, submission reference) |
| `ModerationModuleResult` | Per-module shared artifact outputs |
| `ModerationPolicyModuleResult` | Per-policy, per-module workspace outcomes |
| `ModerationFinalPolicyResult` | Final decision, severity, action, evidence per policy |

---

## Policy Domains Covered

| Policy Group | Policies | Description |
|-------------|---------|-------------|
| LEGAL | LEGAL-01 to LEGAL-05 | Legal threats, privacy, consent, defamation |
| REG | REG-01 to REG-04 | Regulatory and compliance claims |
| MAL | MAL-01 to MAL-04 | Malicious intent, phishing, impersonation |
| OFF | OFF-01 to OFF-03 | Offensive and harmful content |
| NUIS | NUIS-01 to NUIS-04 | Nuisance, spam, repetitive content |
| TYPE-PROJECT | TYPE-PROJECT-01 | Project type and submission validity |

---

## Testing

An 80+ case labelled test suite (`LEGAL_PolicyTestSuite`) covers LEGAL-01 through LEGAL-05 across 4 outcome tiers.

```bash
# Run the test suite (ensure ENABLED_POLICIES is scoped to the target group only)
python -m pytest tests/
```

> ⚠️ **Important:** When running accuracy tests, set `ENABLED_POLICIES` to only the policy group under test. Mixing policy groups inflates M99 severity aggregation and corrupts accuracy measurements.

---

## Azure Deployment Notes

- **Azure SQL Firewall:** Azure SQL uses IP allowlisting. If you see connection timeouts, add your current IP in the Azure Portal under `SQL Server → Networking → Firewall Rules`.
- **Key Vault + Managed Identity:** In production, the Function App's system-assigned Managed Identity is granted `Key Vault Secrets User` access — no credentials are stored in environment variables.
- **Azure Functions:** Deploy using the Azure Functions Core Tools or VS Code Azure extension. Ensure `AzureWebJobsStorage` and application settings are configured in the Function App.

---

## Team

| Name | Role |
|------|------|
| Kirtan | Frontend Engineering, Prompt Engineering |
| Nisarg Vaishnav | Backend Development, AI Analysis Engine |

University Capstone Project — Top Layer Solutions | March–June 2026

---

##  Licence

This project was developed as part of a university capstone. Please contact the authors before reuse.
