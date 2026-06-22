"""Tests for AdamScheduler — cron/interval/once job scheduling via APScheduler"""

import pytest
from datetime import datetime, timedelta
from adam.scheduler import AdamScheduler

class TestSchedulerInit:
    def test_default_init(self):
        sched = AdamScheduler()
        assert sched.scheduler is not None
        jobs = sched.list_jobs()
        assert isinstance(jobs, list)

    def test_init_with_engine(self):
        sched = AdamScheduler(engine="dummy")
        assert sched.scheduler is not None

class TestSchedulerJobs:
    @pytest.fixture
    def sched(self):
        return AdamScheduler()

    async def _dummy_job(self):
        """Dummy async job for testing"""
        self._ran = True

    def test_add_interval(self, sched):
        self._ran = False
        sched.add_interval("test_interval", seconds=3600, func=self._dummy_job, name="test")
        jobs = sched.list_jobs()
        ids = [j["id"] for j in jobs]
        assert "test_interval" in ids

    def test_add_interval_with_args(self, sched):
        async def _job_with_args(msg):
            self._last_msg = msg
        sched.add_interval("test_args", seconds=3600, func=_job_with_args, args=["hello"], name="args_test")
        assert sched.get_job("test_args") is not None

    def test_add_cron(self, sched):
        self._ran = False
        sched.add_cron("test_cron", "0 0 * * *", func=self._dummy_job, name="daily")
        jobs = sched.list_jobs()
        ids = [j["id"] for j in jobs]
        assert "test_cron" in ids

    def test_add_once(self, sched):
        self._ran = False
        future = datetime.now() + timedelta(hours=1)
        sched.add_once("test_once", future, func=self._dummy_job, name="one_off")
        jobs = sched.list_jobs()
        ids = [j["id"] for j in jobs]
        assert "test_once" in ids

    def test_add_duplicate_id(self, sched):
        """Adding a job with an existing ID replaces it"""
        async def _j1(): pass
        async def _j2(): pass
        sched.add_interval("dup", seconds=60, func=_j1)
        sched.add_interval("dup", seconds=120, func=_j2)
        job = sched.get_job("dup")
        assert job is not None

    def test_remove_existing(self, sched):
        self._ran = False
        sched.add_interval("to_remove", seconds=60, func=self._dummy_job)
        assert sched.remove("to_remove") is True
        assert sched.get_job("to_remove") is None

    def test_remove_nonexistent(self, sched):
        assert sched.remove("nonexistent") is False

    def test_list_jobs_format(self, sched):
        self._ran = False
        sched.add_interval("fmt_test", seconds=3600, func=self._dummy_job, name="format_check")
        jobs = sched.list_jobs()
        assert len(jobs) >= 1
        job = jobs[0]
        assert "id" in job
        assert "type" in job
        assert "name" in job

    def test_get_job(self, sched):
        self._ran = False
        sched.add_interval("get_test", seconds=3600, func=self._dummy_job, name="gettable")
        job = sched.get_job("get_test")
        assert job is not None
        assert job["id"] == "get_test"
        assert job["name"] == "gettable"

    def test_get_job_nonexistent(self, sched):
        assert sched.get_job("no_such_job") is None

class TestSchedulerLifecycle:
    @pytest.fixture
    def sched(self):
        s = AdamScheduler()
        yield s
        s.stop()

    def test_start_stop(self, sched):
        """start() and stop() don't raise"""
        sched.start()
        sched.stop()

    def test_double_start(self, sched):
        sched.start()
        sched.start()  # should not raise

    def test_lazy_start_on_add(self, sched):
        """add_* should auto-start if not running"""
        async def _j(): pass
        sched.add_interval("lazy", seconds=60, func=_j)
        jobs = sched.list_jobs()
        assert len(jobs) >= 1

    def test_stop_halts_scheduler(self, sched):
        async def _j(): pass
        sched.add_interval("stop_test", seconds=60, func=_j)
        sched.stop()
        # Should be able to add after stop (it will auto-restart)
        sched.add_interval("after_stop", seconds=60, func=_j)
        assert sched.get_job("after_stop") is not None
