"""
Tests for the client evolution system:
  - mg_onboard.py (multilingual onboarding)
  - mg_contribute.py (secure contributions)
  - mg_payment_tracker.py (funnel tracking)
  - 5 persona tests (Russian, Japanese, Spanish, English, Chinese)

Uses mock Claude responses -- no API key needed for CI.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_onboard import (
    detect_domain_local,
    run_onboarding,
    _detect_language,
    _log_session,
)
from scripts.mg_contribute import (
    sanitize_content,
    create_contribution,
    CONTRIB_DIR,
    VALID_TYPES,
    VALID_DOMAINS,
)
from scripts.mg_payment_tracker import (
    track_event,
    FUNNEL_STAGES,
    _load_funnel,
    _save_funnel,
    FUNNEL_PATH,
)


# ============================================================================
# mg_onboard.py tests
# ============================================================================


class TestLanguageDetection:
    def test_russian(self):
        assert _detect_language("Я разрабатываю ML модель") == "ru"

    def test_japanese(self):
        assert _detect_language("材料の弾性率を測定しています") == "ja"

    def test_chinese(self):
        assert _detect_language("我在做有限元分析仿真") == "zh"

    def test_spanish(self):
        assert _detect_language("Trabajo en predicciones ADMET") == "es"

    def test_english(self):
        assert _detect_language("I calculate VaR models") == "en"

    def test_korean(self):
        assert _detect_language("머신러닝 모델을 개발합니다") == "ko"

    def test_french(self):
        assert _detect_language("Je travaille sur des simulations") == "fr"

    def test_german(self):
        assert _detect_language("Ich arbeite an FEM Simulationen") == "de"

    def test_empty(self):
        assert _detect_language("") == "en"


class TestDomainDetection:
    def test_ml_english(self):
        domain, claim = detect_domain_local("I build machine learning models for prediction")
        assert domain == "ml"
        assert claim == "ML_BENCH-01"

    def test_pharma(self):
        domain, claim = detect_domain_local("ADMET solubility toxicity for pharmaceutical drugs")
        assert domain == "pharma"
        assert claim == "PHARMA-01"

    def test_finance(self):
        domain, claim = detect_domain_local("I calculate VaR for trading desk")
        assert domain == "finance"
        assert claim == "FINRISK-01"

    def test_materials(self):
        domain, claim = detect_domain_local("Measuring elastic modulus of aluminum")
        assert domain == "materials"
        assert claim == "MTR-1"

    def test_digital_twin(self):
        domain, claim = detect_domain_local("Finite element analysis simulation")
        assert domain == "digital_twin"
        assert claim == "DT-FEM-01"

    def test_physics(self):
        domain, claim = detect_domain_local("Boltzmann constant thermodynamics")
        assert domain == "physics"
        assert claim == "PHYS-01"

    def test_systems(self):
        domain, claim = detect_domain_local("System identification ARX model control")
        assert domain == "systems"
        assert claim == "SYSID-01"

    def test_fallback_to_ml(self):
        domain, claim = detect_domain_local("something completely unrelated xyz")
        assert domain == "ml"  # default fallback


# ============================================================================
# Persona tests -- 5 languages
# ============================================================================


class TestPersona1Russian:
    """Russian ML engineer persona."""

    def test_language_detected(self):
        text = "Я разрабатываю ML модель для предсказания цен акций"
        assert _detect_language(text) == "ru"

    def test_domain_detected(self):
        text = "Я разрабатываю ML модель для предсказания цен акций"
        domain, claim = detect_domain_local(text)
        assert domain == "ml"
        assert claim == "ML_BENCH-01"

    def test_full_flow_mock(self):
        mock_responses = [
            "Здравствуйте! Я вижу, что вы работаете с ML моделями. "
            "MetaGenesis проверит точность вашей модели криптографически.",
            "Верификация прошла успешно! Ваш результат теперь "
            "криптографически сертифицирован. Ссылка: $299",
        ]
        result = run_onboarding(
            api_key="mock",
            mock_mode=True,
            mock_input="Я разрабатываю ML модель для предсказания цен акций",
            mock_responses=mock_responses,
        )
        assert result is not None
        assert result["domain"] == "ml"
        assert result["claim"] == "ML_BENCH-01"
        assert result["language"] == "ru"
        assert result["passed"] is True


class TestPersona2Japanese:
    """Japanese materials scientist persona."""

    def test_language_detected(self):
        text = "材料の弾性率を測定しています"
        assert _detect_language(text) == "ja"

    def test_domain_detected(self):
        text = "材料の弾性率を測定しています"
        domain, claim = detect_domain_local(text)
        assert domain == "materials"
        assert claim == "MTR-1"

    def test_full_flow_mock(self):
        mock_responses = [
            "こんにちは！材料科学の分野ですね。MetaGenesisは弾性率の"
            "検証を物理アンカー（E=70GPa）を基準に行います。",
            "検証成功！あなたの計測結果は暗号学的に証明されました。"
            "バンドルの価格は$299です。",
        ]
        result = run_onboarding(
            api_key="mock",
            mock_mode=True,
            mock_input="材料の弾性率を測定しています",
            mock_responses=mock_responses,
        )
        assert result is not None
        assert result["domain"] == "materials"
        assert result["language"] == "ja"
        assert result["passed"] is True


class TestPersona3Spanish:
    """Spanish pharma researcher persona."""

    def test_language_detected(self):
        text = "Trabajo en predicciones ADMET para nuevos medicamentos"
        assert _detect_language(text) == "es"

    def test_domain_detected(self):
        text = "Trabajo en predicciones ADMET para nuevos medicamentos"
        domain, claim = detect_domain_local(text)
        assert domain == "pharma"
        assert claim == "PHARMA-01"

    def test_full_flow_mock(self):
        mock_responses = [
            "Hola! Veo que trabajas en predicciones ADMET. MetaGenesis "
            "verifica tus resultados farmaceuticos con certificacion FDA.",
            "Verificacion exitosa! Tu resultado ahora tiene certificacion "
            "criptografica. El bundle cuesta $299.",
        ]
        result = run_onboarding(
            api_key="mock",
            mock_mode=True,
            mock_input="Trabajo en predicciones ADMET para nuevos medicamentos",
            mock_responses=mock_responses,
        )
        assert result is not None
        assert result["domain"] == "pharma"
        assert result["language"] == "es"
        assert result["passed"] is True


class TestPersona4English:
    """English finance quant persona."""

    def test_language_detected(self):
        text = "I calculate VaR models for our trading desk"
        assert _detect_language(text) == "en"

    def test_domain_detected(self):
        text = "I calculate VaR models for our trading desk"
        domain, claim = detect_domain_local(text)
        assert domain == "finance"
        assert claim == "FINRISK-01"

    def test_full_flow_mock(self):
        mock_responses = [
            "Great! You work with VaR models. MetaGenesis can verify "
            "your risk calculations for Basel III compliance.",
            "Verification passed! Your VaR result is cryptographically "
            "certified. Get your permanent bundle for $299.",
        ]
        result = run_onboarding(
            api_key="mock",
            mock_mode=True,
            mock_input="I calculate VaR models for our trading desk",
            mock_responses=mock_responses,
        )
        assert result is not None
        assert result["domain"] == "finance"
        assert result["language"] == "en"
        assert result["passed"] is True


class TestPersona5Chinese:
    """Chinese digital twin engineer persona."""

    def test_language_detected(self):
        text = "我在做有限元分析仿真"
        assert _detect_language(text) == "zh"

    def test_domain_detected(self):
        text = "我在做有限元分析仿真"
        domain, claim = detect_domain_local(text)
        assert domain == "digital_twin"
        assert claim == "DT-FEM-01"

    def test_full_flow_mock(self):
        mock_responses = [
            "你好！我看到你在做有限元分析。MetaGenesis可以验证你的FEM "
            "仿真结果，包括物理锚点链。",
            "验证成功！你的仿真结果已获得密码学认证。"
            "永久验证包价格为$299。",
        ]
        result = run_onboarding(
            api_key="mock",
            mock_mode=True,
            mock_input="我在做有限元分析仿真",
            mock_responses=mock_responses,
        )
        assert result is not None
        assert result["domain"] == "digital_twin"
        assert result["language"] == "zh"
        assert result["passed"] is True


# ============================================================================
# mg_contribute.py tests
# ============================================================================


class TestSanitization:
    def test_strips_imports(self):
        result = sanitize_content("import os; print('hello')")
        assert "import os" not in result
        assert "[REMOVED]" in result

    def test_strips_file_paths(self):
        result = sanitize_content("Look at /usr/bin/python3.py")
        assert "/usr/bin/python3.py" not in result

    def test_strips_code_blocks(self):
        result = sanitize_content("Here is code ```python\nprint('x')\n```")
        assert "```" not in result

    def test_strips_eval(self):
        result = sanitize_content("Try eval('os.system(\"rm -rf\")')")
        assert "eval(" not in result

    def test_preserves_normal_text(self):
        text = "The verification process was great, I loved the results"
        assert sanitize_content(text) == text

    def test_max_length(self):
        long_text = "a" * 3000
        result = sanitize_content(long_text)
        assert len(result) <= 2000

    def test_empty_input(self):
        assert sanitize_content("") == ""
        assert sanitize_content(None) == ""


class TestContributions:
    def setup_method(self):
        self._orig_dir = CONTRIB_DIR
        self._tmp = Path(tempfile.mkdtemp())
        # Monkey-patch CONTRIB_DIR for tests
        import scripts.mg_contribute as mc
        mc.CONTRIB_DIR = self._tmp

    def teardown_method(self):
        import scripts.mg_contribute as mc
        mc.CONTRIB_DIR = self._orig_dir
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_create_bug_report(self):
        contrib = create_contribution(
            "The verification failed with a timeout error",
            "bug_report",
            domain="ml",
        )
        assert contrib["type"] == "bug_report"
        assert contrib["domain"] == "ml"
        assert contrib["sha256"]
        assert contrib["value_score"] is None
        assert len(contrib["content"]) > 0

    def test_create_domain_idea(self):
        contrib = create_contribution(
            "Could MetaGenesis verify quantum computing results?",
            "domain_idea",
            domain="other",
        )
        assert contrib["type"] == "domain_idea"

    def test_create_success_story(self):
        contrib = create_contribution(
            "Used it for ML benchmark, passed Basel III audit",
            "success_story",
            domain="finance",
        )
        assert contrib["type"] == "success_story"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid type"):
            create_contribution("test", "invalid_type")

    def test_code_only_content_rejected(self):
        with pytest.raises(ValueError, match="empty or contained only code"):
            create_contribution("import os", "bug_report")

    def test_file_created(self):
        contrib = create_contribution("Great tool!", "improvement", domain="ml")
        files = list(self._tmp.glob("contrib_*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["id"] == contrib["id"]

    def test_sha256_deterministic(self):
        """Same content + timestamp should produce same hash."""
        contrib = create_contribution("Test content here", "bug_report")
        payload = json.dumps(
            {"content": contrib["content"], "timestamp": contrib["timestamp"],
             "type": "bug_report"},
            sort_keys=True, separators=(",", ":"),
        )
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert contrib["sha256"] == expected

    def test_language_detection_in_contribution(self):
        contrib = create_contribution(
            "Отличный инструмент для верификации",
            "success_story",
            domain="ml",
        )
        assert contrib["language"] == "ru"


# ============================================================================
# mg_payment_tracker.py tests
# ============================================================================


class TestPaymentTracker:
    def setup_method(self):
        self._orig_path = FUNNEL_PATH
        self._tmp = Path(tempfile.mkdtemp())
        self._tmp_path = self._tmp / "payment_funnel.json"
        import scripts.mg_payment_tracker as mpt
        mpt.FUNNEL_PATH = self._tmp_path

    def teardown_method(self):
        import scripts.mg_payment_tracker as mpt
        mpt.FUNNEL_PATH = self._orig_path
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_track_event_creates_file(self):
        track_event("started_onboarding", domain="ml", language="en")
        assert self._tmp_path.exists()

    def test_funnel_stages(self):
        track_event("started_onboarding", domain="ml", language="en")
        track_event("completed_verification", domain="ml", language="en")
        track_event("saw_payment", domain="ml", language="en")

        data = json.loads(self._tmp_path.read_text(encoding="utf-8"))
        assert data["sessions"]["started_onboarding"] == 1
        assert data["sessions"]["completed_verification"] == 1
        assert data["sessions"]["saw_payment"] == 1
        assert data["sessions"]["converted"] == 0

    def test_conversion_rate(self):
        for _ in range(10):
            track_event("started_onboarding")
        for _ in range(2):
            track_event("converted")

        data = json.loads(self._tmp_path.read_text(encoding="utf-8"))
        assert data["conversion_rate"] == pytest.approx(0.2)

    def test_by_domain_tracking(self):
        track_event("started_onboarding", domain="ml")
        track_event("started_onboarding", domain="pharma")
        track_event("started_onboarding", domain="ml")

        data = json.loads(self._tmp_path.read_text(encoding="utf-8"))
        assert data["by_domain"]["ml"]["started_onboarding"] == 2
        assert data["by_domain"]["pharma"]["started_onboarding"] == 1

    def test_by_language_tracking(self):
        track_event("started_onboarding", language="ru")
        track_event("started_onboarding", language="ja")

        data = json.loads(self._tmp_path.read_text(encoding="utf-8"))
        assert data["by_language"]["ru"]["started_onboarding"] == 1
        assert data["by_language"]["ja"]["started_onboarding"] == 1

    def test_invalid_stage_ignored(self):
        track_event("invalid_stage")
        assert not self._tmp_path.exists()


# ============================================================================
# Integration: onboarding logs session
# ============================================================================


class TestOnboardingLog:
    def setup_method(self):
        self._tmp = Path(tempfile.mkdtemp())
        self._log_path = self._tmp / "onboarding_log.json"

    def teardown_method(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_log_session(self):
        with mock.patch("scripts.mg_onboard.REPO_ROOT", self._tmp):
            (self._tmp / "reports").mkdir(parents=True, exist_ok=True)
            _log_session("ml", "ML_BENCH-01", "ru", True, "test", "abc123")
            log_path = self._tmp / "reports" / "onboarding_log.json"
            assert log_path.exists()
            entries = json.loads(log_path.read_text(encoding="utf-8"))
            assert len(entries) == 1
            assert entries[0]["domain"] == "ml"
            assert entries[0]["language"] == "ru"
            assert entries[0]["verification_passed"] is True
