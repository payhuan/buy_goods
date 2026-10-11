(function (root) {
  function createGame(products) {
    const byId = new Map(products.map(product => [product.id, product]));
    const earned = new Set();
    let zone = '百货区';
    let page = '入口';
    return {
      get page() { return page; },
      get zone() { return zone; },
      get stars() { return earned.size; },
      hasStar(id) { return earned.has(id); },
      foundIn(area) { return products.filter(p => p.zone === area && earned.has(p.id)).length; },
      enter() { zone = '百货区'; page = '百货区'; },
      next() {
        if (page === '入口') { zone = '百货区'; page = '百货区'; }
        else if (page === '百货区') { zone = '食品区'; page = '食品区'; }
        else if (page === '食品区') { page = '结束'; }
      },
      back() {
        if (page === '结束') { page = zone = '食品区'; }
        else if (page === '食品区') { page = zone = '百货区'; }
        else if (page === '百货区') { page = '入口'; }
        else { page = '入口'; }
      },
      restart() { earned.clear(); page = '入口'; zone = '百货区'; },
      setZone(next) {
        if (!['百货区', '食品区'].includes(next)) throw new Error('Unknown zone');
        zone = next;
        page = next;
      },
      select(id) {
        const product = byId.get(id);
        if (!product || product.zone !== zone) return 'ignored';
        if (earned.has(id)) return 'ignored';
        if (product.perPackage !== 10) return 'wrong';
        earned.add(id);
        return 'correct';
      },
    };
  }
  root.createMarketGame = createGame;
  if (typeof module !== 'undefined') module.exports = createGame;
})(typeof globalThis !== 'undefined' ? globalThis : this);
