# 小小采购员：逛超市，找到十个

面向一年级学生的交互式数学课件。在真实货架场景中数一数，选出每袋、盒、件或板内正好有 **10 个**的商品。

课件包含六个页面：入口 → 百货区过渡 → 百货区购物 → 食品区过渡 → 食品区购物 → 结束。基于用户提供的截图、商品参考图片和模型制作，未抓取原网页。

![当前货架效果](verification/替换卷纸模型预览.png)

## 快速运行

需要 Python 3 和支持 WebGL、ES Modules 的现代浏览器。运行课件不需要安装 npm 包，也不需要互联网；Three.js、模型和图片均保存在项目内。

```bash
git clone https://github.com/payhuan/buy_goods.git
cd buy_goods
python serve.py --open
```

默认地址为 `http://127.0.0.1:8767/`，服务只监听本机。按 Ctrl+C 停止。Windows 也可以双击 `打开课堂.cmd`。若系统命令为 `python3`，将上述 `python` 换成 `python3`。

不要直接双击源码 `index.html`；三维模型和模块需要通过本地 HTTP 服务加载。

## 课堂交互

- 每袋、盒、件或板分别计数，判断其内部数量是否为十个。
- 选对后，商品先放大再恢复，大星星缓慢飞向计分区，商品旁保留金色星星。
- 同一商品只奖励一次，两区最多获得六颗星。
- 选错只让商品轻微抖动并播放音效。
- 每区选对三个后，等待约 2.3 秒进入下一页；没有选完也可以手动翻页。
- 过渡页约 1.5 秒；上一页直接返回购物区或入口，避免再次自动跳回。
- 返回货架保留已获得的星星；“再玩一次”清零。
- 货架价签仅显示物品名与价格，没有数量提示和放大按钮。
- 食品采用便于数清前后排的角度；鸡蛋不接收货架投影。

## 商品清单

价格为课堂示例，不是实时市场报价。

| 区域 | 商品 | 内部数量与陈列 | 示例价 | 正确商品 |
|---|---|---|---|---|
| 百货区 | 卷纸 | 10 卷／袋，1 袋 | ¥19.90／袋 | 是 |
| 百货区 | 水杯 | 3 个 | ¥12.90／个 | 否 |
| 百货区 | 牙膏 | 4 盒 | ¥8.90／盒 | 否 |
| 百货区 | 牙刷 | 6 支／板，2 板 | ¥15.90／板 | 否 |
| 百货区 | 电池 | 10 节／板，1 板 | ¥19.90／板 | 是 |
| 百货区 | 铅笔 | 10 支／盒，1 盒 | ¥9.90／盒 | 是 |
| 食品区 | 矿泉水 | 12 瓶／件，1 件 | ¥18.00／件 | 否 |
| 食品区 | 筒装薯片 | 6 筒 | ¥8.90／筒 | 否 |
| 食品区 | 彩虹糖 | 10 小包／袋，1 袋 | ¥12.90／袋 | 是 |
| 食品区 | 酸奶 | 10 杯／件，1 件 | ¥24.90／件 | 是 |
| 食品区 | 鸡蛋 | 10 枚／盒，1 盒 | ¥12.00／盒 | 是 |
| 食品区 | 苹果 | 4 个 | ¥4.00／个 | 否 |

牙刷按每板六支判断，两板合计十二支不改变规则。

## 项目结构

```text
index.html / styles.css    页面入口与样式
app.js                    界面、音效、选对动效与翻页
scene.js                  三维货架、商品摆放与点击区域
data.js / game.js         商品数据与游戏状态
viewer.js                 保留的查看器模块，当前界面不提供放大入口
serve.py                  本地静态服务器
vendor/                   Three.js 与 MIT 许可
resources/                原始模型输入、参考图片和派生贴图
assets/models/            12 个独立 GLB 与完整模型合集
assets/editable/          可编辑 supermarket.blend
assets/images/            商品预览与首页背景
assets/diagnostics/       顶、前、侧诊断图
source/                   Blender 建模、打包、检查与测试脚本
manifest.json             模型验收契约与资源路径
verification/             实测截图、模型导入检查与验收报告
publish/                  发布说明、资源清单和许可
```

所有运行时资源均从项目内相对路径读取，不依赖开发电脑的磁盘路径或外部 CDN。中文网格文字和图像纹理已包含在 GLB 内，浏览器无需安装建模字体。音效使用 Web Audio 合成。

### 当前模型说明

- 卷纸使用用户提供的 `Wrapped/output_saturated/model.glb`，复制保存在 `resources/rolls-supplied.glb`；`assets/models/rolls.glb` 与该输入逐字节一致。保留两排五卷、透明包装、纸层纹理和两孔提手；它已正向显示，不再追加旧卷纸的 90 度旋转。
- 铅笔原始输入保存在 `resources/pencil-original.glb`，保留十支主体并替换英文印刷。
- 牙膏使用红绿展开贴图，醒目英文已替换为中文；贴图保存在 `resources/toothpaste-atlas-chinese.png`。正面、侧面和顶面的镜像 UV 已修正。
- 牙刷手柄沿相机方向弯曲，与刷头连续连接，包装和两板各六支不变。
- 矿泉水使用红盖、红白中文标签与贴合透明膜；彩虹糖为两列五行的红色厚小包。

## 测试与模型验证

行为测试需要 Node.js（支持内置 `node:test`）：

```bash
python source/build_publish.py
node --test source/game.test.cjs
```

也可以运行 `npm test`，无需 `npm install`。当前 7 项测试通过，覆盖页面状态、数量规则、重复奖励、未完成翻页、重玩和资源完整性。测试包含发布文件的资源校验，因此从仓库首次下载后，请先运行 `python source/build_publish.py` 再运行测试。

独立 GLB 导入检查需要 Blender：

```powershell
& '<Blender安装路径>/blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python source/verify_individual_assets.py
```

当前 12 个 GLB 的实体数量、有限坐标、尺寸和内嵌贴图检查通过；两板牙刷各六支。模型验收记录见 `verification/models-feedback/validation.json`。预览与浏览器画面由同一代理实际检查，不宣称独立人工审查。

## 重建三维模型

建模需要 Blender，以及可用的中文常规体和粗体字体。Windows 默认读取系统微软雅黑；其它系统可通过 `--font` 和 `--bold-font` 指定本机字体。字体文件不随项目分发。运行课件本身不需要 Blender 或这些字体。

在项目目录执行，使用新的输出目录以保护现有资产：

```powershell
& '<Blender安装路径>/blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python source/build_models.py -- --output-dir assets-rebuilt --font '<中文常规字体路径>' --bold-font '<中文粗体字体路径>'
```

检查新模型和预览后，再将输出作为 `assets/` 使用。源脚本依赖项目内的 `resources/`，因此重建时必须保留完整项目。除 Blender 内置 Python 外，联系图脚本 `source/contact_sheet.py` 需要 Pillow；课件运行和单文件打包不需要 Pillow。

## 生成超喵单文件版

**按用户要求，仓库不上传单文件 HTML。** 下载源码后，在项目目录执行：

```bash
python source/build_publish.py
```

生成 `publish/逛超市_超喵单文件版.html`。当前大小约 **46.9 MiB**，内嵌十二个 GLB、四十八张商品 PNG、一张首页 JPG、样式和三维模块，无其它运行时文件依赖。`publish/资源依赖清单.json` 记录资源大小和 SHA-256。

上传生成的完整 HTML 到超喵；源码入口 `index.html` 不能作为独立文件上传使用。发布版已通过本地浏览器实测，超喵的上传限制和嵌入环境需在平台验证。重新生成发布版后再运行测试，可核对内嵌资源的完整性。

## 资源来源与许可

- Three.js 依赖遵循 MIT 许可，见 `vendor/THREE-LICENSE.txt` 与 `publish/THREE-LICENSE.txt`。
- 原始铅笔、卷纸、入口照片和商品参考素材由用户提供；参考及派生贴图保存在 `resources/`。牙膏文字编辑过程见 `resources/toothpaste-texture-edit.md`。
- 其它模型、程序和程序化苹果纹理由本任务制作。建模过程中部分微表面细节仅保留在 Blender 文件，GLB 使用可移植 PBR 材质。
- 用户提供的品牌素材和照片未在此声明额外的第三方再分发许可，仓库也不将这些素材统一标为 MIT。
