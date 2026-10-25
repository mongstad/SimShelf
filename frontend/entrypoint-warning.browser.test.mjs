// Reuse the full-App read-only fixture to exercise all named-warning surfaces.
await import('./run-overview.browser.test.mjs');
const result = document.createElement('pre');
result.id = 'results';
document.body.prepend(result);
const wait = ms => new Promise(resolve => setTimeout(resolve,ms));
const assert = (ok,message) => {if (!ok) throw Error(message);};
const scenario = new URLSearchParams(location.search).get('entrypoint');
const warns = ['changed','comment'].includes(scenario);
const label = 'Captured source changed within version';
async function click(label) {
  const button = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === label || b.getAttribute('aria-label') === label);
  assert(button,'Missing '+label);button.click();await wait(500);
}
(async()=>{
  await wait(700);
  assert(document.querySelector('.detail-page').textContent.includes(label) === warns,'detail warning rule');
  if (scenario === 'unavailable') assert(document.body.textContent.includes('Fixture retained source is missing'),'evidence limitation');
  await click('View source comparison');
  assert(document.body.textContent.includes('Changes against version baseline'),'full snapshot evidence retained');
  await click('← Back to runs');
  assert(!!document.querySelector('.run-table .source-note.changed') === warns,'run history warning rule');
  await click('Version history');
  assert(document.body.textContent.includes('primary Python source changes within this version') === warns,'version count rule');
  assert(document.documentElement.scrollWidth <= innerWidth,'no horizontal overflow');
  result.textContent='PASS '+scenario+': detail, source evidence, history and version count';
})().catch(error=>{result.textContent='FAIL '+error.stack;});
