# 多店铺管理规划

SellerHarbor 当前按单店铺运行，但数据边界已经按多店铺预留。核心原则是：商品主档属于商家租户，平台店铺属于租户下的销售渠道，Listing、授权、同步任务和库存占用按店铺关联。

## 当前实现状态

已完成：

- 后端默认店铺配置项：`SELLERHARBOR_DEFAULT_STORE_*`
- 多店铺开关和允许列表：`SELLERHARBOR_MULTI_STORE_ENABLED`、`SELLERHARBOR_ALLOWED_STORE_IDS`
- 后端状态接口：`GET /api/stores/registry`
- readiness 检查：`store_registry`
- 前端设置页：系统设置 -> 平台接入 -> 店铺管理预留
- Docker env 透传和 `.env` 示例

当前仍是单店铺可用模式：

- 商品主档仍在租户层维护，不绑定某个店铺。
- Temu 凭证仍通过环境变量配置给默认店铺。
- 平台状态、仓库、库存和销量暂存在 `products.attributes`。
- 暂不提供店铺 CRUD、真实多店铺授权、跨店铺同步任务和写回操作。

## 数据边界

### Tenant

租户代表商家或团队，是最高数据隔离边界。当前通过 `X-SellerHarbor-Tenant-ID` 传递。

后续表：

```text
tenants
users
roles
```

### Store

店铺代表 Temu、TikTok Shop 等平台里的一个销售账号或店铺。一个租户可以拥有多个店铺。

后续表：

```text
stores(
  id,
  tenant_id,
  platform,
  name,
  region,
  status,
  default_warehouse_id
)
```

### Product

商品是租户级主数据。不要因为一个商品上架到多个店铺而复制多份 Product。

当前表：

```text
products
```

### PlatformListing

Listing 负责连接 Product 和 Store。同一商品在不同店铺可以拥有不同标题、价格、图片、审核状态和外部商品 ID。

后续表：

```text
platform_listings(
  id,
  tenant_id,
  store_id,
  product_id,
  external_listing_id,
  platform_sku,
  title,
  status,
  sync_state,
  last_synced_at
)
```

### Warehouse And Inventory

海外仓属于租户级资源，可被多个店铺共享。库存分配需要区分总库存、可用库存、平台占用和安全库存。

后续表：

```text
warehouses
inventory_items
inventory_movements
platform_allocations
```

### Store Credentials

平台授权凭证必须按店铺隔离。多店铺不能复用 token。

后续表：

```text
store_credentials(
  id,
  tenant_id,
  store_id,
  provider,
  encrypted_payload,
  scopes,
  expires_at,
  rotated_at
)
```

## API 规划

当前：

- `GET /api/stores/registry`：读取默认店铺、扩展槽和数据边界。
- `GET /api/integrations/temu/status`：读取默认 Temu 接入状态。

后续：

- `GET /api/stores`
- `POST /api/stores`
- `PATCH /api/stores/{store_id}`
- `GET /api/stores/{store_id}/integrations`
- `POST /api/stores/{store_id}/sync-jobs`
- `GET /api/platform-listings?storeId=...`
- `GET /api/inventory/allocations?storeId=...`

## 落地顺序

1. 保持当前单店铺默认可用。
2. 新增 `stores` 表和只读 API，把环境变量默认店铺迁移为数据库记录。
3. 新增 `platform_listings` 表，把 `products.attributes` 里的平台状态迁移出去。
4. 新增仓库和库存分配表，支持共享海外仓按店铺占用。
5. 把 Temu 授权改为按 storeId 存储，先支持只读同步。
6. 接入第二个平台或第二个 Temu 店铺。
7. 写回操作继续保持禁用，直到预览、人工确认、审计、重试和回滚就绪。

## 需要你稍后提供

- 当前默认店铺的真实名称、平台、区域和常用海外仓。
- 如果有第二个店铺，提供平台、区域、店铺名和是否共享同一批仓库。
- Temu / TikTok Shop 的授权入口、权限截图和只读接口可用范围。
- 不要把 app secret、access token 或其他密钥发到聊天里。
