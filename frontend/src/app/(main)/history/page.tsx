"use client";
import { useMemo } from "react";
import { Card, Button, Tag } from "@arco-design/web-react";
import {
  IconFile,
  IconRight,
  IconDownload,
} from "@arco-design/web-react/icon";
import { useRouter } from "next/navigation";
import { useDataStore } from "@/lib/stores/dataStore";
import PageHeader from "@/components/common/PageHeader";
import ScoreBadge from "@/components/common/ScoreBadge";
import ReviewStatusTag from "@/components/common/ReviewStatusTag";
import { ContentTypeTag, PlatformTag, ToneTag } from "@/components/common/ConfigTags";

export default function HistoryPage() {
  const router = useRouter();
  const { tasks, contents } = useDataStore();

  const sortedTasks = useMemo(
    () => [...tasks].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
    [tasks]
  );

  return (
    <div className="max-w-7xl mx-auto">
      <PageHeader
        title="生成记录"
        subtitle="查看历史生成任务和结果"
        icon={<IconFile />}
        extra={
          <Button icon={<IconDownload />}>
            导出全部
          </Button>
        }
      />

      <div className="space-y-4">
        {sortedTasks.map((task, index) => {
          const taskContents = contents.filter((c) => c.taskId === task.id);
          const avgScore = taskContents.length > 0
            ? Math.round(taskContents.reduce((sum, c) => sum + c.score, 0) / taskContents.length)
            : 0;
          const approvedCount = taskContents.filter((c) => c.reviewStatus === "approved").length;

          return (
            <Card
              key={task.id}
              className="hover-lift animate-fade-in"
              style={{ borderRadius: 16, animationDelay: `${index * 60}ms` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold m-0 mb-1" style={{ color: "var(--text-color-1)" }}>
                    {task.productName || "未知商品"}
                  </h3>
                  <div className="flex items-center gap-2 flex-wrap">
                    <ContentTypeTag type={task.config.contentType} />
                    <PlatformTag platform={task.config.platform} />
                    <ToneTag tone={task.config.tone} />
                    <Tag>{task.config.count} 条</Tag>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>
                    {new Date(task.createdAt).toLocaleDateString("zh-CN")}{" "}
                    {new Date(task.createdAt).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  <Tag color={task.status === "completed" ? "green" : task.status === "failed" ? "red" : "blue"}>
                    {task.status === "completed" ? "已完成" : task.status === "failed" ? "失败" : "生成中"}
                  </Tag>
                </div>
              </div>

              {/* Summary stats */}
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                  <div className="text-lg font-bold" style={{ color: "var(--text-color-1)" }}>{taskContents.length}</div>
                  <div className="text-xs" style={{ color: "var(--text-color-3)" }}>生成数量</div>
                </div>
                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                  <div className="text-lg font-bold" style={{ color: "var(--color-primary)" }}>{avgScore}</div>
                  <div className="text-xs" style={{ color: "var(--text-color-3)" }}>平均分</div>
                </div>
                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                  <div className="text-lg font-bold" style={{ color: "var(--color-success)" }}>{approvedCount}</div>
                  <div className="text-xs" style={{ color: "var(--text-color-3)" }}>已通过</div>
                </div>
                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                  <div className="text-lg font-bold" style={{ color: "var(--color-warning)" }}>
                    {taskContents.filter((c) => c.reviewStatus === "pending").length}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-color-3)" }}>待审核</div>
                </div>
              </div>

              {/* Content previews */}
              <div className="space-y-2">
                {taskContents.slice(0, 3).map((content) => (
                  <div
                    key={content.id}
                    className="flex items-center gap-3 p-3 rounded-xl"
                    style={{ backgroundColor: "var(--color-fill-1)" }}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate m-0" style={{ color: "var(--text-color-2)" }}>
                        {content.text.slice(0, 80)}...
                      </p>
                    </div>
                    <ScoreBadge score={content.score} size="small" />
                    <ReviewStatusTag status={content.reviewStatus} />
                  </div>
                ))}
                {taskContents.length > 3 && (
                  <div className="text-center text-xs py-2" style={{ color: "var(--text-color-4)" }}>
                    还有 {taskContents.length - 3} 条内容...
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-4 pt-3 border-t" style={{ borderColor: "var(--border-color-light)" }}>
                <Button type="text" size="small" onClick={() => router.push("/review")}>
                  查看全部 <IconRight />
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
