# Red Wine Quality Analysis

## Overview

This project analyzes the **Red Wine Quality dataset** using Python, Pandas, statistics, and data visualization.
The goal is to understand how the physicochemical properties of red wine relate to its quality score.

The main research question is:

> **Which chemical properties are most related to wine quality?**

This project is part of my data learning path, moving from **statistics** to **Python/Pandas**, then toward **data visualization**, **SQL**, and later **machine learning**.

---

## Dataset

The dataset used in this project is the **Red Wine Quality dataset** from the UCI Machine Learning Repository.

* Dataset source: [UCI Wine Quality Dataset](https://archive.ics.uci.edu/dataset/186/wine%2Bquality)
* Direct CSV file: [winequality-red.csv](https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv)

The dataset contains physicochemical measurements of red wine samples, along with a quality score.

### Features

The dataset includes the following variables:

* Fixed acidity
* Volatile acidity
* Citric acid
* Residual sugar
* Chlorides
* Free sulfur dioxide
* Total sulfur dioxide
* Density
* pH
* Sulphates
* Alcohol
* Quality

The target variable is:

```text
quality
```

---

## Project Objectives

The main objectives of this project are to:

1. Load and inspect the red wine quality dataset.
2. Clean and prepare the data for analysis.
3. Explore the distribution of wine quality scores.
4. Analyze the relationship between chemical properties and wine quality.
5. Use visualizations to identify patterns and trends.
6. Compare low-quality and high-quality wines.
7. Apply basic statistical reasoning to support conclusions.
8. Prepare the project for a future machine learning extension.

---

## Project Structure

```text
red-wine-quality-analysis/
│
├── data/
│   ├── raw/
│   │   └── winequality-red.csv
│   └── processed/
│
├── notebooks/
│   └── wine_quality_statistics_project.ipynb
│
├── reports/
│   └── figures/
│
├── src/
│
├── README.md
```

---

## Tools and Libraries

This project uses:

* Python
* Pandas
* NumPy
* Matplotlib
* Seaborn
* SciPy
* Jupyter Notebook

---

## Analysis Plan

### 1. Data Loading

The dataset is loaded using Pandas.

```python
import pandas as pd

url = "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"

df = pd.read_csv(url, sep=";")
df.head()
```

The dataset uses a semicolon separator, so `sep=";"` is required.

---

### 2. Data Cleaning

The cleaning step includes:

* Checking the shape of the dataset
* Checking column names
* Looking for missing values
* Looking for duplicated rows
* Cleaning column names for easier use in Python

Example:

```python
df.columns = df.columns.str.lower().str.replace(" ", "_")
```

---

### 3. Exploratory Data Analysis

The exploratory analysis focuses on understanding the data before applying any advanced techniques.

Main questions:

* What is the distribution of wine quality scores?
* Are most wines low, medium, or high quality?
* Which variables have the highest and lowest values?
* Are there unusual values or outliers?

Visualizations include:

* Quality score count plot
* Histograms of chemical properties
* Boxplots by quality group
* Correlation heatmap

---

### 4. Correlation Analysis

Correlation analysis is used to identify which variables are most related to wine quality.

The main focus is on variables such as:

* Alcohol
* Volatile acidity
* Sulphates
* Citric acid
* Density
* Chlorides

The goal is not only to calculate correlations, but also to interpret them correctly.

Example questions:

* Does higher alcohol content tend to be associated with higher wine quality?
* Does higher volatile acidity tend to be associated with lower wine quality?
* Which features show weak or strong relationships with quality?

---

### 5. Low vs High Quality Comparison

To make the analysis more interpretable, wines can be grouped into categories such as:

```text
Low quality: quality <= 5
High quality: quality >= 6
```

Then the average values of chemical properties can be compared between the two groups.

This helps answer questions like:

* Do higher-quality wines have more alcohol?
* Do lower-quality wines have more volatile acidity?
* Are sulphates higher in better-rated wines?

---

### 6. Statistical Testing

Basic statistical tests can be used to support the analysis.

Possible tests:

* T-test comparing alcohol levels between low-quality and high-quality wines
* T-test comparing volatile acidity between low-quality and high-quality wines
* Correlation significance tests

The purpose is to connect the project to core statistical reasoning, not just visual exploration.

---

### 7. Regression Analysis

A simple regression analysis can be added to study how selected features relate to wine quality.

Possible models:

* Simple linear regression using alcohol as one predictor
* Multiple linear regression using several physicochemical variables

The objective is to understand prediction and interpretation before moving into machine learning.

---

## Possible Future Machine Learning Extension

This project can later be extended into a machine learning project.

Possible ML tasks:

### Classification

Convert quality into classes:

```text
Low quality
Medium quality
High quality
```

Then train models such as:

* Logistic Regression
* Decision Tree
* Random Forest
* K-Nearest Neighbors

### Regression

Use the physicochemical features to predict the numerical quality score.

Possible models:

* Linear Regression
* Random Forest Regressor
* Gradient Boosting Regressor

---

## Expected Insights

This project aims to identify the most important chemical indicators of red wine quality.

Expected areas of focus include:

* Whether alcohol content is positively related to quality
* Whether volatile acidity is negatively related to quality
* Whether sulphates have a noticeable relationship with quality
* Whether some chemical properties have weak or no clear relationship with quality

Final conclusions will be based on data exploration, visualizations, correlations, and statistical testing.

---

## How to Run the Project

### 1. Clone the repository

```bash
git clone https://github.com/karimchaal911-web/PROJECTS.git
cd PROJECTS
```

### 2. Navigate to the project folder

```bash
cd "WINE QUALITY ANALYSIS"
```

### 3. Install required libraries

```bash
pip install -r requirements.txt
```

If there is no `requirements.txt` file yet, install the main libraries manually:

```bash
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter
```

### 4. Open Jupyter Notebook

```bash
jupyter notebook
```

Then open:

```text
notebooks/wine_quality_statistics_project.ipynb
```

---

## Skills Practiced

This project helps practice:

* Data loading with Pandas
* Data cleaning
* Exploratory Data Analysis
* Descriptive statistics
* Data visualization
* Correlation analysis
* Statistical testing
* Regression basics
* Project organization for GitHub
* Writing clear data-analysis conclusions

---

## Current Status

This project is currently focused on **data analysis and statistical interpretation**.

Machine learning can be added later after completing the exploratory and statistical analysis properly.

---

## Author

**Karim Chaal**

This project is part of my personal data, statistics, and machine learning portfolio.
