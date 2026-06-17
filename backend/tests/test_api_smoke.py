from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

_temp_dir = tempfile.TemporaryDirectory()

os.environ["SELLERHARBOR_ENV"] = "development"
os.environ["SELLERHARBOR_DB_PATH"] = str(Path(_temp_dir.name) / "sellerharbor-test.db")
os.environ["SELLERHARBOR_SEED_DEMO"] = "true"
os.environ["SELLERHARBOR_LLM_BASE_URL"] = "http://127.0.0.1:9"
os.environ["SELLERHARBOR_LLM_API_KEY"] = "test-token"
os.environ["SELLERHARBOR_LLM_MODEL"] = "test-model"
os.environ["SELLERHARBOR_LLM_CONNECT_TIMEOUT_SECONDS"] = "0.2"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import repository  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.models.schemas import GeneratedContent, QualityReport  # noqa: E402
from app.services.llm import _parse_json_object  # noqa: E402


class ApiSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repository.init_db()
        repository.seed_demo()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()
        _temp_dir.cleanup()

    def test_health_and_read_models(self) -> None:
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        self.assertEqual(self.client.get("/api/health").status_code, 200)

        products = self.client.get("/api/products")
        feedbacks = self.client.get("/api/feedback")

        self.assertEqual(products.status_code, 200)
        self.assertEqual(feedbacks.status_code, 200)
        self.assertGreaterEqual(len(products.json()), 1)
        self.assertGreaterEqual(len(feedbacks.json()), 1)

    def test_business_overview_summarizes_operational_readiness(self) -> None:
        response = self.client.get("/api/business/overview")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["positioning"], "内容与评价运营助手")
        self.assertIn("评价邀请", body["primaryUseCases"])
        self.assertGreaterEqual(body["evidenceCoverage"]["totalProducts"], 1)
        self.assertIn("coverageRate", body["evidenceCoverage"])
        self.assertIn("pending", body["reviewFunnel"])
        self.assertGreaterEqual(len(body["recommendedActions"]), 1)

    def test_commerce_overview_tracks_cross_border_operations(self) -> None:
        headers = {"X-SellerHarbor-Tenant-ID": "tenant-commerce-e2e", "X-SellerHarbor-Actor": "commerce-test"}
        product_response = self.client.post(
            "/api/products",
            headers=headers,
            json={
                "name": "跨境低库存测试水杯",
                "category": "Outdoor Bottle",
                "attributes": {
                    "sku": "TT-CUP-001",
                    "platforms": "temu,tiktok_shop",
                    "temuStatus": "live",
                    "tiktokStatus": "draft",
                    "warehouse": "US-West LA 3PL",
                    "warehouseCountry": "US",
                    "availableStock": "3",
                    "reservedStock": "2",
                    "safetyStock": "10",
                    "weeklySales": "42",
                    "rating": "4.8",
                    "reviewCount": "128",
                },
                "sellingPoints": ["双层保温", "轻量便携", "杯盖防漏"],
                "usageScenarios": ["户外徒步", "办公室饮水"],
                "forbiddenClaims": ["最保温", "永久防漏"],
            },
        )
        self.assertEqual(product_response.status_code, 201)
        product = product_response.json()

        response = self.client.get("/api/commerce/overview", headers=headers)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["positioning"], "SellerHarbor 跨境卖家商品运营港")
        self.assertIn("海外仓库存分配", body["operatingFocus"])
        self.assertEqual({item["platform"] for item in body["platforms"]}, {"temu", "tiktok_shop"})
        temu = next(item for item in body["platforms"] if item["platform"] == "temu")
        tiktok = next(item for item in body["platforms"] if item["platform"] == "tiktok_shop")
        self.assertEqual(temu["readyListings"], 1)
        self.assertEqual(tiktok["watchListings"], 1)
        self.assertTrue(any(warehouse["name"] == "US-West LA 3PL" for warehouse in body["warehouses"]))
        self.assertTrue(any(alert["productId"] == product["id"] and alert["status"] == "low_stock" for alert in body["inventoryAlerts"]))
        self.assertEqual(body["hotProducts"][0]["sku"], "TT-CUP-001")
        self.assertTrue(any(action["key"] == "resolve_inventory_alerts" for action in body["recommendedActions"]))

    def test_llm_health_reports_unavailable(self) -> None:
        response = self.client.get("/api/llm/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["configured"])
        self.assertEqual(body["status"], "unavailable")
        self.assertIn("connection", body["detail"])

    def test_readiness_includes_component_checks(self) -> None:
        response = self.client.get("/api/readiness")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["environment"], "development")
        self.assertIn("database", {check["key"] for check in body["checks"]})
        self.assertIn("llm", {check["key"] for check in body["checks"]})
        self.assertIn("generation_queue", {check["key"] for check in body["checks"]})

    def test_readiness_skips_unconfigured_llm_in_development(self) -> None:
        with patch(
            "app.services.readiness.llm_client.health",
            new=AsyncMock(
                return_value={
                    "status": "unconfigured",
                    "configured": False,
                    "provider": "anthropic",
                    "model": "test-model",
                    "baseUrl": "http://127.0.0.1:9",
                    "detail": "missing apiKey",
                    "latencyMs": None,
                }
            ),
        ):
            response = self.client.get("/api/readiness")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "healthy")
        llm_check = next(check for check in body["checks"] if check["key"] == "llm")
        self.assertEqual(llm_check["status"], "skipped")

    def test_metrics_and_request_id_are_exposed(self) -> None:
        response = self.client.get("/api/metrics", headers={"X-Request-ID": "test-request-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "test-request-id")
        body = response.json()
        self.assertIn("requestsTotal", body)
        self.assertIn("generationTaskStatusCounts", body)

    def test_rate_limit_blocks_when_threshold_is_exceeded(self) -> None:
        original_enabled = settings.rate_limit_enabled
        original_limit = settings.requests_per_minute
        object.__setattr__(settings, "rate_limit_enabled", True)
        object.__setattr__(settings, "requests_per_minute", 1)
        try:
            headers = {"X-SellerHarbor-Actor": "rate-limit-test"}
            self.assertEqual(self.client.get("/api/products", headers=headers).status_code, 200)
            blocked = self.client.get("/api/feedback", headers=headers)
            self.assertEqual(blocked.status_code, 429)
            self.assertIn("Retry-After", blocked.headers)
        finally:
            object.__setattr__(settings, "rate_limit_enabled", original_enabled)
            object.__setattr__(settings, "requests_per_minute", original_limit)

    def test_api_key_gate_blocks_business_api_when_enabled(self) -> None:
        original_required = settings.auth_required
        original_keys = settings.api_keys
        object.__setattr__(settings, "auth_required", True)
        object.__setattr__(settings, "api_keys", ["test-secret"])
        try:
            self.assertEqual(self.client.get("/healthz").status_code, 200)
            self.assertEqual(self.client.get("/api/products").status_code, 401)
            allowed = self.client.get("/api/products", headers={"X-SellerHarbor-API-Key": "test-secret"})
            self.assertEqual(allowed.status_code, 200)
        finally:
            object.__setattr__(settings, "auth_required", original_required)
            object.__setattr__(settings, "api_keys", original_keys)

    def test_tenant_header_isolates_business_data(self) -> None:
        create_response = self.client.post(
            "/api/products",
            headers={"X-SellerHarbor-Tenant-ID": "tenant-a", "X-SellerHarbor-Actor": "tenant-test"},
            json={
                "name": "租户隔离测试商品",
                "category": "测试",
                "sellingPoints": ["只属于 A"],
                "usageScenarios": ["隔离验证"],
                "forbiddenClaims": ["第一"],
            },
        )

        self.assertEqual(create_response.status_code, 201)
        product = create_response.json()
        self.assertEqual(product["tenantId"], "tenant-a")

        tenant_a_products = self.client.get("/api/products", headers={"X-SellerHarbor-Tenant-ID": "tenant-a"}).json()
        tenant_b_products = self.client.get("/api/products", headers={"X-SellerHarbor-Tenant-ID": "tenant-b"}).json()

        self.assertTrue(any(item["id"] == product["id"] for item in tenant_a_products))
        self.assertFalse(any(item["id"] == product["id"] for item in tenant_b_products))
        self.assertEqual(
            self.client.get(f"/api/products/{product['id']}", headers={"X-SellerHarbor-Tenant-ID": "tenant-b"}).status_code,
            404,
        )

    def test_tenant_allowlist_rejects_unknown_tenant(self) -> None:
        original_allowed = settings.allowed_tenant_ids
        object.__setattr__(settings, "allowed_tenant_ids", ["tenant-allowed"])
        try:
            blocked = self.client.get("/api/products", headers={"X-SellerHarbor-Tenant-ID": "tenant-blocked"})
            allowed = self.client.get("/api/products", headers={"X-SellerHarbor-Tenant-ID": "tenant-allowed"})

            self.assertEqual(blocked.status_code, 403)
            self.assertEqual(allowed.status_code, 200)
        finally:
            object.__setattr__(settings, "allowed_tenant_ids", original_allowed)

    def test_stale_generation_tasks_are_recovered_as_failed(self) -> None:
        product = self.client.get("/api/products").json()[0]
        task = repository.create_generation_task_pending(
            repository.GenerationConfig(
                productId=product["id"],
                contentType="review_draft",
                platform="taobao",
                tone="natural",
                length="short",
                persona="third_person",
                count=1,
            ),
            repository.get_product(product["id"]),
        )
        with repository.connect() as conn:
            conn.execute(
                "UPDATE generation_tasks SET updated_at = ? WHERE id = ?",
                ("2000-01-01T00:00:00Z", task.id),
            )
            conn.commit()

        recovered = repository.fail_stale_generation_tasks(1)

        self.assertTrue(any(item.id == task.id and item.status == "failed" for item in recovered))
        self.assertEqual(repository.get_generation_task(task.id).status, "failed")

    def test_generation_fails_fast_when_llm_unavailable(self) -> None:
        products = self.client.get("/api/products").json()
        feedbacks = self.client.get("/api/feedback").json()
        feedback_by_product = {feedback["productId"]: feedback for feedback in feedbacks}
        product = next(product for product in products if product["id"] in feedback_by_product)
        feedback = feedback_by_product[product["id"]]

        response = self.client.post(
            "/api/generations",
            json={
                "productId": product["id"],
                "feedbackId": feedback["id"],
                "contentType": "review_draft",
                "platform": "taobao",
                "tone": "natural",
                "length": "short",
                "persona": "third_person",
                "count": 1,
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("LLM unavailable", response.json()["detail"])

    def test_async_generation_job_completes_and_is_audited(self) -> None:
        products = self.client.get("/api/products").json()
        feedbacks = self.client.get("/api/feedback").json()
        feedback_by_product = {feedback["productId"]: feedback for feedback in feedbacks}
        product = next(product for product in products if product["id"] in feedback_by_product)
        feedback = feedback_by_product[product["id"]]
        fake_content = GeneratedContent(
            id="gen_test_async",
            taskId="temporary",
            text="这是一条通过异步任务生成的测试内容。",
            score=88,
            riskFlags=[],
            sourceTrace=["test"],
            qualityReport=QualityReport(overallScore=88),
            createdAt=repository.now_iso(),
        )

        with (
            patch("app.api.routes.llm_client.ensure_ready", new=AsyncMock()),
            patch("app.api.routes.run_generation_agent", new=AsyncMock(return_value=[fake_content])),
        ):
            response = self.client.post(
                "/api/generation-jobs",
                headers={"X-SellerHarbor-Actor": "tester"},
                json={
                    "productId": product["id"],
                    "feedbackId": feedback["id"],
                    "contentType": "review_draft",
                    "platform": "taobao",
                    "tone": "natural",
                    "length": "short",
                    "persona": "third_person",
                    "count": 1,
                },
            )

        self.assertEqual(response.status_code, 202)
        task_id = response.json()["id"]
        task = self.client.get(f"/api/generation-jobs/{task_id}").json()
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["contents"][0]["taskId"], task_id)

        audit_events = self.client.get("/api/audit/events").json()
        self.assertTrue(any(event["action"] == "generation.completed" and event["resourceId"] == task_id for event in audit_events))

    def test_feedback_organization_e2e_flow_reaches_exportable_content(self) -> None:
        headers = {"X-SellerHarbor-Tenant-ID": "tenant-organize-e2e", "X-SellerHarbor-Actor": "organizer-e2e"}
        product_response = self.client.post(
            "/api/products",
            headers=headers,
            json={
                "name": "E2E 静音料理机",
                "category": "厨房电器",
                "attributes": {"容量": "1.5L", "颜色": "白色"},
                "sellingPoints": ["预约功能", "自清洗", "低噪运行"],
                "usageScenarios": ["早餐豆浆", "宝宝辅食"],
                "forbiddenClaims": ["治疗", "最安静"],
            },
        )
        self.assertEqual(product_response.status_code, 201)
        product = product_response.json()

        organize_response = self.client.post(
            "/api/feedback/organize",
            headers=headers,
            json={
                "productId": product["id"],
                "sourceType": "cs_summary",
                "consentStatus": "confirmed",
                "rawText": "客户回访说收到后没有异味，预约功能很方便，晚上设好早上能喝豆浆。自清洗省事，比老机器安静。",
                "platform": "taobao",
            },
        )

        self.assertEqual(organize_response.status_code, 200)
        organized = organize_response.json()
        self.assertGreaterEqual(organized["readinessScore"], 60)
        self.assertIn("收到后没有异味", " ".join(organized["confirmedFacts"]))
        self.assertIn("预约功能很方便", " ".join(organized["subjectiveOpinions"]))
        self.assertIn("自清洗省事", " ".join(organized["subjectiveOpinions"]))
        self.assertIn("recommendation", organized["recommendedContentTypes"])

        feedback_response = self.client.post(
            "/api/feedback",
            headers=headers,
            json={
                "productId": product["id"],
                "sourceType": organized["sourceType"],
                "sourceSummary": organized["sourceSummary"],
                "confirmedFacts": organized["confirmedFacts"],
                "subjectiveOpinions": organized["subjectiveOpinions"],
                "consentStatus": organized["consentStatus"],
            },
        )
        self.assertEqual(feedback_response.status_code, 201)
        feedback = feedback_response.json()

        overview_after_feedback = self.client.get("/api/business/overview", headers=headers).json()
        self.assertEqual(overview_after_feedback["evidenceCoverage"]["productsWithUsableFeedback"], 1)
        self.assertEqual(overview_after_feedback["evidenceCoverage"]["coverageRate"], 100)

        fake_content = GeneratedContent(
            id="gen_e2e_organized",
            taskId="temporary",
            text="这款料理机适合早餐豆浆场景，预约功能和自清洗都比较省心，反馈里也提到到手无异味。",
            score=91,
            riskFlags=[],
            sourceTrace=["organizer.raw_feedback", "feedback.confirmed_facts", "product.selling_points"],
            qualityReport=QualityReport(overallScore=91, factConsistency=92, specificity=88),
            createdAt=repository.now_iso(),
        )
        with (
            patch("app.api.routes.llm_client.ensure_ready", new=AsyncMock()),
            patch("app.api.routes.run_generation_agent", new=AsyncMock(return_value=[fake_content])),
        ):
            generation_response = self.client.post(
                "/api/generation-jobs",
                headers=headers,
                json={
                    "productId": product["id"],
                    "feedbackId": feedback["id"],
                    "contentType": "recommendation",
                    "platform": "taobao",
                    "tone": "natural",
                    "length": "short",
                    "persona": "merchant",
                    "count": 1,
                },
            )

        self.assertEqual(generation_response.status_code, 202)
        task = self.client.get(f"/api/generation-jobs/{generation_response.json()['id']}", headers=headers).json()
        self.assertEqual(task["status"], "completed")
        content = task["contents"][0]

        review_response = self.client.post(
            f"/api/contents/{content['id']}/review",
            headers=headers,
            json={"status": "approved", "reviewer": "e2e-reviewer", "comment": "来源清晰，可导出"},
        )
        self.assertEqual(review_response.status_code, 200)
        self.assertEqual(review_response.json()["reviewStatus"], "approved")

        overview_after_review = self.client.get("/api/business/overview", headers=headers).json()
        self.assertEqual(overview_after_review["reviewFunnel"]["approved"], 1)
        self.assertEqual(overview_after_review["reviewFunnel"]["exportable"], 1)
        self.assertTrue(any(item["contentType"] == "recommendation" for item in overview_after_review["contentMix"]))

        audit_events = self.client.get("/api/audit/events", headers=headers).json()
        self.assertTrue(any(event["action"] == "feedback.organized" for event in audit_events))
        self.assertTrue(any(event["action"] == "content.approved" for event in audit_events))

    def test_feedback_organization_e2e_downgrades_risky_claims(self) -> None:
        headers = {"X-SellerHarbor-Tenant-ID": "tenant-organize-risk-e2e", "X-SellerHarbor-Actor": "organizer-risk-e2e"}
        product = self.client.post(
            "/api/products",
            headers=headers,
            json={
                "name": "E2E 健康设备",
                "category": "健康设备",
                "sellingPoints": ["趋势图表", "家庭成员管理"],
                "usageScenarios": ["家庭健康管理"],
                "forbiddenClaims": ["治疗", "医用级"],
            },
        ).json()

        response = self.client.post(
            "/api/feedback/organize",
            headers=headers,
            json={
                "productId": product["id"],
                "sourceType": "customer_review",
                "consentStatus": "confirmed",
                "rawText": "客户说趋势图表清楚，但也提到可能有治疗效果，包装到手完整。",
                "platform": "jd",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("forbidden_claim", body["riskFlags"])
        self.assertIn("uncertain_claims_present", body["riskFlags"])
        self.assertEqual(body["recommendedContentTypes"], ["review_invitation", "cs_followup"])
        self.assertTrue(any("删除禁用词" in action for action in body["nextActions"]))

    def test_product_create_records_audit_event(self) -> None:
        response = self.client.post(
            "/api/products",
            headers={"X-SellerHarbor-Actor": "tester"},
            json={
                "name": "审计测试商品",
                "category": "测试",
                "sellingPoints": ["稳定", "可追溯"],
                "usageScenarios": ["投产演练"],
                "forbiddenClaims": ["第一"],
            },
        )

        self.assertEqual(response.status_code, 201)
        product_id = response.json()["id"]
        audit_events = self.client.get("/api/audit/events").json()
        self.assertTrue(any(event["action"] == "product.created" and event["resourceId"] == product_id for event in audit_events))

    def test_llm_json_parser_repairs_common_model_format_drift(self) -> None:
        data = _parse_json_object(
            """
            ```json
            {
              "items": [
                {
                  "text": "第一行
第二行",
                  "score": 82,
                  "riskFlags": [],
                }
              ],
            }
            ```
            """
        )

        self.assertEqual(data["items"][0]["text"], "第一行\n第二行")
        self.assertEqual(data["items"][0]["score"], 82)


if __name__ == "__main__":
    unittest.main()
