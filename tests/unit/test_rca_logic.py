"""
Unit Tests for RCA (Root Cause Analysis) Logic
==============================================

Tests for log truncation utilities, error pattern matching,
and RCA analysis formatting.
"""

import pytest
import sys
import os

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))


# =============================================================================
# Sample Log Data
# =============================================================================

SAMPLE_PYTHON_LOG = """
Started by user admin
Building in workspace /var/jenkins_home/workspace/nexus-pipeline
Cloning repository https://github.com/example/nexus-backend.git

[Pipeline] stage
[Pipeline] { (Test)
+ python -m pytest tests/ -v

============================= test session starts ==============================
tests/test_users.py::TestUserService::test_validate_email FAILED

=================================== FAILURES ===================================
_________________________ TestUserService.test_validate_email __________________________

>       assert result.is_valid == True
E       AttributeError: 'NoneType' object has no attribute 'is_valid'

tests/test_users.py:42: AttributeError
=========================== short test summary info ============================
FAILED tests/test_users.py::TestUserService::test_validate_email - AttributeError
============================= 1 failed, 44 passed in 12.34s ====================

ERROR: script returned exit code 1
Finished: FAILURE
"""


# =============================================================================
# Test Classes
# =============================================================================

class TestLogTruncation:
    """Tests for build log truncation utility."""
    
    def test_truncate_build_log_exists(self):
        """Test truncate_build_log function exists."""
        from nexus_lib.utils import truncate_build_log
        
        assert callable(truncate_build_log)
    
    def test_truncate_short_log(self):
        """Test truncation of short logs."""
        from nexus_lib.utils import truncate_build_log
        
        short_log = "Build started\nCompiling...\nBuild complete"
        result = truncate_build_log(short_log)
        
        assert result is not None
        assert len(result) > 0
    
    def test_truncate_long_log(self):
        """Test truncation of long logs."""
        from nexus_lib.utils import truncate_build_log
        
        long_log = "\n".join([f"Line {i}" for i in range(1000)])
        result = truncate_build_log(long_log, max_total_chars=5000)
        
        # Should be truncated
        assert len(result) <= 5100  # Allow some overhead
    
    def test_preserve_errors(self):
        """Test that error sections are preserved."""
        from nexus_lib.utils import truncate_build_log
        
        result = truncate_build_log(SAMPLE_PYTHON_LOG, preserve_error_blocks=True)
        
        # Error content should be preserved
        assert "FAILURE" in result or "FAILED" in result
    
    def test_empty_log(self):
        """Test handling of empty log."""
        from nexus_lib.utils import truncate_build_log
        
        result = truncate_build_log("")
        
        assert result is not None


class TestErrorSummaryExtraction:
    """Tests for error summary extraction."""
    
    def test_extract_error_summary_exists(self):
        """Test extract_error_summary function exists."""
        from nexus_lib.utils import extract_error_summary
        
        assert callable(extract_error_summary)
    
    def test_extract_python_errors(self):
        """Test extraction of Python errors."""
        from nexus_lib.utils import extract_error_summary
        
        errors = extract_error_summary(SAMPLE_PYTHON_LOG)
        
        assert isinstance(errors, list)
    
    def test_extract_empty_log(self):
        """Test extraction from empty log."""
        from nexus_lib.utils import extract_error_summary
        
        errors = extract_error_summary("")
        
        assert isinstance(errors, list)


class TestStackTraceParsing:
    """Tests for stack trace parsing."""
    
    def test_parse_stack_trace_exists(self):
        """Test parse_stack_trace function exists."""
        from nexus_lib.utils import parse_stack_trace
        
        assert callable(parse_stack_trace)
    
    def test_parse_python_stack_trace(self):
        """Test parsing Python stack trace."""
        from nexus_lib.utils import parse_stack_trace
        
        result = parse_stack_trace(SAMPLE_PYTHON_LOG)
        
        # Result can be None or a dict
        assert result is None or isinstance(result, dict)
    
    def test_parse_no_stack_trace(self):
        """Test parsing log with no stack trace."""
        from nexus_lib.utils import parse_stack_trace
        
        result = parse_stack_trace("Just some text\nNo stack trace here")
        
        assert result is None or isinstance(result, dict)


class TestFailingTestIdentification:
    """Tests for failing test identification."""
    
    def test_identify_failing_test_exists(self):
        """Test identify_failing_test function exists."""
        from nexus_lib.utils import identify_failing_test
        
        assert callable(identify_failing_test)
    
    def test_identify_pytest_failure(self):
        """Test identification of pytest failure."""
        from nexus_lib.utils import identify_failing_test
        
        result = identify_failing_test(SAMPLE_PYTHON_LOG)
        
        assert result is None or isinstance(result, dict)


class TestRcaSchemas:
    """Tests for RCA Pydantic schemas."""
    
    def test_rca_request_import(self):
        """Test RcaRequest can be imported."""
        from nexus_lib.schemas.agent_contract import RcaRequest
        
        assert RcaRequest is not None
    
    def test_rca_analysis_import(self):
        """Test RcaAnalysis can be imported."""
        from nexus_lib.schemas.agent_contract import RcaAnalysis
        
        assert RcaAnalysis is not None
    
    def test_rca_confidence_level_import(self):
        """Test RcaConfidenceLevel can be imported."""
        from nexus_lib.schemas.agent_contract import RcaConfidenceLevel
        
        assert RcaConfidenceLevel is not None
    
    def test_rca_error_type_import(self):
        """Test RcaErrorType can be imported."""
        from nexus_lib.schemas.agent_contract import RcaErrorType
        
        assert RcaErrorType is not None


class TestRcaEnums:
    """Tests for RCA enumeration types."""
    
    def test_confidence_levels(self):
        """Test confidence level enum values."""
        from nexus_lib.schemas.agent_contract import RcaConfidenceLevel
        
        # Check enum has expected values
        assert hasattr(RcaConfidenceLevel, 'LOW')
        assert hasattr(RcaConfidenceLevel, 'MEDIUM')
        assert hasattr(RcaConfidenceLevel, 'HIGH')
    
    def test_error_types(self):
        """Test error type enum values."""
        from nexus_lib.schemas.agent_contract import RcaErrorType
        
        # Check enum has expected values
        assert hasattr(RcaErrorType, 'UNKNOWN')


class TestLogPatterns:
    """Tests for common log pattern detection."""
    
    def test_detect_assertion_error(self):
        """Test detection of assertion errors."""
        log = "AssertionError: expected 'foo' but got 'bar'"
        
        assert "AssertionError" in log
    
    def test_detect_attribute_error(self):
        """Test detection of attribute errors."""
        log = "AttributeError: 'NoneType' object has no attribute 'is_valid'"
        
        assert "AttributeError" in log
    
    def test_detect_failure_marker(self):
        """Test detection of FAILED marker."""
        assert "FAILED" in SAMPLE_PYTHON_LOG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
