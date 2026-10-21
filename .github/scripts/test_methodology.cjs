const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { test } = require('node:test');
const vm = require('node:vm');

const html = readFileSync('methodology/index.html', 'utf8');
const latest = 'https://github.com/transitrix/methodology/releases/latest';
const api = 'https://api.github.com/repos/transitrix/methodology/releases/latest';
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/gi)].at(-1)[1];

function initialElements() {
  const elements = {};
  for (const id of ['spec-link', 'version-placeholder']) {
    const match = html.match(new RegExp(`<([a-z]+) id="${id}"([^>]*)>([^<]*)</\\1>`, 'i'));
    assert.ok(match, `Missing ${id}`);
    elements[id] = { textContent: match[3], href: match[2].match(/href="([^"]+)"/)?.[1] };
  }
  return elements;
}

async function load(fetch, signal = new AbortController().signal) {
  const elements = initialElements();
  const context = vm.createContext({
    document: { getElementById: id => elements[id] },
    AbortSignal: { timeout: ms => { assert.equal(ms, 8000); return signal; } },
    fetch: (url, options) => {
      assert.equal(url, api);
      assert.equal(options.signal, signal);
      return fetch(url, options);
    },
    console: { error() {} },
  });
  await vm.runInContext(script, context, { timeout: 1000 });
  return elements;
}

test('without JavaScript, the link opens the latest release and text remains useful', () => {
  const elements = initialElements();
  assert.equal(elements['spec-link'].href, latest);
  assert.match(elements['version-placeholder'].textContent, /latest published specification/);
});

test('the fetched release determines the version and link, including future releases', async () => {
  for (const tag of ['v7.0.0', 'v42.3.1']) {
    const elements = await load(async () => ({ ok: true, json: async () => ({ tag_name: tag }) }));
    assert.equal(elements['spec-link'].href, `https://github.com/transitrix/methodology/releases/tag/${tag}`);
    assert.equal(elements['spec-link'].textContent, `Read the ${tag} methodology specification on GitHub`);
    assert.match(elements['version-placeholder'].textContent, new RegExp(tag.slice(1).replaceAll('.', '\\.')));
  }
});

test('HTTP, network, JSON and invalid release failures preserve the latest-release link', async () => {
  const failures = [
    async () => { throw new Error('Network unavailable'); },
    async () => ({ ok: false }),
    async () => ({ ok: true, json: async () => { throw new Error('Invalid JSON'); } }),
    ...[null, {}, { tag_name: '' }, { tag_name: 7 }, { tag_name: 'v8', draft: true },
      { tag_name: 'v8', prerelease: true }].map(release =>
      async () => ({ ok: true, json: async () => release })),
  ];
  for (const fetch of failures) {
    const elements = await load(fetch);
    assert.equal(elements['spec-link'].href, latest);
    assert.equal(elements['version-placeholder'].textContent, 'View the latest methodology specification on GitHub.');
  }
});

test('release names stay text and release tags stay within the tag URL', async () => {
  const elements = await load(async () => ({ ok: true, json: async () => ({
    tag_name: 'v8/preview?#', name: '<img src=x> (breaking)',
  }) }));
  assert.equal(elements['spec-link'].href, 'https://github.com/transitrix/methodology/releases/tag/v8%2Fpreview%3F%23');
  assert.match(elements['version-placeholder'].textContent, /Breaking changes/);
  assert.doesNotMatch(elements['version-placeholder'].textContent, /<img/);
});

test('a timed-out request keeps a truthful fallback destination and label', async () => {
  const signal = AbortSignal.abort(new DOMException('Request timed out', 'TimeoutError'));
  const elements = await load(async (url, { signal }) => { throw signal.reason; }, signal);
  assert.equal(elements['spec-link'].href, latest);
  assert.equal(elements['spec-link'].textContent, 'Read the full methodology specification on GitHub');
  assert.equal(elements['version-placeholder'].textContent, 'View the latest methodology specification on GitHub.');
});
