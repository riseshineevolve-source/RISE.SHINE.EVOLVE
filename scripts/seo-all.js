#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = process.cwd();
const REPORT_DIR = path.join(ROOT, 'reports');
const REPORT_FILE = path.join(REPORT_DIR, 'seo-status.json');

function run(cmd, args) {
  const startedAt = new Date().toISOString();
  const res = spawnSync(cmd, args, { cwd: ROOT, encoding: 'utf8' });
  const endedAt = new Date().toISOString();
  return {
    command: [cmd, ...args].join(' '),
    startedAt,
    endedAt,
    code: res.status,
    ok: res.status === 0,
    stdout: res.stdout || '',
    stderr: res.stderr || ''
  };
}

const steps = [
  run('node', ['scripts/validate-seo.js']),
  run('node', ['scripts/seo-audit.js'])
];

const ok = steps.every(s => s.ok);
const report = {
  generatedAt: new Date().toISOString(),
  overallOk: ok,
  steps: steps.map(s => ({
    command: s.command,
    ok: s.ok,
    code: s.code,
    startedAt: s.startedAt,
    endedAt: s.endedAt
  }))
};

fs.mkdirSync(REPORT_DIR, { recursive: true });
fs.writeFileSync(REPORT_FILE, JSON.stringify(report, null, 2) + '\n');

for (const s of steps) {
  process.stdout.write(`\n$ ${s.command}\n`);
  process.stdout.write(s.stdout);
  if (s.stderr) process.stderr.write(s.stderr);
}
console.log(`\nReport: ${path.relative(ROOT, REPORT_FILE)}`);

if (!ok) process.exit(1);
