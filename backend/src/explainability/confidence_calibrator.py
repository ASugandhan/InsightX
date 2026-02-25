class ConfidenceCalibrator:
    def __init__(self):
        self.base_thresholds = {'high': 0.85, 'medium': 0.70, 'low': 0.50}
    
    def calibrate(self, raw_confidence, query_complexity, rag_boost, result_quality):
        confidence = raw_confidence + rag_boost
        # Complexity adjustments
        if query_complexity == 1:
            confidence += 0.05
        elif query_complexity == 3:
            confidence -= 0.05
        # Use additive quality bonus instead of multiplicative penalty
        # so large samples don't unfairly punish confidence
        if result_quality >= 1.0:
            confidence += 0.05
        elif result_quality >= 0.85:
            confidence += 0.0   # neutral
        elif result_quality >= 0.70:
            confidence -= 0.05  # small penalty
        else:
            confidence -= 0.15  # empty/tiny result penalty
        confidence = max(0.50, min(1.0, confidence))
        if confidence >= 0.85:
            label = "HIGH"
        elif confidence >= 0.70:
            label = "MEDIUM"
        else:
            label = "LOW"
        return confidence, label
    
    def assess_query_complexity(self, parsed_query):
        score = 1
        if len(parsed_query.filters) > 2:
            score += 1
        if len(parsed_query.dimensions) > 2:
            score += 1
        if len(parsed_query.metrics) > 2:
            score += 1
        return min(3, score)
    
    def assess_result_quality(self, result, sample_size):
        # Large samples are high quality
        if sample_size >= 10000:
            score = 1.0
        elif sample_size >= 1000:
            score = 0.95
        elif sample_size >= 100:
            score = 0.85
        elif sample_size >= 10:
            score = 0.70
        else:
            score = 0.50
        if result.empty:
            score = 0.30
        return score