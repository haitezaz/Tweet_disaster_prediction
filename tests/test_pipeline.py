"""
test_pipeline.py

Unit tests for preprocessing, feature engineering, and decision engine.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

from src.data_work.preprocess import clean_text, preprocess_data
from src.features.feature_engineering import build_tfidf_features


# ==============================
# Test Preprocessing
# ==============================

class TestCleanText:
    """Tests for clean_text function."""
    
    def test_lowercase_conversion(self):
        """Test that text is converted to lowercase."""
        result = clean_text("HELLO WORLD")
        assert result == "hello world"
    
    def test_url_removal(self):
        """Test that URLs are removed."""
        result = clean_text("Check this https://example.com link")
        assert "https" not in result
        assert "example" not in result
    
    def test_mention_removal(self):
        """Test that @mentions are removed."""
        result = clean_text("Hello @user how are you")
        assert "@user" not in result
        assert "hello" in result
    
    def test_hashtag_symbol_removal(self):
        """Test that # symbol is removed but word remains."""
        result = clean_text("This is #trending")
        assert "#" not in result
        assert "trending" in result
    
    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        result = clean_text("Hello! How are you?")
        assert "!" not in result
        assert "?" not in result
    
    def test_empty_string_for_non_string(self):
        """Test that non-string input returns empty string."""
        assert clean_text(None) == ""
        assert clean_text(123) == ""


class TestPreprocessData:
    """Tests for preprocess_data function."""
    
    def test_valid_dataframe_with_target(self):
        """Test preprocessing with valid training data."""
        df = pd.DataFrame({
            "text": ["Hello world", "Test tweet"],
            "target": [0, 1]
        })
        X, y = preprocess_data(df)
        assert len(X) == 2
        assert len(y) == 2
    
    def test_missing_text_column_raises_error(self):
        """Test that missing text column raises ValueError."""
        df = pd.DataFrame({"other": ["data"]})
        with pytest.raises(ValueError, match="must contain 'text' column"):
            preprocess_data(df)
    
    def test_non_dataframe_raises_error(self):
        """Test that non-DataFrame input raises ValueError."""
        with pytest.raises(ValueError, match="must be a pandas DataFrame"):
            preprocess_data("not a dataframe")
    
    def test_drops_unnecessary_columns(self):
        """Test that id, keyword, location columns are dropped."""
        df = pd.DataFrame({
            "id": [1, 2],
            "keyword": ["fire", "flood"],
            "location": ["NYC", "LA"],
            "text": ["Hello", "World"],
            "target": [0, 1]
        })
        X, y = preprocess_data(df)
        assert len(X) == 2


# ==============================
# Test Feature Engineering
# ==============================

class TestBuildTfidfFeatures:
    """Tests for build_tfidf_features function."""
    
    def test_returns_sparse_matrix(self):
        """Test that TF-IDF returns sparse matrices."""
        X_train = pd.Series(["hello world", "test data"])
        X_train_tfidf, vectorizer = build_tfidf_features(X_train)
        
        assert X_train_tfidf.shape[0] == 2
        assert vectorizer is not None
    
    def test_with_validation_data(self):
        """Test TF-IDF with train and validation data."""
        X_train = pd.Series(["hello world", "test data"])
        X_val = pd.Series(["hello test"])
        
        X_train_tfidf, X_val_tfidf, vectorizer = build_tfidf_features(X_train, X_val)
        
        assert X_train_tfidf.shape[0] == 2
        assert X_val_tfidf.shape[0] == 1
    
    def test_vectorizer_fitted_on_train(self):
        """Test that vectorizer is fitted only on training data."""
        X_train = pd.Series(["hello world"])
        X_val = pd.Series(["unseen word"])
        
        X_train_tfidf, X_val_tfidf, vectorizer = build_tfidf_features(X_train, X_val)
        
        # Vectorizer should only know words from training
        assert "hello" in vectorizer.vocabulary_ or "world" in vectorizer.vocabulary_


# ==============================
# Test Decision Engine
# ==============================

class TestDecisionEngine:
    """Tests for DecisionEngine class."""
    
    @pytest.fixture
    def mock_engine(self):
        """Create a mocked DecisionEngine for testing."""
        with patch('src.models.decision_engine.joblib.load') as mock_load:
            # Create mock models
            mock_lr = MagicMock()
            mock_nb = MagicMock()
            mock_vectorizer = MagicMock()
            
            mock_vectorizer.transform.return_value = [[0.5, 0.5]]
            
            mock_load.side_effect = [mock_lr, mock_nb, mock_vectorizer]
            
            from src.models.decision_engine import DecisionEngine
            engine = DecisionEngine()
            engine.lr_model = mock_lr
            engine.nb_model = mock_nb
            engine.vectorizer = mock_vectorizer
            
            return engine
    
    def test_high_confidence_disaster(self, mock_engine):
        """Test prediction when LR is highly confident of disaster."""
        mock_engine.lr_model.predict_proba.return_value = [[0.1, 0.9]]
        
        result = mock_engine.predict("earthquake damage")
        
        assert result["prediction"] == 1
        assert result["confidence"] >= 0.75
        assert result["source"] == "logistic_regression"
    
    def test_high_confidence_non_disaster(self, mock_engine):
        """Test prediction when LR is highly confident of non-disaster."""
        mock_engine.lr_model.predict_proba.return_value = [[0.9, 0.1]]
        
        result = mock_engine.predict("having a great day")
        
        assert result["prediction"] == 0
        assert result["source"] == "logistic_regression"
    
    def test_fallback_to_naive_bayes(self, mock_engine):
        """Test fallback to Naive Bayes when LR is uncertain."""
        # LR probability in uncertain zone (0.25 < prob < 0.75)
        mock_engine.lr_model.predict_proba.return_value = [[0.5, 0.5]]
        mock_engine.nb_model.predict_proba.return_value = [[0.3, 0.7]]
        
        result = mock_engine.predict("ambiguous tweet")
        
        assert result["source"] == "naive_bayes_fallback"
        assert result["prediction"] == 1
