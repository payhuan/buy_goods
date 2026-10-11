(function (root) {
  const products = [
    { id: 'rolls', name: '卷纸', zone: '百货区', perPackage: 10, stock: 1, unit: '袋', price: 19.9, note: '柔软纸巾 · 家庭装' },
    { id: 'mugs', name: '水杯', zone: '百货区', perPackage: 1, stock: 3, unit: '个', price: 12.9, note: '陶瓷水杯 · 日常好物' },
    { id: 'toothpaste', name: '牙膏', zone: '百货区', perPackage: 1, stock: 4, unit: '盒', price: 8.9, note: '清新薄荷 · 120克' },
    { id: 'brushes', name: '牙刷', zone: '百货区', perPackage: 6, stock: 2, unit: '板', price: 15.9, note: '柔软刷毛 · 板装' },
    { id: 'batteries', name: '电池', zone: '百货区', perPackage: 10, stock: 1, unit: '板', price: 19.9, note: '碱性电池 · 板装' },
    { id: 'pencils', name: '铅笔', zone: '百货区', perPackage: 10, stock: 1, unit: '盒', price: 9.9, note: '学生铅笔 · 盒装' },
    { id: 'water', name: '矿泉水', zone: '食品区', perPackage: 12, stock: 1, unit: '件', price: 18, note: '纯净饮水 · 每瓶500毫升' },
    { id: 'chips', name: '筒装薯片', zone: '食品区', perPackage: 1, stock: 6, unit: '筒', price: 8.9, note: '原味薯片 · 筒装' },
    { id: 'candy', name: '彩虹糖', zone: '食品区', perPackage: 10, stock: 1, unit: '袋', price: 12.9, note: '缤纷果味 · 小包袋装' },
    { id: 'yogurt', name: '酸奶', zone: '食品区', perPackage: 10, stock: 1, unit: '件', price: 24.9, note: '原味酸奶 · 杯装组合' },
    { id: 'eggs', name: '鸡蛋', zone: '食品区', perPackage: 10, stock: 1, unit: '盒', price: 12, note: '新鲜鸡蛋 · 纸浆盒装' },
    { id: 'apples', name: '苹果', zone: '食品区', perPackage: 1, stock: 4, unit: '个', price: 4, note: '脆甜红苹果 · 按个计价' },
  ];
  root.MARKET_PRODUCTS = products;
  root.MARKET_ASSET_VERSION = '20261012-compressed';
  root.marketAssetUrl = path => root.MARKET_EMBEDDED_ASSETS?.[path] || `${path}?v=${root.MARKET_ASSET_VERSION}`;
  if (typeof module !== 'undefined') module.exports = products;
})(typeof globalThis !== 'undefined' ? globalThis : this);

