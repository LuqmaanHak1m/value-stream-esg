import os
from flask import Flask, render_template, jsonify
import pandas as pd
import json

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')

def load_esg_data():
    """Load ESG scores from CSV"""
    try:
        df = pd.read_csv('esg_scores.csv')
        return df
    except Exception as e:
        print(f"Error loading ESG data: {e}")
        return pd.DataFrame()

def calculate_category_scores(df, company):
    """Calculate average scores by category for a company"""
    company_data = df[df['company'] == company]
    
    categories = {}
    for category in ['Environmental', 'Social', 'Governance']:
        cat_data = company_data[company_data['category'] == category]
        if not cat_data.empty:
            categories[category] = {
                'score': round(cat_data['score'].mean(), 2),
                'metrics': cat_data[['metric', 'score']].to_dict('records')
            }
    
    return categories

@app.route('/')
def index():
    """Main dashboard page"""
    df = load_esg_data()
    companies = df['company'].unique().tolist() if not df.empty else []
    return render_template('index.html', companies=companies)

@app.route('/api/company/<company_name>')
def get_company_data(company_name):
    """API endpoint to get company ESG data"""
    df = load_esg_data()
    
    if df.empty:
        return jsonify({'error': 'No data available'}), 404
    
    if company_name not in df['company'].values:
        return jsonify({'error': 'Company not found'}), 404
    
    categories = calculate_category_scores(df, company_name)
    
    # Placeholder for LLM-adjusted scores and news articles
    # This will be populated when you integrate the LLM analysis
    
    return jsonify({
        'company': company_name,
        'original_scores': categories,
        'adjusted_scores': {},  # To be populated with LLM results
        'news_articles': []  # To be populated with scraped news
    })

@app.route('/health')
def health():
    """Health check endpoint for cloud hosting"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=(os.environ.get('FLASK_ENV') == 'development'))
