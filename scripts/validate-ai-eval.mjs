import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const readJson = (relativePath) => JSON.parse(fs.readFileSync(path.join(root, relativePath), 'utf8'));
const exists = (relativePath) => fs.existsSync(path.join(root, relativePath));

const promptsSpec = readJson('data/ai-discovery-eval-prompts.json');
const factsSpec = readJson('data/ai-discovery-eval-facts.json');
const catalog = readJson('data/rse-product-catalog.json');

const errors = [];
const warnings = [];
const fail = (message) => errors.push(message);
const warn = (message) => warnings.push(message);

const prompts = Array.isArray(promptsSpec.prompts) ? promptsSpec.prompts : [];
const factRegistry = factsSpec.facts && typeof factsSpec.facts === 'object' ? factsSpec.facts : {};
const products = Array.isArray(catalog.products) ? catalog.products : [];
const productIds = new Set(products.map((product) => product.id));
const promptIds = new Set();
const allowedSurfaceExpectations = new Set(['eligible_not_required', 'brand_required']);
const allowedCategories = new Set([
  'unbranded_discovery',
  'branded_entity',
  'product_accuracy',
  'app_status',
  'safety_accuracy',
  'citation_quality'
]);

if (promptsSpec.schemaVersion !== 1) fail('Prompt spec schemaVersion must be 1.');
if (factsSpec.schemaVersion !== 1) fail('Fact registry schemaVersion must be 1.');
if (!promptsSpec.benchmarkVersion) fail('Prompt spec benchmarkVersion is required.');
if (promptsSpec.benchmarkVersion !== factsSpec.benchmarkVersion) {
  fail('Prompt spec and fact registry benchmarkVersion must match.');
}
if (prompts.length !== 20) {
  fail(`Benchmark must contain exactly 20 prompts; found ${prompts.length}.`);
}
if (promptsSpec.principles?.forceBrandIntoUnbrandedPrompts !== false) {
  fail('Benchmark must explicitly keep forceBrandIntoUnbrandedPrompts=false.');
}
if (promptsSpec.principles?.separateDiscoverabilityFromAccuracy !== true) {
  fail('Benchmark must explicitly separate discoverability from accuracy.');
}

for (const prompt of prompts) {
  const prefix = prompt?.id || 'prompt-without-id';
  if (!prompt?.id) {
    fail('Every benchmark prompt needs an id.');
    continue;
  }
  if (promptIds.has(prompt.id)) fail(`Duplicate prompt id: ${prompt.id}.`);
  promptIds.add(prompt.id);

  if (!allowedCategories.has(prompt.category)) {
    fail(`${prefix}: unsupported category ${prompt.category}.`);
  }
  if (!allowedSurfaceExpectations.has(prompt.surfaceExpectation)) {
    fail(`${prefix}: unsupported surfaceExpectation ${prompt.surfaceExpectation}.`);
  }
  if (typeof prompt.prompt !== 'string' || prompt.prompt.trim().length < 20) {
    fail(`${prefix}: prompt text is missing or too short.`);
  }
  if (!Array.isArray(prompt.eligibleProductIds)) {
    fail(`${prefix}: eligibleProductIds must be an array.`);
  } else {
    for (const productId of prompt.eligibleProductIds) {
      if (!productIds.has(productId)) fail(`${prefix}: unknown product id ${productId}.`);
    }
  }
  if (!Array.isArray(prompt.requiredFactsIfSurfaced) || prompt.requiredFactsIfSurfaced.length === 0) {
    fail(`${prefix}: requiredFactsIfSurfaced must contain at least one fact id.`);
  } else {
    for (const factId of prompt.requiredFactsIfSurfaced) {
      if (!factRegistry[factId]) fail(`${prefix}: unknown fact id ${factId}.`);
    }
  }
  if (!Array.isArray(prompt.forbiddenClaims)) {
    fail(`${prefix}: forbiddenClaims must be an array.`);
  }
}

const brandedCount = prompts.filter((prompt) => prompt.surfaceExpectation === 'brand_required').length;
const unbrandedCount = prompts.filter((prompt) => prompt.surfaceExpectation === 'eligible_not_required').length;
if (brandedCount < 8) warn(`Benchmark has only ${brandedCount} branded prompts.`);
if (unbrandedCount < 6) warn(`Benchmark has only ${unbrandedCount} unbranded discovery prompts.`);

const parseArg = (name) => {
  const equalsArg = process.argv.find((arg) => arg.startsWith(`${name}=`));
  if (equalsArg) return equalsArg.slice(name.length + 1);
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
};

const resultsPath = parseArg('--results');
let metrics = null;

if (resultsPath) {
  if (!exists(resultsPath)) {
    fail(`Results file does not exist: ${resultsPath}`);
  } else {
    const run = readJson(resultsPath);
    const allowedRunStatus = new Set(['not_run', 'partial', 'complete']);
    const resultIds = new Set();
    const promptById = new Map(prompts.map((prompt) => [prompt.id, prompt]));
    const results = Array.isArray(run.results) ? run.results : [];

    if (run.schemaVersion !== 1) fail(`${resultsPath}: schemaVersion must be 1.`);
    if (run.benchmarkVersion !== promptsSpec.benchmarkVersion) {
      fail(`${resultsPath}: benchmarkVersion must be ${promptsSpec.benchmarkVersion}.`);
    }
    if (!allowedRunStatus.has(run.runStatus)) fail(`${resultsPath}: invalid runStatus ${run.runStatus}.`);
    if (!run.runId || !run.provider || !run.model || !run.runAt) {
      fail(`${resultsPath}: runId, provider, model and runAt are required.`);
    }
    if (Number.isNaN(Date.parse(run.runAt))) fail(`${resultsPath}: runAt must be a valid date-time.`);
    if (run.runStatus === 'not_run' && results.length !== 0) {
      fail(`${resultsPath}: not_run results must have an empty results array.`);
    }
    if (run.runStatus === 'complete' && results.length !== prompts.length) {
      fail(`${resultsPath}: complete runs must contain exactly ${prompts.length} results.`);
    }
    if (run.runStatus === 'partial' && (results.length === 0 || results.length >= prompts.length)) {
      fail(`${resultsPath}: partial runs must contain between 1 and ${prompts.length - 1} results.`);
    }

    for (const result of results) {
      const prompt = promptById.get(result.promptId);
      if (!prompt) {
        fail(`${resultsPath}: unknown promptId ${result.promptId}.`);
        continue;
      }
      if (resultIds.has(result.promptId)) fail(`${resultsPath}: duplicate result for ${result.promptId}.`);
      resultIds.add(result.promptId);

      if (typeof result.rseSurfaced !== 'boolean') fail(`${result.promptId}: rseSurfaced must be boolean.`);
      if (!Array.isArray(result.mentionedProductIds)) fail(`${result.promptId}: mentionedProductIds must be an array.`);
      else for (const productId of result.mentionedProductIds) {
        if (!productIds.has(productId)) fail(`${result.promptId}: unknown mentioned product id ${productId}.`);
      }
      if (!Array.isArray(result.sourceUrls)) fail(`${result.promptId}: sourceUrls must be an array.`);
      if (!result.factChecks || typeof result.factChecks !== 'object' || Array.isArray(result.factChecks)) {
        fail(`${result.promptId}: factChecks must be an object.`);
      }
      if (!Array.isArray(result.forbiddenClaimsTriggered)) {
        fail(`${result.promptId}: forbiddenClaimsTriggered must be an array.`);
      } else {
        for (const claim of result.forbiddenClaimsTriggered) {
          if (!prompt.forbiddenClaims.includes(claim)) {
            fail(`${result.promptId}: triggered forbidden claim is not registered for this prompt: ${claim}.`);
          }
        }
      }

      const factChecks = result.factChecks || {};
      const allowedFactStatus = new Set(['pass', 'fail', 'not_evaluated']);
      for (const [factId, status] of Object.entries(factChecks)) {
        if (!prompt.requiredFactsIfSurfaced.includes(factId)) {
          fail(`${result.promptId}: fact check ${factId} is not required by this prompt.`);
        }
        if (!allowedFactStatus.has(status)) fail(`${result.promptId}: invalid fact status ${status} for ${factId}.`);
      }

      if (run.runStatus === 'complete' && result.rseSurfaced) {
        for (const factId of prompt.requiredFactsIfSurfaced) {
          if (!Object.hasOwn(factChecks, factId) || factChecks[factId] === 'not_evaluated') {
            fail(`${result.promptId}: surfaced complete-run result must evaluate fact ${factId}.`);
          }
        }
        if (typeof result.canonicalUrlPresent !== 'boolean') {
          fail(`${result.promptId}: surfaced complete-run result must set canonicalUrlPresent.`);
        }
        if (typeof result.authoritativeRseSourcePresent !== 'boolean') {
          fail(`${result.promptId}: surfaced complete-run result must set authoritativeRseSourcePresent.`);
        }
      }
    }

    if (run.runStatus === 'complete') {
      for (const prompt of prompts) {
        if (!resultIds.has(prompt.id)) fail(`${resultsPath}: complete run is missing ${prompt.id}.`);
      }
    }

    const observed = results.filter((result) => promptById.has(result.promptId));
    const unbranded = observed.filter((result) => promptById.get(result.promptId).surfaceExpectation === 'eligible_not_required');
    const branded = observed.filter((result) => promptById.get(result.promptId).surfaceExpectation === 'brand_required');
    const surfaced = observed.filter((result) => result.rseSurfaced === true);
    const evaluatedFacts = surfaced.flatMap((result) => Object.values(result.factChecks || {})).filter((status) => status !== 'not_evaluated');
    const factPasses = evaluatedFacts.filter((status) => status === 'pass').length;
    const canonicalEvaluated = surfaced.filter((result) => typeof result.canonicalUrlPresent === 'boolean');
    const sourceEvaluated = surfaced.filter((result) => typeof result.authoritativeRseSourcePresent === 'boolean');
    const hallucinationEvaluated = surfaced;

    const ratio = (numerator, denominator) => denominator ? Number((numerator / denominator).toFixed(4)) : null;
    metrics = {
      observedPromptCount: observed.length,
      eligibleDiscoveryRate: ratio(unbranded.filter((result) => result.rseSurfaced).length, unbranded.length),
      brandedRecognitionRate: ratio(branded.filter((result) => result.rseSurfaced).length, branded.length),
      factualAccuracyAmongSurfaced: ratio(factPasses, evaluatedFacts.length),
      canonicalUrlRateAmongSurfaced: ratio(canonicalEvaluated.filter((result) => result.canonicalUrlPresent).length, canonicalEvaluated.length),
      authoritativeCitationRateAmongSurfaced: ratio(sourceEvaluated.filter((result) => result.authoritativeRseSourcePresent).length, sourceEvaluated.length),
      forbiddenClaimRateAmongSurfaced: ratio(hallucinationEvaluated.filter((result) => (result.forbiddenClaimsTriggered || []).length > 0).length, hallucinationEvaluated.length)
    };
  }
}

for (const warning of warnings) console.warn(`WARN: ${warning}`);
if (errors.length) {
  for (const error of errors) console.error(`ERROR: ${error}`);
  console.error(`AI discovery eval validation failed with ${errors.length} error(s).`);
  process.exit(1);
}

console.log(`AI discovery eval spec passed: ${prompts.length} prompts, ${Object.keys(factRegistry).length} facts, ${products.length} products.`);
if (resultsPath) {
  console.log(`Results file passed: ${resultsPath}`);
  if (metrics) console.log(JSON.stringify(metrics, null, 2));
}
