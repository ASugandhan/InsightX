"""
Plain Language Translator
Converts statistical jargon into plain English
"""

class PlainLanguageTranslator:
    """Translate statistical terms to plain language"""
    
    def __init__(self):
        self.glossary = self._build_glossary()
        print("✓ Plain Language Translator initialized")
    
    def translate(self, text: str) -> str:
        """
        Translate statistical terms in text to plain language
        
        Args:
            text: Text containing statistical terms
        
        Returns:
            Text with terms explained
        """
        
        translated = text
        
        # Replace technical terms with plain language
        for term, explanation in self.glossary.items():
            if term.lower() in translated.lower():
                # Add explanation in parentheses
                translated = translated.replace(term, f"{term} ({explanation})")
        
        return translated
    
    def explain_term(self, term: str) -> str:
        """Get plain language explanation of a term"""
        
        term_lower = term.lower()
        
        for key, explanation in self.glossary.items():
            if key.lower() == term_lower:
                return explanation
        
        return f"No explanation available for '{term}'"
    
    def explain_statistic(self, stat_name: str, value: float, context: dict = None) -> str:
        """
        Explain a statistic in plain language with context
        
        Args:
            stat_name: Name of statistic (e.g., 'p-value', 'std_dev')
            value: Value of the statistic
            context: Optional context (mean, median, etc.)
        
        Returns:
            Plain language explanation
        """
        
        explanations = {
            'p-value': self._explain_p_value(value),
            'std_dev': self._explain_std_dev(value, context),
            'coefficient_of_variation': self._explain_cv(value),
            'skewness': self._explain_skewness(value),
            'correlation': self._explain_correlation(value),
            'confidence_interval': self._explain_confidence_interval(value, context),
        }
        
        return explanations.get(stat_name, f"{stat_name}: {value}")
    
    def _explain_p_value(self, p_value: float) -> str:
        """Explain p-value in plain language"""
        
        if p_value < 0.001:
            return f"p-value < 0.001 means: This difference is EXTREMELY unlikely to be due to chance (less than 0.1% probability). You can be very confident this is a real pattern."
        elif p_value < 0.01:
            return f"p-value = {p_value:.3f} means: This difference is very unlikely to be due to chance (less than 1% probability). Strong evidence of a real pattern."
        elif p_value < 0.05:
            return f"p-value = {p_value:.3f} means: This difference is unlikely to be due to chance (less than 5% probability). Statistically significant."
        else:
            return f"p-value = {p_value:.3f} means: This difference could easily be due to chance (more than 5% probability). Not statistically significant."
    
    def _explain_std_dev(self, std_dev: float, context: dict) -> str:
        """Explain standard deviation in plain language"""
        
        if not context or 'mean' not in context:
            return f"Standard deviation of {std_dev:.2f} indicates the typical spread of values"
        
        mean = context['mean']
        cv = std_dev / mean if mean != 0 else 0
        
        if cv < 0.15:
            return f"Standard deviation of ±{std_dev:.2f} means: Values are tightly clustered around the average ({mean:.2f}). Low variability."
        elif cv < 0.30:
            return f"Standard deviation of ±{std_dev:.2f} means: Values spread moderately around the average ({mean:.2f}). About 68% of values fall within ±{std_dev:.2f} of {mean:.2f}."
        else:
            return f"Standard deviation of ±{std_dev:.2f} means: Values vary widely around the average ({mean:.2f}). High variability - individual transactions differ substantially."
    
    def _explain_cv(self, cv: float) -> str:
        """Explain coefficient of variation"""
        
        if cv < 0.15:
            return f"CV of {cv:.1%} means: Very consistent values (low variability)"
        elif cv < 0.30:
            return f"CV of {cv:.1%} means: Moderate consistency (typical variability)"
        elif cv < 0.50:
            return f"CV of {cv:.1%} means: High variability (values differ substantially)"
        else:
            return f"CV of {cv:.1%} means: Extreme variability (values differ dramatically)"
    
    def _explain_skewness(self, skewness: float) -> str:
        """Explain skewness"""
        
        if abs(skewness) < 0.5:
            return f"Skewness of {skewness:.2f} means: Distribution is roughly symmetric (balanced)"
        elif skewness > 0.5:
            return f"Skewness of {skewness:.2f} means: Right-skewed distribution (a few very high values pull the average up)"
        else:
            return f"Skewness of {skewness:.2f} means: Left-skewed distribution (a few very low values pull the average down)"
    
    def _explain_correlation(self, corr: float) -> str:
        """Explain correlation coefficient"""
        
        direction = "positive" if corr > 0 else "negative"
        abs_corr = abs(corr)
        
        if abs_corr > 0.8:
            strength = "very strong"
        elif abs_corr > 0.6:
            strength = "strong"
        elif abs_corr > 0.4:
            strength = "moderate"
        elif abs_corr > 0.2:
            strength = "weak"
        else:
            strength = "very weak"
        
        return f"Correlation of {corr:.2f} means: {strength.title()} {direction} relationship. When one goes up, the other tends to {'go up' if corr > 0 else 'go down'} {strength}ly."
    
    def _explain_confidence_interval(self, ci_width: float, context: dict) -> str:
        """Explain confidence interval"""
        
        if not context or 'mean' not in context:
            return f"95% confidence interval width of {ci_width:.2f}"
        
        mean = context['mean']
        lower = mean - ci_width/2
        upper = mean + ci_width/2
        
        return f"95% confidence interval [{lower:.2f}, {upper:.2f}] means: We're 95% confident the true average falls within this range."
    
    def _build_glossary(self) -> dict:
        """Build glossary of statistical terms"""
        
        return {
            'mean': 'average value',
            'median': 'middle value when sorted',
            'mode': 'most common value',
            'standard deviation': 'typical spread around the average',
            'variance': 'measure of data spread (squared deviation)',
            'coefficient of variation': 'relative variability (std dev / mean)',
            'skewness': 'measure of asymmetry in distribution',
            'kurtosis': 'measure of tail heaviness',
            'correlation': 'how two variables move together',
            'p-value': 'probability this occurred by chance',
            'confidence interval': 'range where true value likely falls',
            't-test': 'test if two groups differ significantly',
            'chi-square': 'test if categories are related',
            'ANOVA': 'test if multiple groups differ',
            'regression': 'predict one variable from others',
            'outlier': 'unusual value far from others',
            'percentile': 'percentage of data below this value',
            'quartile': '25th, 50th, or 75th percentile',
            'IQR': 'interquartile range (middle 50% of data)',
            'null hypothesis': 'assumption of no difference/effect',
            'alternative hypothesis': 'assumption of difference/effect',
            'Type I error': 'false positive (saying difference exists when it doesn\'t)',
            'Type II error': 'false negative (missing a real difference)',
            'statistical significance': 'unlikely to occur by chance',
            'effect size': 'magnitude of difference',
            'sample size': 'number of observations',
            'population': 'entire group of interest',
            'sample': 'subset of population analyzed',
        }


# ============================================================================
# TESTING
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("PLAIN LANGUAGE TRANSLATOR TEST")
    print("="*80)
    
    translator = PlainLanguageTranslator()
    
    # Test 1: Translate technical text
    print("\n--- Test 1: Translate Technical Text ---")
    technical = "The standard deviation is ±1234 with a p-value < 0.001, indicating statistical significance."
    plain = translator.translate(technical)
    print(f"Technical: {technical}")
    print(f"\nPlain: {plain}")
    
    # Test 2: Explain specific statistics
    print("\n\n--- Test 2: Explain Statistics ---")
    
    print("\n1. P-value:")
    print(translator.explain_statistic('p-value', 0.003))
    
    print("\n2. Standard Deviation:")
    print(translator.explain_statistic('std_dev', 1234, {'mean': 2847}))
    
    print("\n3. Correlation:")
    print(translator.explain_statistic('correlation', 0.75))
    
    print("\n\n--- Test 3: Term Lookup ---")
    terms = ['skewness', 'outlier', 'confidence interval']
    for term in terms:
        print(f"\n{term}: {translator.explain_term(term)}")
    
    print("\n" + "="*80)
    print("✓ PLAIN LANGUAGE TRANSLATOR TEST COMPLETE")
    print("="*80)