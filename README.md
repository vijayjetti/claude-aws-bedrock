# Amazon Bedrock — Claude Setup

This documents how [`001_Api_Requests.ipynb`](001_Api_Requests.ipynb) was set up to call Claude models through Amazon Bedrock, including the issues hit along the way and how they were resolved.

## Environment

- Python 3.14.5, virtualenv at `.venv`
- Packages: `boto3`, `anthropic[bedrock]`, `python-dotenv`, `jupyter`, `ipykernel`
- AWS region: `us-west-2`
- AWS identity used: IAM user `vjuser1` (account `671192919555`)

## 1. Credentials

Bedrock auth is standard AWS credentials (access key / secret key / session token), not a separate API key.

- Credentials are stored in a local **`.env`** file at the project root — never hardcoded in the notebook.
- **`.gitignore`** excludes `.env` (and `.env.*`, except `.env.example`) from version control.
- The notebook loads credentials via `python-dotenv`'s `load_dotenv()` and validates that `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` are present before proceeding.

`.env` format:

```
AWS_ACCESS_KEY_ID=<your key>
AWS_SECRET_ACCESS_KEY=<your secret>
AWS_SESSION_TOKEN=<only needed for temporary/STS credentials>
AWS_REGION=us-west-2
```

> ⚠️ **Security note:** an earlier access key was accidentally pasted into chat and into the notebook directly. It was rotated in IAM and replaced. Never paste real credentials into a notebook cell, a chat, or any file that isn't `.env`-gitignored.

## 2. Client setup

Two ways to call Claude on Bedrock were set up in the notebook:

- **Option A — boto3 (native AWS SDK)**, calling `bedrock-runtime`'s `Converse` API directly. **This is the one that works end-to-end on this account** and is what the notebook's test cell uses.
- **Option B — Anthropic SDK's `AnthropicBedrockMantle` client**, which gives the same `messages.create(...)` interface as the first-party Anthropic SDK. Left in the notebook for reference, but see the model ID issue below — it didn't work with this account's available model IDs.

## 3. Verifying the connection (what we checked, in order)

1. **`.env` loads correctly** — confirmed `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` all present.
2. **AWS credentials are valid** — `sts.get_caller_identity()` resolved to `arn:aws:iam::671192919555:user/vjuser1`.
3. **Anthropic models exist in the region** — `bedrock.list_foundation_models(byProvider="anthropic")` listed the Claude model catalog available in `us-west-2`.
4. **Model invocation** — this is where several issues surfaced (see below).

## 4. Issues hit and how they were resolved

| Issue | Cause | Fix |
|---|---|---|
| `NotFoundError: model 'anthropic.claude-opus-4-8' does not exist` (via Anthropic Mantle client) | Some newer Claude models require a **cross-region inference profile ID** (`us.` prefix), not the bare model ID | Looked up the correct ID via `bedrock.list_inference_profiles()` |
| `AccessDeniedException: ... is not available for this account` (via raw boto3 Converse, using `us.anthropic.claude-opus-4-8`) | **Bedrock model access** was not enabled for that model in this AWS account/region — this is a one-time opt-in per account/region, done in the console | AWS Console → **Amazon Bedrock → Model access** → enable access for at least one Anthropic model (region must be `us-west-2`) |
| `ResourceNotFoundException: Model is marked by provider as Legacy ...` (Claude 3 Haiku) | That specific model had lapsed due to 30 days of inactivity | Switched to testing with a currently-active model instead of a legacy one |
| `ResourceNotFoundException: Model use case details have not been submitted for this account` | Anthropic models on Bedrock require a **one-time "use case details" form**, separate from the model access toggle | Submitted the use case form in the Bedrock console; AWS notes it can take up to 15 minutes to propagate |
| `NotFoundError: model 'us.anthropic.claude-haiku-4-5-...' does not exist` (via Anthropic Mantle client) | The Mantle client only recognizes **bare** `anthropic.*` model IDs, not `us.`-prefixed inference profile IDs | Switched the working test cell to **raw boto3** (`bedrock_runtime.converse(...)`), which does accept the inference profile ID |
| `PermissionDeniedError: anthropic.claude-haiku-4-5 is not available for this account` (bare ID, via Mantle client) | The bare (non-inference-profile) on-demand model ID isn't enabled for this account | Confirmed the inference-profile ID is the one to use going forward; Option B left as-is for reference |

## 5. Working configuration

```python
BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

response = bedrock_runtime.converse(
    modelId=BEDROCK_MODEL_ID,
    messages=[{"role": "user", "content": [{"text": "Say hello in one short sentence."}]}],
    inferenceConfig={"maxTokens": 64},
)
print(response["output"]["message"]["content"][0]["text"])
```

Confirmed output: `"Hello!"`

## 6. Key takeaways / gotchas for next time

- Bedrock model IDs come in two shapes: a **bare model ID** (`anthropic.claude-haiku-4-5-20251001-v1:0`) and a **cross-region inference profile ID** (`us.anthropic.claude-haiku-4-5-20251001-v1:0` / `global.anthropic....`). Newer models generally require the inference profile form for on-demand invocation.
- Model access in Bedrock is **opt-in per AWS account and per region** — enabling it in one region doesn't carry over to another.
- Anthropic models specifically require a **use case details form** submitted once per account, independent of the model access toggle.
- The Anthropic SDK's `AnthropicBedrockMantle` client (Option B) did not accept the inference-profile-style model ID on this account — raw `boto3` (Option A) was the reliable path here. Worth re-testing Option B if the SDK is updated or if bare on-demand access is enabled later.
