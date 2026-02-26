from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from task.models import Task

BASENAME = "task"  


class TaskApiTests(APITestCase):
    def setUp(self):
        self.list_url = reverse(f"{BASENAME}-list")

    def _create_task(self, **overrides) -> Task:
        """
        Crea tareas en BD directamente para preparar escenarios de prueba.
        """
        data = {
            "title": "Tarea base",
            "description": "Desc",
            "status": "pending",
            "due_date": timezone.now() + timedelta(days=3),
            "created_by_name": "Yerlys",
        }
        data.update(overrides)
        return Task.objects.create(**data)

    def _detail_url(self, task_id: int) -> str:
        return reverse(f"{BASENAME}-detail", args=[task_id])

    def _status_url(self, task_id: int) -> str:
        # action change_status => "{basename}-change-status"
        return reverse(f"{BASENAME}-change-status", args=[task_id])

    def _upcoming_url(self) -> str:
        # action upcoming => "{basename}-upcoming"
        return reverse(f"{BASENAME}-upcoming")

    # -------------------------
    # CREATE
    # -------------------------
    def test_create_task_success(self):
        payload = {
            "title": "Comprar mercado",
            "description": "Leche, huevos",
            "status": "pending",
            "due_date": (timezone.now() + timedelta(days=2)).isoformat(),
            "created_by_name": "Yerlys",
        }

        res = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.assertIn("id", res.data)
        self.assertEqual(res.data["title"], payload["title"])
        self.assertEqual(res.data["status"], payload["status"])
        self.assertIsNotNone(res.data.get("created_at"))
        self.assertIsNotNone(res.data.get("updated_at"))

    def test_create_task_invalid_status_returns_400(self):
        payload = {
            "title": "X",
            "status": "invalid_status",
            "created_by_name": "Yerlys",
        }

        res = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Si tienes custom_exception_handler, viene envuelto en "error"
        if isinstance(res.data, dict) and "error" in res.data:
            self.assertIn("details", res.data["error"])
        else:
            self.assertIn("status", res.data)

    # -------------------------
    # LIST
    # -------------------------
    def test_list_excludes_deleted_by_default(self):
        t1 = self._create_task(title="A")
        t2 = self._create_task(title="B")
        t2.soft_delete()

        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        returned_ids = [item["id"] for item in items]

        self.assertIn(t1.id, returned_ids)
        self.assertNotIn(t2.id, returned_ids)

    def test_list_include_deleted_true(self):
        t1 = self._create_task(title="A")
        t2 = self._create_task(title="B")
        t2.soft_delete()

        res = self.client.get(self.list_url + "?include_deleted=true")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        returned_ids = [item["id"] for item in items]

        self.assertIn(t1.id, returned_ids)
        self.assertIn(t2.id, returned_ids)

    # -------------------------
    # RETRIEVE
    # -------------------------
    def test_retrieve_task_success(self):
        task = self._create_task(title="Detalle")

        res = self.client.get(self._detail_url(task.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], task.id)
        self.assertEqual(res.data["title"], "Detalle")

    def test_retrieve_deleted_task_without_include_deleted_returns_404(self):
        task = self._create_task()
        task.soft_delete()

        res = self.client.get(self._detail_url(task.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # UPDATE / PATCH
    # -------------------------
    def test_patch_task_updates_fields(self):
        task = self._create_task(title="Antes", description="Antes desc")

        res = self.client.patch(self._detail_url(task.id), {"title": "Después"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Después")

    # -------------------------
    # SOFT DELETE
    # -------------------------
    def test_delete_soft_delete_marks_deleted_at(self):
        task = self._create_task()

        res = self.client.delete(self._detail_url(task.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        task.refresh_from_db()
        self.assertIsNotNone(task.deleted_at)

        # ya no debe salir en list normal
        res2 = self.client.get(self.list_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        data = res2.data
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        returned_ids = [item["id"] for item in items]

        self.assertNotIn(task.id, returned_ids)

    # -------------------------
    # CHANGE STATUS
    # -------------------------
    def test_change_status_success(self):
        task = self._create_task(status="pending")

        res = self.client.patch(self._status_url(task.id), {"status": "completed"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "completed")

        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_change_status_invalid_returns_400(self):
        task = self._create_task()

        res = self.client.patch(self._status_url(task.id), {"status": "xxx"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------
    # UPCOMING
    # -------------------------
    def test_upcoming_returns_only_matching_tasks(self):
        now = timezone.now()

        # debe entrar: vence dentro de 7 días, no eliminada, due_date no null, no completada
        self._create_task(title="ok1", status="pending", due_date=now + timedelta(days=2))
        self._create_task(title="ok2", status="postponed", due_date=now + timedelta(hours=10))

        # no entra: completed
        self._create_task(title="no_completed", status="completed", due_date=now + timedelta(days=2))

        # no entra: sin due_date
        self._create_task(title="no_due", due_date=None)

        # no entra: ya vencida
        self._create_task(title="past", due_date=now - timedelta(hours=1))

        # no entra: fuera de rango (> 7 días)
        self._create_task(title="far", due_date=now + timedelta(days=10))

        # no entra: eliminada
        t_deleted = self._create_task(title="deleted", due_date=now + timedelta(days=2))
        t_deleted.soft_delete()

        res = self.client.get(self._upcoming_url() + "?within_days=7")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        titles = [item["title"] for item in items]

        self.assertIn("ok1", titles)
        self.assertIn("ok2", titles)

        self.assertNotIn("no_completed", titles)
        self.assertNotIn("no_due", titles)
        self.assertNotIn("past", titles)
        self.assertNotIn("far", titles)
        self.assertNotIn("deleted", titles)

    def test_upcoming_within_days_non_int_returns_400(self):
        res = self.client.get(self._upcoming_url() + "?within_days=abc")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upcoming_within_days_negative_returns_400(self):
        res = self.client.get(self._upcoming_url() + "?within_days=-1")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)