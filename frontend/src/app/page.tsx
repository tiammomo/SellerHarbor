"use client";
import { useRouter } from "next/navigation";
import { Button, Grid } from "@arco-design/web-react";
import { IconRight, IconArrowRise, IconThumbUp } from "@arco-design/web-react/icon";

const { Row, Col } = Grid;

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="flex items-center justify-center h-screen" style={{ backgroundColor: "var(--bg-color-page)" }}>
      <div className="text-center animate-fade-in max-w-2xl px-6">
        <div
          className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold text-white mx-auto mb-6 shadow-lg"
          style={{ background: "linear-gradient(135deg, #f97316 0%, #f59e0b 58%, #d97706 100%)" }}
        >
          R
        </div>
        <h1 className="text-3xl font-bold mb-3" style={{ color: "var(--text-color-1)" }}>
          ReviewPilot
        </h1>
        <p className="text-lg mb-2" style={{ color: "var(--text-color-2)" }}>
          口碑内容助手
        </p>
        <p className="text-sm mb-8" style={{ color: "var(--text-color-3)" }}>
          基于真实商品信息、客户反馈和品牌语气，生成可审核、可编辑、可追溯的口碑内容草稿
        </p>

        {/* 主要功能入口 */}
        <Row gutter={16} className="mb-8">
          <Col span={12}>
            <div
              className="p-6 rounded-2xl cursor-pointer hover-lift"
              style={{
                background: "linear-gradient(135deg, #f97316 0%, #f59e0b 100%)",
                color: "white",
              }}
              onClick={() => router.push("/trending")}
            >
              <IconArrowRise style={{ fontSize: 48, marginBottom: 16 }} />
              <h3 className="text-xl font-bold mb-2">选品推荐</h3>
              <p className="text-sm opacity-90 mb-4">
                基于市场趋势和销售数据，推荐当前热销商品
              </p>
              <Button
                type="default"
                icon={<IconRight />}
              >
                开始选品
              </Button>
            </div>
          </Col>
          <Col span={12}>
            <div
              className="p-6 rounded-2xl cursor-pointer hover-lift"
              style={{
                background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                color: "white",
              }}
              onClick={() => router.push("/reviews")}
            >
              <IconThumbUp style={{ fontSize: 48, marginBottom: 16 }} />
              <h3 className="text-xl font-bold mb-2">好评生成</h3>
              <p className="text-sm opacity-90 mb-4">
                基于商品信息和用户反馈，生成真实自然的好评内容
              </p>
              <Button
                type="default"
                icon={<IconRight />}
              >
                生成好评
              </Button>
            </div>
          </Col>
        </Row>

        {/* 其他入口 */}
        <div className="flex items-center justify-center gap-4">
          <Button
            size="large"
            onClick={() => router.push("/dashboard")}
            style={{ height: 48, paddingInline: 32, fontSize: 16 }}
          >
            数据看板
          </Button>
          <Button
            size="large"
            onClick={() => router.push("/products")}
            style={{ height: 48, paddingInline: 32, fontSize: 16 }}
          >
            商品管理
          </Button>
        </div>
      </div>
    </div>
  );
}
