# Temu 接入计划

SellerHarbor 的 Temu 接入采用“只读同步优先、写回能力后置”的策略。目标是先把 Temu 的商品、订单、履约和库存信号同步进 SellerHarbor，用于商品主档、库存预警和热款追踪；价格、库存、Listing 写回必须等审计、回滚和人工确认就绪后再开放。

## 当前实现状态

已完成：

- 后端配置项：`SELLERHARBOR_TEMU_*`
- 后端状态接口：`GET /api/integrations/temu/status`
- 店铺注册接口：`GET /api/stores/registry`
- readiness 检查：`temu_integration`
- 前端设置页：系统设置 -> 平台接入 -> Temu 只读同步准备
- Docker env 透传和 `.env` 示例

尚未完成：

- 真实 Temu API 签名调用
- Seller Center OAuth/授权回调
- 商品、订单、库存字段映射
- 同步任务、dry-run、导入和冲突处理
- 按 storeId 存储多店铺 Temu 授权
- 写回类操作

## 需要你稍后提供

请先确认 Temu Seller Center 是否能看到 Partner/Open Platform、Third-party App 或 API 授权入口。后续真实接入需要：

- 店铺所在区域和站点，例如 global、EU、US、本土店等。
- Temu Partner/Open Platform 应用信息：
  - `SELLERHARBOR_TEMU_APP_KEY`
  - `SELLERHARBOR_TEMU_APP_SECRET`
- Seller Center 授权结果：
  - `SELLERHARBOR_TEMU_ACCESS_TOKEN`
  - `SELLERHARBOR_TEMU_SELLER_ID`
- API base URL：
  - `SELLERHARBOR_TEMU_API_BASE_URL`
- 是否有 sandbox/test shop：
  - `SELLERHARBOR_TEMU_SANDBOX`
- 当前账号开放的接口权限截图或文档：
  - 商品列表 / SKU / Listing 读取
  - 订单列表读取
  - 订单履约 / 发货读取
  - 库存相关读取
  - Webhook / 事件订阅
  - 价格或库存写回权限是否存在，先只记录，不启用

不要把 app secret 或 access token 发到聊天里。实际接入时请写入本机 `.env` 或部署环境变量。

当前 Temu 凭证只代表默认店铺。真实多店铺时，每个 Temu 店铺必须有独立 storeId、授权 token、权限范围和同步任务，不能复用另一个店铺的 token。

## 分阶段落地

### Phase 1: 授权与连通性

- 在设置页看到 Temu 状态从 `needs_credentials` 变成 `ready`。
- 用后端调试脚本验证签名、token、基础接口连通。
- 不写业务表，只记录连通性和权限范围。

### Phase 2: 只读 dry-run

- 拉取商品、SKU、Listing 状态。
- 拉取订单、履约状态和近 7/30 天销量信号。
- 拉取库存相关字段。
- 输出字段映射报告，不创建或覆盖 SellerHarbor 商品。

### Phase 3: 导入 SellerHarbor 主档

- 将 Temu 商品映射为 SellerHarbor `Product`。
- 将 Temu 店铺映射为 SellerHarbor `Store`，Listing 通过 `storeId + productId` 关联。
- 标记 `platforms=temu`、`temuStatus`、`sku`、`availableStock`、`weeklySales`、`rating`、`reviewCount` 等属性。
- 保留外部 ID、最近同步时间和来源追踪。
- 冲突时人工确认。

### Phase 4: 后台同步

- 用 Redis worker 执行定时同步。
- 加入重试、幂等、速率限制和审计事件。
- Webhook 能用时再减少轮询。

### Phase 5: 写回能力

写回范围包括 Listing、价格、库存或履约动作。默认保持禁用，必须满足：

- 同步前预览。
- 人工确认。
- 审计日志。
- 失败重试和回滚策略。
- 对高风险操作设置更高权限。

## 官方参考入口

- Temu Partner Platform: https://partner.temu.com/
- Seller Authorization Guide: https://partner.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303
- Authorization callback: https://partner.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a
- Temu Open Platform Postman: https://www.postman.com/temu-open/temu-open-platform/overview
