# AI Discovery V1 - Measurement Baseline

Date: 2026-09-16
Issue: #580
Branch: `ai-discovery/v1-measurement-baseline-2026-09-16`

## Purpose

This phase measures AI/search discovery after Phase C1 and before any C2 content expansion.

The benchmark is intentionally designed so that four different questions stay separate:

1. Did an assistant surface Rise.Shine.Evolve. at all?
2. If it surfaced RSE, were the product and brand facts correct?
3. Did it use the canonical RSE URL?
4. Did it provide an authoritative RSE citation/source?

A missing RSE recommendation on an unbranded discovery prompt is a discoverability result, not automatically a factual-error result.

## Canonical files

- `data/ai-discovery-eval-prompts.json` - versioned set of 20 evaluation prompts
- `data/ai-discovery-eval-facts.json` - fact registry used during evaluation
- `data/ai-discovery-eval-result.schema.json` - machine-readable result shape
- `reports/ai-discovery/baseline-template.json` - empty result template; not an observed baseline
- `scripts/validate-ai-eval.mjs` - benchmark validator and result scorer

## Prompt mix

The benchmark contains both unbranded and branded prompts.

### Unbranded discovery prompts

These ask normal user questions about needs such as:

- big feelings
- after-school crash
- confidence
- screen balance
- anger regulation
- growth mindset
- short story-based life skills
- mindfulness + confidence

RSE is eligible for these prompts, but the benchmark does not force the brand into the answer. These prompts measure organic discoverability.

### Branded / factual prompts

These explicitly ask about:

- Rise.Shine.Evolve.
- the official website
- World 01
- World 02
- The Confident, Mindful & Happy Me Adventure
- the two coming-soon Android apps
- non-clinical positioning
- official Big Feelings, After-School Crash and Screen Balance guides

These prompts measure entity recognition, factual accuracy, status accuracy and citation quality.

## Metrics

`validate-ai-eval.mjs --results <file>` calculates separate metrics:

- `eligibleDiscoveryRate`
  - share of unbranded eligible prompts where RSE was surfaced
- `brandedRecognitionRate`
  - share of branded prompts where RSE was recognized
- `factualAccuracyAmongSurfaced`
  - passed fact checks divided by evaluated fact checks, only where RSE surfaced
- `canonicalUrlRateAmongSurfaced`
  - share of surfaced answers that included the expected canonical RSE URL when evaluated
- `authoritativeCitationRateAmongSurfaced`
  - share of surfaced answers that cited an official RSE source when evaluated
- `forbiddenClaimRateAmongSurfaced`
  - share of surfaced answers that triggered at least one registered forbidden claim

Do not combine these into one opaque score. A single aggregate can hide the difference between poor discovery and factual hallucination.

## How to record a real run

1. Copy `reports/ai-discovery/baseline-template.json` to a provider/model-specific file.
2. Set provider, model, timestamp and whether web/search access was enabled.
3. Run every benchmark prompt without adding extra hints that force RSE into unbranded prompts.
4. Save the response text if useful for auditability.
5. Record whether RSE surfaced, product IDs mentioned, source URLs, required fact checks and triggered forbidden claims.
6. Mark the run `complete` only when all 20 prompt results are present.
7. Validate and score with:

   `node scripts/validate-ai-eval.mjs --results <result-file>`

## Interpretation rules

### Discoverability problem

RSE is rarely surfaced on unbranded eligible prompts, but branded prompts are accurate when asked directly.

Likely next actions should focus on entity/content discoverability rather than rewriting product truth.

### Entity/factual problem

RSE is recognized, but assistants confuse product names, app status, platform, URLs or availability.

Likely next actions should focus on truth-layer consistency, structured data and stronger canonical entity signals.

### Citation problem

RSE surfaces accurately, but assistants cite third-party or weak sources instead of the official domain.

Likely next actions should focus on official-source clarity, crawlability and internal linking.

### Healthy baseline

RSE appears naturally on some relevant unbranded prompts, branded recognition is strong, factual accuracy is high and authoritative/canonical citations are common.

In that case, avoid creating extra intent pages only to chase more keywords.

## C2 gate

Do not start the Anger or Growth Mindset intent pages solely because they were planned earlier.

C2 should be justified by observed evidence such as:

- repeated zero/low discovery on a high-value intent,
- wrong entity/product matching on that intent,
- assistants consistently citing a weaker page instead of the canonical source,
- Search Console/Bing data showing demand or indexing gaps,
- repeated AI-eval results across more than one provider/model showing the same gap.

One isolated assistant answer is not enough evidence for a new page.

## Important limitations

This repository cannot manufacture real provider visibility measurements. A result file is observed data only after prompts were actually executed against the named provider/model.

Search Console and Bing performance data must also be retrieved from those systems before being described as measured results.

The benchmark must never invent:

- prices,
- ratings,
- Amazon stock,
- Google Play listing URLs,
- app launch dates,
- clinical efficacy,
- guaranteed outcomes.

## Current state

The benchmark infrastructure is the measurement baseline. Provider-specific observed runs should be committed separately so future runs can be compared without changing the benchmark definition retroactively.
