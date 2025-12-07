# Backend Test Results

Last Updated: December 2, 2025

## Latest Test Run Summary

### ML Combined Training + Pipeline Tests (30 tests)

**Command:**
```bash
python3 -m pytest tests/test_pipeline.py tests/test_ml_combined_training.py -v
```

**Result:** ✅ **30/30 passed** (100% pass rate)

**Duration:** ~73 seconds

---

## Individual Test Suite Results

### test_pipeline.py (16 tests)
| Test | Status |
|------|--------|
| TestPipelineEndpoints::test_get_status_endpoint | ✅ PASSED |
| TestPipelineEndpoints::test_get_pending_changes_endpoint | ✅ PASSED |
| TestPipelineEndpoints::test_get_history_endpoint | ✅ PASSED |
| TestPipelineEndpoints::test_get_history_with_limit | ✅ PASSED |
| TestPipelineEndpoints::test_get_last_run_endpoint | ✅ PASSED |
| TestPipelineEndpoints::test_trigger_pipeline_no_changes | ✅ PASSED |
| TestPipelineEndpoints::test_trigger_pipeline_with_force | ✅ PASSED |
| TestPipelineEndpoints::test_clear_changes_endpoint | ✅ PASSED |
| TestChatbotCompatibility::test_chatbot_still_works | ✅ PASSED |
| TestChatbotCompatibility::test_analytics_still_works | ✅ PASSED |
| TestChatbotCompatibility::test_ml_forecast_endpoint_available | ✅ PASSED |
| TestPipelineIntegration::test_pipeline_status_structure | ✅ PASSED |
| TestPipelineIntegration::test_pipeline_history_structure | ✅ PASSED |
| TestPipelineIntegration::test_pipeline_endpoints_dont_break_health | ✅ PASSED |
| TestConcurrentAccess::test_analytics_during_pipeline_status_check | ✅ PASSED |
| TestConcurrentAccess::test_chatbot_during_pipeline_operations | ✅ PASSED |

**Result:** ✅ 16/16 passed

---

### test_ml_combined_training.py (14 tests)
| Test | Status |
|------|--------|
| TestMLTrainEndpoint::test_train_endpoint_exists | ✅ PASSED |
| TestMLTrainEndpoint::test_train_response_structure | ✅ PASSED |
| TestMLTrainEndpoint::test_train_message_mentions_combined_data | ✅ PASSED |
| TestMLForecastEndpoint::test_forecast_30d_standard | ✅ PASSED |
| TestMLForecastEndpoint::test_forecast_60d_contracted | ✅ PASSED |
| TestMLForecastEndpoint::test_forecast_90d_custom | ✅ PASSED |
| TestPipelineRetraining::test_pipeline_status_available | ✅ PASSED |
| TestPipelineRetraining::test_pipeline_can_trigger_with_force | ✅ PASSED |
| TestDataStandardization::test_analytics_metrics_include_competitor_data | ✅ PASSED |
| TestDataStandardization::test_health_check_still_works | ✅ PASSED |
| TestMLTrainingMetadata::test_training_stores_data_sources | ✅ PASSED |
| TestRegressorIntegration::test_forecast_uses_hwco_patterns | ✅ PASSED |
| TestErrorHandling::test_invalid_pricing_model_handled | ✅ PASSED |
| TestErrorHandling::test_missing_pricing_model_handled | ✅ PASSED |

**Result:** ✅ 14/14 passed

---

## Feature Coverage

### ML Combined Training Feature
The Prophet ML model now trains on **combined HWCO + competitor data** for improved forecast accuracy.

**Verified Functionality:**
- ✅ Training loads data from both `historical_rides` and `competitor_prices` collections
- ✅ Data is standardized using `_standardize_record_for_training()`
- ✅ `Rideshare_Company` regressor added (HWCO vs COMPETITOR)
- ✅ Training response includes `data_sources` breakdown
- ✅ Forecasts use `company_HWCO=1` for HWCO-specific predictions
- ✅ Pipeline triggers retraining when historical/competitor data changes

### Agent Pipeline Feature
The agent pipeline runs Forecasting, Analysis, Recommendation, and What-If agents in sequence.

**Verified Functionality:**
- ✅ ChangeTracker monitors MongoDB changes
- ✅ Pipeline API endpoints (trigger, status, history, changes)
- ✅ Chatbot continues working during pipeline operations
- ✅ No blocking of analytics or ML endpoints
- ✅ Pipeline can be force-triggered manually

---

## Test Environment

- **Python:** 3.12.7
- **Pytest:** 7.4.3
- **Server:** localhost:8000
- **Database:** MongoDB (configured via .env)
- **Model:** Prophet ML with combined training

---

## How to Run Tests

```bash
# Ensure server is running
cd backend
uvicorn app.main:app --reload

# In another terminal, run tests
cd backend
source ../venv/bin/activate

# Run all pipeline + ML tests
python3 -m pytest tests/test_pipeline.py tests/test_ml_combined_training.py -v

# Run individual suites
python3 -m pytest tests/test_pipeline.py -v
python3 -m pytest tests/test_ml_combined_training.py -v
```


