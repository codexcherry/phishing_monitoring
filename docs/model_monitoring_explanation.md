# Model Monitoring and Drift Detection in Phishing Detection

## 1. Importance of Monitoring in Phishing Detection

Phishing attacks are highly dynamic. Attackers constantly evolve their techniques to bypass security filters. A machine learning model trained on phishing URLs from six months ago might be completely ineffective against today's campaigns.

**Why monitoring is critical:**
*   **Evolving Attack Patterns:** Attackers change URL structures, use new TLDs, or compromise different types of legitimate sites.
*   **Degradation of Performance:** Without monitoring, a model's accuracy (precision/recall) will silently degrade over time, allowing malicious emails/URLs to slip through.
*   **Business Impact:** False negatives lead to security breaches; false positives disrupt user productivity.

## 2. Types of Drift

### Data Drift (Covariate Shift)
This occurs when the distribution of the input data ($P(X)$) changes, but the relationship between inputs and the target variable ($P(Y|X)$) remains the same.

*   **Example:** A model was trained mostly on `.com` and `.net` phishing URLs. Suddenly, attackers start using `.xyz` or IP-address-based URLs heavily. The input features (TLD, URL length) have shifted.

### Concept Drift
This occurs when the relationship between the input data and the target variable ($P(Y|X)$) changes. What used to be benign might now be malicious, or vice versa.

*   **Example:** A specific URL pattern (e.g., `login-secure`) was previously a strong indicator of phishing. However, a legitimate service starts using a similar structure for valid login pages. The model now flags legitimate traffic as phishing (False Positive increase).

## 3. Strategies for Detection and Addressing Drift

### Detection Techniques

1.  **Statistical Tests (Unsupervised):**
    *   **Kolmogorov-Smirnov (KS) Test:** Compares the cumulative distribution functions (CDF) of a feature in the reference (training) data vs. the current production data. Good for continuous variables (e.g., URL length).
    *   **Chi-Square Test:** Used for categorical features (e.g., TLD, protocol).
    *   **Population Stability Index (PSI):** Measures how much a variable has shifted in distribution.

2.  **Model Performance Monitoring (Supervised):**
    *   If ground truth labels are available (e.g., from user reports or security analyst verification), monitor metrics like Accuracy, Precision, Recall, and F1-Score over time.
    *   **Delayed Labels:** In phishing, labels often come with a delay (after a user reports it).

### Addressing Drift

1.  **Retraining:**
    *   **Scheduled:** Retrain every week/month.
    *   **Trigger-based:** Retrain immediately when drift is detected.
2.  **Online Learning:** Update the model incrementally with new samples (complex to manage).
3.  **Ensemble Methods:** Use an ensemble of models trained on different time windows.
