# 抖音节点下载与按日期起拉

## 节点脚本在做什么

- **`douyin_node_pull.py`** 读取 **`douyin_nodes.yaml`**，用 **`cookies.text`** 调 f2 下载主页作品。
- 字段 **`sync_through_date`** 表示：**已经覆盖到这一天（含）为止**；下一次执行时，只会拉 **从「该日期的下一天」到今天** 这个区间内的作品（与 f2 的 `-i 开始日|结束日` 一致）。
- 已存在的视频文件 f2 会跳过，重复跑一般不会反复下同一文件。

## 从指定日期开始下（例如从 2026-04-13 起）

### 方式一：改节点里的 `sync_through_date`（推荐）

脚本规则是：**实际下载区间** = `(sync_through_date + 1 天)` ～ **`今天`**。

因此若希望 **从 2026-04-13（含）** 开始拉：

1. 打开 **`douyin_nodes.yaml`**，找到对应节点。
2. 把 **`sync_through_date`** 设为 **`2026-04-12`**（比目标起始日早一天）。
3. 执行：

   ```bash
   python douyin_node_pull.py <节点id>
   ```

   等价于 f2 使用区间 **`2026-04-13|今天`**。

| 你想从哪天开始（含） | 应设置的 `sync_through_date` |
|----------------------|------------------------------|
| 2026-04-13           | 2026-04-12                   |
| 2026-04-01           | 2026-03-31                   |

若 **`sync_through_date` 为 `null`**：下一次是 **全量**（不按日期过滤）。

### 方式二：只拉某一天或固定结束日

可直接用 f2（需自行拼 Cookie，或用 `scripts/cookies_tsv_to_f2.py` 从 `cookies.text` 生成）：

```bash
python -m f2 douyin -M post -u "用户主页URL" -k "Cookie字符串" -p "保存目录" -i 2026-04-13|2026-04-20
```

- **`-i`** 格式：`开始日期|结束日期`，均为 **`YYYY-MM-DD`**。
- 结束日写 **`今天`** 的日期即可拉到最新；同一天则 **`2026-04-13|2026-04-13`**。

### 方式三：全量重新拉

```bash
python douyin_node_pull.py <节点id> --full
```

或把该节点的 **`sync_through_date`** 改回 **`null`** 后再执行节点拉取（下次为全量）。

## 执行成功后 YAML 会怎样

节点拉取 **正常结束（退出码 0）** 后，脚本会把该节点的 **`sync_through_date`** 更新为 **当天日期**，方便下次只拉「新的一天起」的内容。若你刚手动改成 `2026-04-12` 只为了从 4/13 开拉，跑完后会变成今天；这是预期行为，下次增量从「明天」相对今天继续。

## 依赖与文件

- 根目录 **`cookies.text`**：浏览器导出的制表符 Cookie 表。
- 已安装 **f2**（见仓库 `requirements.txt` / `install-deps.bat`）。
- 保存目录默认 **`Download`**，可用 **`-p`** 修改。

## 相关文件

| 文件 | 说明 |
|------|------|
| `douyin_nodes.yaml` | 节点列表与 `sync_through_date` |
| `douyin_node_pull.py` | 按节点拉取并维护日期 |
| `douyin_user_download.py` | 按 URL 单次拉取（不传日期区间） |
| `scripts/cookies_tsv_to_f2.py` | 将 `cookies.text` 转为 Cookie 字符串 |
