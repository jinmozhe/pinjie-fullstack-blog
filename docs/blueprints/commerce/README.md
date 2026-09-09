# 电商业务蓝图

本蓝图说明如何在 `pinjie-fullstack-base` 母版基础上扩展为完整的电商业务系统。

## 派生仓库建议

从母版 fork 或 clone 后，新建独立仓库，例如：

```text
pinjie-commerce-platform
```

## 电商领域划分

| 领域 | 目录 | 说明 |
| --- | --- | --- |
| 商品 | `domains/products/` | SPU/SKU、分类、规格属性 |
| 库存 | `domains/inventory/` | 乐观锁防超卖、预扣减 |
| 购物车 | `domains/cart/` | 后端持久化、双轨合并 |
| 订单 | `domains/orders/` | 状态机、超时自动取消 |
| 支付 | `domains/payment/` | 微信/支付宝回调幂等 |
| 促销 | `domains/promotions/` | 优惠券、满减活动 |
| 评价 | `domains/reviews/` | 商品评价、评分晒图 |

## 详细设计文档（待补充）

- `domain-model.md`：数据库不变量与领域模型
- `checkout-workflow.md`：下单结算完整链路
- `inventory-consistency.md`：高并发库存一致性方案
- `payment-idempotency.md`：支付回调幂等处理

## 参考来源

原始规划文档见 `pinjie-standard` 仓库：

`docs/2026-08-05_全栈Monorepo架构与1Panel部署规划方案.md`
