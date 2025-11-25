import pandas as pd
import numpy as np
from scipy.stats import ks_2samp, chi2_contingency

class DriftDetector:
    def __init__(self, reference_data):
        """
        Args:
            reference_data (pd.DataFrame): The training data to compare against.
        """
        self.reference_data = reference_data
        self.p_value_threshold = 0.05

    def detect_drift(self, new_data):
        """
        Checks for drift between reference_data and new_data.
        Returns a dictionary with drift status for each feature.
        """
        report = {}
        drift_detected = False
        
        # Numerical features: Use Kolmogorov-Smirnov (KS) Test
        numerical_features = ['url_length', 'num_special_chars']
        for feature in numerical_features:
            ref_values = self.reference_data[feature]
            new_values = new_data[feature]
            
            # KS Test
            statistic, p_value = ks_2samp(ref_values, new_values)
            
            is_drift = p_value < self.p_value_threshold
            report[feature] = {
                'test': 'KS',
                'p_value': p_value,
                'drift_detected': is_drift
            }
            if is_drift:
                drift_detected = True

        # Categorical features: Use Chi-Square Test
        # Note: Chi-Square requires contingency tables.
        categorical_features = ['has_ip_address', 'https_token']
        for feature in categorical_features:
            # Create contingency table
            # We need to ensure all categories are present in both
            ref_counts = self.reference_data[feature].value_counts().sort_index()
            new_counts = new_data[feature].value_counts().sort_index()
            
            # Align indexes (handle missing categories in one batch)
            all_categories = sorted(list(set(ref_counts.index) | set(new_counts.index)))
            ref_freq = [ref_counts.get(cat, 0) for cat in all_categories]
            new_freq = [new_counts.get(cat, 0) for cat in all_categories]
            
            # Chi-square test requires frequencies, but we can't just pass raw counts if sample sizes differ significantly 
            # without normalization, but chi2_contingency expects count table.
            # We construct a table: [[ref_cat1, ref_cat2], [new_cat1, new_cat2]]
            contingency_table = [ref_freq, new_freq]
            
            # Remove columns with zero sum to avoid errors
            contingency_table = np.array(contingency_table)
            contingency_table = contingency_table[:, contingency_table.sum(axis=0) > 0]

            if contingency_table.shape[1] < 2:
                # Not enough categories to test
                p_value = 1.0
            else:
                chi2, p, dof, ex = chi2_contingency(contingency_table)
                p_value = p
            
            is_drift = p_value < self.p_value_threshold
            report[feature] = {
                'test': 'Chi-Square',
                'p_value': p_value,
                'drift_detected': is_drift
            }
            if is_drift:
                drift_detected = True
                
        return drift_detected, report
