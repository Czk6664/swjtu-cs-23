import { strict as assert } from 'node:assert';
import { maliciousCategories, maliciousPost, maliciousText } from './fixtures/malicious-content.mjs';

globalThis.__xssExecuted = false;
globalThis.window = {
  location: {
    origin: 'http://localhost:5173'
  }
};

const { buildStateCard, escapeHtml, postCard } = await import('../assets/modules/ui.js');

const assertEscaped = (html, label) => {
  assert.ok(!html.includes('<script>'), `${label} leaked script tag`);
  assert.ok(!html.includes('<img src=x'), `${label} leaked img tag`);
  assert.ok(!html.includes('onerror="'), `${label} leaked executable event handler`);
  assert.ok(html.includes('&lt;') || html.includes('&quot;'), `${label} did not escape hostile text`);
};

Object.entries(maliciousCategories).forEach(([label, value]) => {
  assertEscaped(escapeHtml(value), label);
});

assertEscaped(postCard(maliciousPost), 'postCard');
assertEscaped(buildStateCard(maliciousText, maliciousText, maliciousText, 'reload'), 'stateCard');
assert.equal(globalThis.__xssExecuted, false, 'malicious fixture executed during rendering test');
