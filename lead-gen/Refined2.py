from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

import requests
import json
import os
from groq import Groq
from typing import Dict, List, Optional
import statistics
import pydantic
from pydantic import BaseModel
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import json
import os
from groq import Groq
from typing import Dict, List, Optional
import statistics
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

# Must be the first Streamlit command
st.set_page_config(
    page_title="AI agents assessment",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


class TaskBreakdown(BaseModel):
    step: str
    percentage: float

class TimeAnalysis(BaseModel):
    hours_per_task: float
    times_per_month: int
    hours_per_year_before: float
    hours_per_year_after: float
    hours_saved_per_year: float

class CostProjections(BaseModel):
    average_annual_salary: float
    hourly_rate: float
    monthly_task_cost: float
    annual_task_cost: float

class ROIAnalysis(BaseModel):
    percentage: float
    calculation_basis: str

class AutomationObject(BaseModel):
    # Job and Company Info
    job_title: str
    location: str
    company_activity: str
    
    # Task Details
    task_description: str
    
    # Salary Data
    found_salary_data: List[float]
    
    # Task Breakdown
    task_steps: List[TaskBreakdown]
    
    # Time Analysis
    time_analysis: TimeAnalysis
    
    # Cost Projections
    cost_projections: CostProjections
    
    # ROI Analysis
    roi_analysis: ROIAnalysis

def fetch_salary_data(query: str, location: str) -> Dict:
    """
    Fetch salary data from Google Search API using Serper
    """
    url = "https://google.serper.dev/search"
    formatted_query = f"salary {query} {location}"
    
    payload = json.dumps({
        "q": formatted_query,
        "location": location,
        "type": "search",
        "engine": "google",
        "gl": "us"
    })
    
    headers = {
        'X-API-KEY': os.getenv('SERPER_API_KEY'),
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def extract_salary_info(search_results: Dict) -> List[str]:
    """
    Extract the first 8 snippet results from the search data
    """
    if not search_results or 'organic' not in search_results:
        return []
        
    snippets = []
    for result in search_results.get('organic', [])[:8]:
        snippets.append(result.get('snippet', ''))
    return snippets

def analyze_salaries_with_llm(snippets: List[str]) -> List[float]:
    """
    Use Groq with LLaMA to analyze salary snippets and extract average total pay
    Returns the list of found salaries instead of just the median
    """
    if not snippets:
        return []
        
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    prompt = f"""
    You are a precise salary data analyst. Analyze these salary snippets and extract total annual compensation in USD. Follow these steps exactly:

    1. First, identify if the salary is monthly or annual
       - If monthly, multiply by 12 to get annual
       - If hourly, multiply by 2080 (40 hours * 52 weeks) to get annual
       
    2. Then, handle currency conversion to USD using these exact rates:
       AED to USD: multiply by 0.2723
       GBP to USD: multiply by 1.29
       EUR to USD: multiply by 1.09
       CHF to USD: multiply by 1.16
       CAD to USD: multiply by 0.73
       AUD to USD: multiply by 0.66
       CNY to USD: multiply by 0.14
       HKD to USD: multiply by 0.13
       
    3. Return ONLY the final annual USD amount as a whole number (no decimals)
       - Format: one number per line
       - No text, just the number
       - No currency symbols
       - No commas
       - No trailing zeros
       
    Examples of correct processing:

    Input: "Monthly salary AED 10000"
    Steps:
    1. Convert to annual: 10000 * 12 = 120000 AED
    2. Convert to USD: 120000 * 0.2723 = 32676 USD
    Output: 32676

    Input: "Annual salary £50000"
    Steps:
    1. Already annual, no conversion needed
    2. Convert to USD: 50000 * 1.29 = 64500 USD
    Output: 64500

    Here are the snippets to analyze:
    {json.dumps(snippets, indent=2)}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-70b-8192",
            temperature=0.1,  # Reduced temperature for more consistent outputs
        )
        
        # Get the response and split it into lines
        response_lines = chat_completion.choices[0].message.content.strip().split('\n')
        
        # Convert each line to a float, removing any non-numeric characters
        salaries = []
        for line in response_lines:
            try:
                # Clean the string and convert to float
                cleaned_value = ''.join(c for c in line if c.isdigit() or c == '.')
                if cleaned_value:
                    value = float(cleaned_value)
                    if value > 5000:  # Basic sanity check for annual salary
                        salaries.append(value)
            except ValueError:
                continue
        
        # Remove outliers (values more than 2 standard deviations from mean)
        if len(salaries) > 2:
            mean = statistics.mean(salaries)
            stdev = statistics.stdev(salaries)
            salaries = [s for s in salaries if abs(s - mean) <= 2 * stdev]
        
        # Return the list of salaries
        if salaries:
            print(f"Found valid total compensation figures: {salaries}")
            return salaries
        return []
        
    except Exception as e:
        print(f"Error processing LLM response: {e}")
        return []

def calculate_task_costs(annual_salary: float, hours_per_task: float, times_per_month: int) -> CostProjections:
    """
    Calculate various cost metrics based on salary and task parameters
    """
    # Calculate hourly rate (annual salary divided by 2080 work hours per year)
    hourly_rate = annual_salary / 2080
    
    # Calculate monthly task hours
    monthly_task_hours = hours_per_task * times_per_month
    
    # Calculate monthly cost for this task
    monthly_task_cost = hourly_rate * monthly_task_hours
    
    # Calculate annual cost for this task
    annual_task_cost = monthly_task_cost * 12
    
    return CostProjections(
        average_annual_salary=annual_salary,
        hourly_rate=hourly_rate,
        monthly_task_cost=monthly_task_cost,
        annual_task_cost=annual_task_cost
    )

def get_user_inputs() -> Dict[str, any]:
    """
    Get all necessary inputs from the user including company and task details
    """
    print("\n=== Job Search Parameters ===")
    job_query = input("Enter job title to search (e.g., 'senior procurement manager'): ")
    location = input("Enter location (e.g., 'New York'): ")
    
    print("\n=== Company Information ===")
    company_activity = input("What is your company's main business activity? Please be specific: ")
    
    print("\n=== Task Details ===")
    task_description = input("Please describe the specific task that needs automation (be detailed): ")
    
    print("\n=== Task Parameters ===")
    while True:
        try:
            hours_per_task = float(input("How many hours does the employee work on this task (per occurrence)? "))
            if hours_per_task <= 0:
                print("Hours must be greater than 0")
                continue
            break
        except ValueError:
            print("Please enter a valid number")
    
    while True:
        try:
            times_per_month = int(input("How many times per month is this task performed? "))
            if times_per_month <= 0:
                print("Frequency must be greater than 0")
                continue
            break
        except ValueError:
            print("Please enter a valid number")
    
    return {
        "job_query": job_query,
        "location": location,
        "company_activity": company_activity,
        "task_description": task_description,
        "hours_per_task": hours_per_task,
        "times_per_month": times_per_month
    }

def analyze_automation_potential(inputs: Dict[str, any], annual_salary: float) -> AutomationObject:
    """
    Use LLM to analyze automation potential and generate recommendations
    Returns structured AutomationObject
    """
    hours_per_year_before = inputs['hours_per_task'] * inputs['times_per_month'] * 12
    hours_per_year_after = hours_per_year_before * 0.2  # Assuming 80% automation
    hours_saved_per_year = hours_per_year_before - hours_per_year_after
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    prompt = f"""
    You are a business automation expert. Analyze this task and break it down into its component steps.
    
    BUSINESS CONTEXT:
    Role: {inputs['job_query']}
    Company Activity: {inputs['company_activity']}
    Task Description: {inputs['task_description']}
    Time Investment: {inputs['hours_per_task']} hours/task, {inputs['times_per_month']} times/month
    Annual Cost: ${annual_salary:,.2f}

    Analyze the task and provide EXACTLY this output format with no additional text:

    TASK_STEPS:
    Step 1: [specific step name] | [number]%
    Step 2: [specific step name] | [number]%
    Step 3: [specific step name] | [number]%
    (Add more steps if needed, percentages must sum to 100%)

    TIME_ANALYSIS:
    Hours per year before automation: [number]
    Hours per year after automation: [number]
    Hours saved per year: [number]

    ROI_ANALYSIS:
    ROI percentage: [number]
    Calculation basis: [brief explanation]
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-70b-8192",
            temperature=0.7,
        )
        
        # Get the raw response
        raw_response = chat_completion.choices[0].message.content.strip()
        
        # Debug print
        print("Raw LLM Response:")
        print(raw_response)
        
        # Parse the response manually
        sections = raw_response.split('\n\n')
        
        # Parse task steps more robustly
        task_steps = []
        task_section = next((section for section in sections if 'TASK_STEPS:' in section), '')
        step_lines = [line.strip() for line in task_section.split('\n')[1:] if line.strip() and '|' in line]
        
        for line in step_lines:
            try:
                # Split on the last occurrence of '|' to handle cases where step name might contain '|'
                name_part, percentage_part = line.rsplit('|', 1)
                
                # Clean up the step name
                name = name_part.split(':', 1)[-1].strip() if ':' in name_part else name_part.strip()
                
                # Extract and clean up the percentage
                percentage_str = ''.join(c for c in percentage_part if c.isdigit() or c == '.')
                if percentage_str:
                    percentage = float(percentage_str)
                    task_steps.append({"step": name, "percentage": percentage})
            except Exception as e:
                print(f"Error parsing step line '{line}': {str(e)}")
                continue
        
        # Validate we got some task steps
        if not task_steps:
            raise ValueError("No valid task steps found in LLM response")
            
        # Normalize percentages to sum to 100
        total_percentage = sum(step["percentage"] for step in task_steps)
        if total_percentage != 100:
            print(f"Normalizing task percentages from {total_percentage}% to 100%")
            for step in task_steps:
                step["percentage"] = (step["percentage"] / total_percentage) * 100
        
        # Parse time analysis
        time_section = next((section for section in sections if 'TIME_ANALYSIS:' in section), '')
        time_lines = [line.strip() for line in time_section.split('\n')[1:] if ':' in line]
        
        # time_analysis = {
        #     "hours_per_task": inputs['hours_per_task'],
        #     "times_per_month": inputs['times_per_month'],
        #     "hours_per_year_before": float(''.join(c for c in time_lines[0].split(':')[1] if c.isdigit() or c == '.')),
        #     "hours_per_year_after": float(''.join(c for c in time_lines[1].split(':')[1] if c.isdigit() or c == '.')),
        #     "hours_saved_per_year": float(''.join(c for c in time_lines[2].split(':')[1] if c.isdigit() or c == '.'))
        # }

        time_analysis = TimeAnalysis(
            hours_per_task=inputs['hours_per_task'],
            times_per_month=inputs['times_per_month'],
            hours_per_year_before=hours_per_year_before,
            hours_per_year_after=hours_per_year_after,
            hours_saved_per_year=hours_saved_per_year
        )
        
        # Parse ROI analysis
        roi_section = next((section for section in sections if 'ROI_ANALYSIS:' in section), '')
        roi_lines = [line.strip() for line in roi_section.split('\n')[1:] if ':' in line]
        
        roi_analysis = {
            "percentage": float(''.join(c for c in roi_lines[0].split(':')[1] if c.isdigit() or c == '.')),
            "calculation_basis": roi_lines[1].split(':', 1)[1].strip()
        }
        
        # Calculate cost projections
        cost_projections = calculate_task_costs(
            annual_salary,
            inputs['hours_per_task'],
            inputs['times_per_month']
        )
        
        # Create the complete AutomationObject
        automation_object = AutomationObject(
            job_title=inputs['job_query'],
            location=inputs['location'],
            company_activity=inputs['company_activity'],
            task_description=inputs['task_description'],
            found_salary_data=[annual_salary],
            task_steps=[TaskBreakdown(**step) for step in task_steps],
            time_analysis=TimeAnalysis(**time_analysis),
            cost_projections=cost_projections,
            roi_analysis=ROIAnalysis(**roi_analysis)
        )
        
        return automation_object
        
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        # Make a separate call just for task breakdown
        try:
            task_prompt = f"""
            Break down this task into 3-5 component steps:
            {inputs['task_description']}
            
            Respond EXACTLY in this format with no additional text:
            Step 1: [step name] | [number]%
            Step 2: [step name] | [number]%
            Step 3: [step name] | [number]%
            (Percentages must sum to 100%)
            """
            
            task_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": task_prompt}],
                model="llama3-70b-8192",
                temperature=0.3
            )
            
            # Parse the task steps
            task_steps = []
            response_lines = task_completion.choices[0].message.content.strip().split('\n')
            
            for line in response_lines:
                if '|' in line:
                    name_part, percentage_part = line.rsplit('|', 1)
                    name = name_part.split(':', 1)[-1].strip()
                    percentage_str = ''.join(c for c in percentage_part if c.isdigit() or c == '.')
                    if percentage_str:
                        percentage = float(percentage_str)
                        task_steps.append({"step": name, "percentage": percentage})
        
        except Exception as e:
            print(f"Error in fallback task analysis: {str(e)}")
            # If even that fails, use generic steps
            task_steps = [
                {"step": "Initial Processing", "percentage": 30.0},
                {"step": "Main Task Execution", "percentage": 40.0},
                {"step": "Review and Finalization", "percentage": 30.0}
            ]
        
        # Create default time analysis
        time_analysis = TimeAnalysis(
            hours_per_task=inputs['hours_per_task'],
            times_per_month=inputs['times_per_month'],
            hours_per_year_before=inputs['hours_per_task'] * inputs['times_per_month'] * 12,
            hours_per_year_after=inputs['hours_per_task'] * inputs['times_per_month'] * 12,
            hours_saved_per_year=inputs['hours_per_task'] * inputs['times_per_month'] * 12
        )
        
        cost_projections = calculate_task_costs(
            annual_salary,
            inputs['hours_per_task'],
            inputs['times_per_month']
        )
        
        return AutomationObject(
            job_title=inputs['job_query'],
            location=inputs['location'],
            company_activity=inputs['company_activity'],
            task_description=inputs['task_description'],
            found_salary_data=[annual_salary],
            task_steps=[TaskBreakdown(**step) for step in task_steps],
            time_analysis=time_analysis,
            cost_projections=cost_projections,
            roi_analysis=ROIAnalysis(
                percentage=300.0,
                calculation_basis="Based on standard automation efficiency metrics"
            )
        )

def create_styles():
    return """
    <style>
    /* Header/Hero Section */
    .hero-container {
        position: relative;
        width: 100%;
        height: 40vh;          /* 40% of viewport height */
        overflow: hidden;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .hero-image {
        position: absolute;
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: brightness(0.5);  /* Darkens image for better text readability */
    }
    .hero-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        color: white;
        width: 80%;
        z-index: 10;           /* Ensures text stays above image */
    }
    .hero-title {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .hero-subtitle {
        font-size: 1.2rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }

    /* CTA Section */
    .cta-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 40px 0;
        width: 100%;
    }
    .cta-title {
        font-size: 2.5rem;
        margin-bottom: 20px;
        color: white;
    }
    .cta-description {
        font-size: 1.2rem;
        margin: 20px 0;
        color: rgba(255, 255, 255, 0.9);
    }
    .cta-buttons {
        margin-top: 30px;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
    }
    .cta-button {
        display: inline-block;
        padding: 15px 40px;
        border-radius: 30px;
        font-weight: bold;
        font-size: 1.1rem;
        text-decoration: none;
        transition: all 0.3s ease;
        min-width: 200px;
    }
    .cta-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    .cta-button.primary {
        background-color: #00ff88;
        color: #1a1a1a;
        box-shadow: 0 4px 15px rgba(0,255,136,0.3);
    }
    .cta-button.secondary {
        background-color: #ff3366;
        color: white;
        box-shadow: 0 4px 15px rgba(255,51,102,0.3);
    }
    
    /* Footer Styling */
    .footer-container {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d3436 100%);
        padding: 3rem;
        border-radius: 15px;
        color: white;
        margin: 40px 0;
    }
    
    @media (min-width: 768px) {
        .footer-content {
            display: flex;
            align-items: flex-start;
            gap: 30px;
        }
        
        .profile-image-container {
            flex: 0 0 auto;
        }
        
        .profile-text {
            flex: 1;
        }
    }
    
    @media (max-width: 767px) {
        .footer-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        
        .profile-image-container {
            margin-bottom: 20px;
        }
    }
    
    .profile-image {
        width: 150px;
        height: 150px;
        border-radius: 75px;
        border: 4px solid #00ff88;
        box-shadow: 0 4px 15px rgba(0,255,136,0.3);
    }
    
    /* Case Studies Grid */
    .case-studies-grid {
        display: grid;
        gap: 2rem;
        margin: 2rem 0;
    }
    
    @media (min-width: 768px) {
        .case-studies-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    .case-study-card {
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .case-study-card:hover {
        transform: translateY(-5px);
    }
    
    .case-study-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 15px 15px 0 0;
    }
    
    .case-study-content {
        padding: 1.5rem;
    }
    
    .kpi-button {
        display: block;
        padding: 12px 20px;
        border-radius: 25px;
        font-size: 1rem;
        margin: 8px 0;
        font-weight: 500;
        width: 100%;
        text-align: center;
        color: white;
        text-decoration: none;
    }
    
    .kpi-cost { 
        background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%); 
    }
    .kpi-time { 
        background: linear-gradient(135deg, #7209b7 0%, #560bad 100%); 
    }
    .kpi-efficiency { 
        background: linear-gradient(135deg, #f72585 0%, #b5179e 100%); 
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        .hero-subtitle {
            font-size: 1rem;
        }
        .cta-title {
            font-size: 2rem;
        }
        .cta-button {
            width: 100%;
            margin: 5px 0;
        }
        .case-studies-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """

def create_donut_chart(task_steps):
    """Create a donut chart for task breakdown with better readability"""
    fig = go.Figure(data=[go.Pie(
        labels=[step.step for step in task_steps],
        values=[round(step.percentage) for step in task_steps],
        hole=.3,
        textposition='outside',  # Move text outside
        textinfo='label+percent',  # Show both label and percentage
        hovertemplate="%{label}<br>%{value:.0f}%<extra></extra>",
        pull=[0.05] * len(task_steps)  # Slightly separate slices
    )])
    
    fig.update_layout(
        showlegend=False,
        height=500,
        margin=dict(t=0, b=0, l=120, r=120),  # Added margins for outside labels
        annotations=[dict(text="Task<br>Breakdown", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig

def create_vertical_waterfall_chart(task_steps):
    """Create a vertical waterfall chart showing cumulative task breakdown"""
    
    # Calculate cumulative percentages
    cumulative = 0
    y_positions = []
    hover_texts = []
    
    for step in task_steps:
        y_positions.append(cumulative + (step.percentage / 2))
        cumulative += step.percentage
        hover_texts.append(f"{step.step}: {step.percentage:.0f}%<br>Cumulative: {cumulative:.0f}%")

    # Create the vertical waterfall chart
    fig = go.Figure()
    
    # Add the bars
    fig.add_trace(go.Bar(
        x=[step.percentage for step in task_steps],
        y=[step.step for step in task_steps],
        orientation='h',
        marker=dict(
            color=['#4361ee', '#3a0ca3', '#7209b7', '#9b5de5', '#f72585'][:len(task_steps)],
            opacity=0.8
        ),
        text=[f"{step.percentage:.0f}%" for step in task_steps],
        textposition='auto',
        hovertext=hover_texts,
        hoverinfo='text'
    ))
    
    # Add cumulative line
    cumulative = 0
    x_line = [0]
    y_line = [task_steps[0].step]
    
    for step in task_steps[:-1]:
        cumulative += step.percentage
        x_line.extend([cumulative, cumulative])
        y_line.extend([step.step, task_steps[task_steps.index(step) + 1].step])

    fig.add_trace(go.Scatter(
        x=x_line,
        y=y_line,
        mode='lines',
        line=dict(color='rgba(0,0,0,0.3)', width=1, dash='dot'),
        hoverinfo='skip',
        showlegend=False
    ))

    # Update layout
    fig.update_layout(
        title={
            'text': "Task Time Breakdown",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        showlegend=False,
        height=400,
        xaxis=dict(
            title="Percentage of Total Time",
            range=[0, 100],
            ticksuffix="%"
        ),
        yaxis=dict(
            title="",
            autorange="reversed"  # This puts first task at top
        ),
        margin=dict(l=200, r=50, t=100, b=50),  # Increased left margin for labels
        bargap=0.15,
        plot_bgcolor='white',
        hovermode='closest'
    )
    
    # Add gridlines
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)'
    )
    
    return fig

def create_time_savings_chart(time_analysis):
    """Create a bar chart comparing time before and after automation"""
    categories = ['Before Automation', 'After Automation']
    values = [time_analysis.hours_per_year_before, time_analysis.hours_per_year_after]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            text=[f"{v:.1f} hours" for v in values],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Annual Hours Comparison",
        yaxis_title="Hours per Year",
        height=400
    )
    return fig

def create_cost_savings_chart(cost_projections, time_analysis):
    """Create a bar chart showing cost savings"""
    hourly_rate = cost_projections.hourly_rate
    before_cost = time_analysis.hours_per_year_before * hourly_rate
    after_cost = time_analysis.hours_per_year_after * hourly_rate
    savings = before_cost - after_cost
    
    fig = go.Figure(data=[
        go.Bar(
            x=['Before Automation', 'After Automation', 'Annual Savings'],
            y=[before_cost, after_cost, savings],
            text=[f"${v:,.2f}" for v in [before_cost, after_cost, savings]],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Cost Analysis",
        yaxis_title="Annual Cost ($)",
        height=400
    )
    return fig

def create_header():
    """Create an attractive header with hero image"""
    st.markdown("""
    <style>
    .hero-container {
        position: relative;
        width: 100%;
        height: 300px;
        overflow: hidden;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .hero-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: brightness(0.7);
    }
    .hero-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        color: white;
        width: 80%;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .hero-subtitle {
        font-size: 1.2rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    </style>
    
    <div class="hero-container">
        <img class="hero-image" src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1500"
             alt="Digital Transformation">
        <div class="hero-text">
            <div class="hero-title">Do you need AI agents?</div>
            <div class="hero-subtitle">Estimate how much time and money you could save by automating your business processes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Update the metrics calculation
def calculate_time_saved_percentage(hours_saved_per_year: float, total_hours: float) -> int:
    """Calculate percentage of time saved per year"""
    return round((hours_saved_per_year / total_hours) * 100)

def display_task_analysis_section(automation_analysis):
    """Display the task analysis section"""
    st.markdown("<h2 style='width: 100%; text-align: center; margin: 40px 0;'>Task Time Analysis</h2>", 
                unsafe_allow_html=True)
    chart = create_vertical_waterfall_chart(automation_analysis.task_steps)
    st.plotly_chart(chart, use_container_width=True)
    create_key_insights(automation_analysis)
    
    # Create and display the waterfall chart
    chart = create_vertical_waterfall_chart(automation_analysis.task_steps)
    st.plotly_chart(chart, use_container_width=True)
    
    # Add insights box
    total_time = automation_analysis.time_analysis.hours_per_year_before
    st.markdown(f"""
    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 20px;'>
        <h4>💡 Key Insights</h4>
        <ul>
            <li>Total annual time investment: <strong>{total_time:.0f} hours</strong></li>
            <li>Largest time investment: <strong>{max(automation_analysis.task_steps, key=lambda x: x.percentage).step}</strong> 
                ({max(automation_analysis.task_steps, key=lambda x: x.percentage).percentage:.0f}% of total time)</li>
            <li>Number of distinct tasks: <strong>{len(automation_analysis.task_steps)}</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def create_case_study_styles():
    """Create simple grid layout for case studies"""
    return """
    <style>
    .case-studies-grid {
        display: grid;
    }
    
    .case-study-card {
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .case-study-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
    }
    
    .case-study-content {
        padding: 1.5px;
    }
    
    .kpi-button {
        display: block;
        padding: 12px 20px;
        border-radius: 25px;
        font-size: 1rem;
        margin: 8px 0;
        font-weight: 500;
        width: 100%;
        text-align: center;
        color: white;
    }
    
    .kpi-cost { background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%); }
    .kpi-time { background: linear-gradient(135deg, #7209b7 0%, #560bad 100%); }
    .kpi-efficiency { background: linear-gradient(135deg, #f72585 0%, #b5179e 100%); }
    
    </style>
    """

def display_case_studies(case_studies):
    """Display case studies using Streamlit's native components"""
    # Apply custom CSS
    st.markdown("""
        <style>
        .case-study-card {
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
            height: 100%;
        }
        .case-study-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        .case-study-title {
            font-size: 1.4rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .case-study-description {
            color: #666;
            margin-bottom: 1rem;
        }
        .case-study-meta {
            font-weight: 500;
            margin-bottom: 1rem;
        }
        .kpi-button {
            background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            margin: 8px 0;
            text-align: center;
            width: 100%;
            display: block;
        }
        .kpi-time {
            background: linear-gradient(135deg, #7209b7 0%, #560bad 100%);
        }
        .kpi-efficiency {
            background: linear-gradient(135deg, #f72585 0%, #b5179e 100%);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## Some practical examples")
    
    # Create three columns for desktop view
    cols = st.columns(3)
    
    # Display each case study in its own column
    for idx, (col, study) in enumerate(zip(cols, case_studies)):
        with col:
            st.markdown(f"""
                <div class="case-study-card">
                    <img src="{study['image']}" class="case-study-image" alt="{study['title']}">
                    <div class="case-study-title">{study['title']}</div>
                    <div class="case-study-description">{study['description']}</div>
                    <div class="case-study-meta">
                        <strong>{study['role']}</strong> • {study['location']}
                    </div>
                    <div class="kpi-button">{study['cost']}</div>
                    <div class="kpi-button kpi-time">{study['time']}</div>
                    <div class="kpi-button kpi-efficiency">{study['efficiency']}</div>
                </div>
            """, unsafe_allow_html=True)


def create_metrics_explanation():
    """Create explanation box for KPIs"""
    st.markdown("""
    <div class="calculation-box">
        <h4>💡 How We Calculate These Metrics</h4>
        <ul style="margin-top: 10px; list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 10px;">
                <strong style="color: #4361ee;">💰 Cost Savings:</strong> 
                Calculated using average salaries from Glassdoor for similar roles, 
                accounting for time saved through automation.
            </li>
            <li style="margin-bottom: 10px;">
                <strong style="color: #3a0ca3;">⏱️ Time Saved:</strong> 
                Based on task frequency × hours per task, representing new capacity 
                gained through automation.
            </li>
            <li style="margin-bottom: 10px;">
                <strong style="color: #7209b7;">📈 Efficiency Gain:</strong> 
                Percentage of total working hours (2,080/year) freed up for 
                high-value activities.
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def create_key_insights(automation_analysis):
    """Create enhanced key insights section"""
    # Find most and least automated tasks
    most_time_task = max(automation_analysis.task_steps, key=lambda x: x.percentage)
    least_time_task = min(automation_analysis.task_steps, key=lambda x: x.percentage)
    
    monthly_hours = automation_analysis.time_analysis.hours_per_task * automation_analysis.time_analysis.times_per_month
    annual_hours = monthly_hours * 12
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 25px;
                border-radius: 15px;
                margin-top: 20px;
                border-left: 4px solid #4361ee;'>
        <h4 style='color: #1a1a1a; margin-bottom: 15px;'>💡 Key Insights</h4>
        <ul style='list-style-type: none; padding-left: 0;'>
            <li style='margin-bottom: 12px;'>
                <strong style='color: #4361ee;'>Time Investment:</strong> 
                Currently spending {annual_hours:.0f} hours annually 
                ({monthly_hours:.1f} hours/month) on this process
            </li>
            <li style='margin-bottom: 12px;'>
                <strong style='color: #3a0ca3;'>Bottleneck Identified:</strong> 
                {most_time_task.step} takes up {most_time_task.percentage:.0f}% of the process time
            </li>
            <li style='margin-bottom: 12px;'>
                <strong style='color: #7209b7;'>Quick Wins:</strong> 
                {least_time_task.step} (only {least_time_task.percentage:.0f}%) 
                could be automated first for immediate impact
            </li>
            <li style='margin-bottom: 12px;'>
                <strong style='color: #ff6b6b;'>Process Complexity:</strong> 
                {len(automation_analysis.task_steps)} distinct steps identified, 
                showing {len(automation_analysis.task_steps) >= 4 and "high" or "moderate"} complexity
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Update the metrics dashboard to show efficiency instead of ROI
def create_metrics_dashboard(automation_analysis, average_annual_salary):
    """Create an enhanced metrics dashboard with better visuals"""
    cols = st.columns(3)
    
    # Calculate efficiency percentage
    annual_hours = 2080  # Standard work hours per year
    efficiency_percentage = calculate_time_saved_percentage(
        automation_analysis.time_analysis.hours_saved_per_year,
        annual_hours
    )
    
    metrics_data = [
        {
            "icon": "💰",
            "label": "Annual Cost Savings",
            "value": f"${int(automation_analysis.cost_projections.annual_task_cost):,}",
            "delta": "Through Automation",
            "color": "#4361ee"
        },
        {
            "icon": "⏱️",
            "label": "Hours Saved Annually",
            "value": f"{int(automation_analysis.time_analysis.hours_saved_per_year):,}",
            "delta": "Productivity Gain",
            "color": "#3a0ca3"
        },
        {
            "icon": "📈",
            "label": "Efficiency Gain",
            "value": f"{efficiency_percentage}%",
            "delta": "Of Annual Hours",
            "color": "#7209b7"
        }
    ]
    
    for col, metric in zip(cols, metrics_data):
        with col:
            st.markdown(f"""
            <div style='background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        border-left: 4px solid {metric["color"]};
                        text-align: center;'>
                <div style='font-size: 32px;'>{metric["icon"]}</div>
                <div style='color: #666;'>{metric["label"]}</div>
                <div style='font-size: 24px; font-weight: bold; color: {metric["color"]};'>{metric["value"]}</div>
                <div style='color: #888; font-size: 14px;'>{metric["delta"]}</div>
            </div>
            """, unsafe_allow_html=True)

def create_footer():
    """Create footer with personal introduction"""
    st.markdown("""
    <style>
    .footer-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 15px;
        color: white;
        margin: 40px 0;
        display: flex;
        align-items: center;
        gap: 30px;
    }
    .profile-image {
        width: 150px;
        height: 150px;
        border-radius: 75px;
        border: 4px solid white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .profile-text {
        flex: 1;
    }
    </style>
    
    <div class="footer-container">
        <div class="footer-content">
            <div class="profile-image-container">
                <a href="https://ibb.co/hm2yXYy">
                    <img src="https://i.ibb.co/qrmd0Jd/DSC01712.jpg" class="profile-image" alt="Vlad" />
                </a>
            </div>
            <div class="profile-text">
                <h3 style="color: white;">👋 Nice to meet you!</h3>
                <p>
                    Hi, I'm Vlad. I started out building AI agents for Fire Scan. A lead-gen agency in the US. I automated parts of my outreach, content creation, and sales process. I'm now helping other entrepreneurs do the same. Reach out if you want to talk anything about AI, automation, entrepreneurship, or triathlons.
                </p>
                <div style='margin-top: 20px; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; display: inline-block;'>
                    <p style='margin: 0; color: white;'>✉️ <span style='font-weight: bold;'>vladimir@fire-scan.com</span></p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)



def create_cta_section():
    return """
    <div class="cta-container">
        <h2 class="cta-title">You still think it doesn't apply to you?</h2>
        <p class="cta-description">See practical examples of how AI agents can help you.</p>
        <div class="cta-buttons">
            <a href='https://cal.com/vladimir-de-ziegler-uyu7qb/15min' 
               target='_blank' 
               class='cta-button primary'>
                🗓️ Let's talk
            </a>
            <a href='https://www.youtube.com/@CrewYourCompany-q2c/videos' 
               target='_blank' 
               class='cta-button secondary'>
                📺 2' mins videos with practical examples
            </a>
        </div>
    </div>
    """

# Constants for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1aDla1mfz8QJ298cUWSt7OUKrdwb3QlHjpc2MZILHwO0'

def load_credentials():
    try:
        # Parse the JSON string from the secret
        token_info = json.loads(st.secrets["gmail_tokens"]["token_json"])
        
        # Create credentials from the parsed JSON
        return Credentials.from_authorized_user_info(token_info, SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {str(e)}")
        return None

def save_to_google_sheets(automation_object: AutomationObject):
    """
    Save automation analysis results to Google Sheets using service account
    """
    try:
        credentials = load_credentials()
        if not credentials:
            print("Failed to load credentials")
            return False

        # Build the Sheets API service
        service = build('sheets', 'v4', credentials=credentials)
        
        # Prepare the data row
        data = [
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                automation_object.job_title,
                automation_object.location,
                automation_object.company_activity,
                automation_object.task_description,
                str(automation_object.time_analysis.hours_saved_per_year),
                f"${automation_object.cost_projections.annual_task_cost:,.2f}",
                f"{automation_object.roi_analysis.percentage}%"
            ]
        ]
        
        # Prepare the request body
        body = {
            'values': data
        }
        
        # Append the row to the sheet
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:H',  # Adjust range as needed
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"Updated {result.get('updates').get('updatedCells')} cells")
        return True
        
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")
        return False

def main():
    # Add custom styles
    st.markdown(create_case_study_styles(), unsafe_allow_html=True)
    st.markdown(create_styles(), unsafe_allow_html=True)

    
    # Hero Header
    # Updated Hero Header with Video
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 1rem; font-size: 3rem; font-weight: bold;">
        Do you even need an AI agent?
    </h1>
    <p style="text-align: center; margin-bottom: 2rem; font-size: 1.5rem; color: #4a5568;">
        Calculate how many hours & dollars you could save with automation 💰
    </p>
    <div style="position: relative; padding-bottom: 56.25%; height: 0; margin-bottom: 2rem;">
        <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
                src="https://www.tella.tv/video/cm3epo9b7000903jw99cs4r0a/embed?b=1&title=1&a=1&loop=0&autoPlay=true&t=0&muted=1&wt=1" 
                allowfullscreen 
                allowtransparency>
        </iframe>
    </div>
    """, unsafe_allow_html=True)
    # st.markdown("""
    # <div class="hero-container">
    #     <img class="hero-image" src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1500"
    #          alt="Digital Transformation">
    #     <div class="hero-text">
    #         <div class="hero-title">Do you need AI agents?</div>
    #         <div class="hero-subtitle">Estimate how much time and money you could save by automating your business processes</div>
    #     </div>
    # </div>
    # """, unsafe_allow_html=True)
    
    # Input Form Container
    with st.container():
        # st.markdown("""
        # <div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        # """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💼 Job Details")
            job_query = st.text_input("Job Title", placeholder="The role to automate (e.g., Senior Procurement Manager)", key="job_title")
            location = st.text_input("Location", placeholder="The location of the role (e.g., New York)", key="location")
            company_activity = st.text_input("Company's main business activity", 
                                           placeholder="What does your company do?",
                                           key="company_activity")

        with col2:
            st.subheader("📋 Task Details")
            task_description = st.text_input("Task Description", 
                                           placeholder="Please describe the specific task that needs automation",
                                           key="task_description")
            hours_per_task = st.number_input("Hours per Task", 
                                           min_value=0.0, max_value=10000.0, value=1.0,
                                           step=0.5,
                                           key="hours_per_task")
            times_per_month = st.number_input("Times per Month", 
                                            min_value=1, max_value=10000, value=1,
                                            key="times_per_month")

        # Center the button
        col1, col2, col3 = st.columns([1,2,1])
        # Add extra space using one of these methods:
        # st.markdown("<br>", unsafe_allow_html=True)  # Option 1
        st.write("")  # Option 2 (can add multiple for more space)
        analyze_button = st.button("🚀 Generate ROI Analysis", type="primary", use_container_width=True)
            
    # Analysis Results Section
    if analyze_button:
        with st.container():
            try:
                # Prepare inputs
                inputs = {
                    "job_query": job_query,
                    "location": location,
                    "company_activity": company_activity,
                    "task_description": task_description,
                    "hours_per_task": hours_per_task,
                    "times_per_month": times_per_month
                }
                
                # Validate inputs
                if not all([job_query, location, company_activity, task_description]):
                    st.error("Please fill in all fields to proceed with the analysis.")
                    return
                
                # Analysis process
                with st.spinner("🔄 Analyzing automation potential..."):
                    # Fetch and analyze salary data
                    search_results = fetch_salary_data(inputs["job_query"], inputs["location"])
                    
                    if not search_results:
                        st.error("Unable to fetch salary data. Please try again.")
                        return
                    
                    snippets = extract_salary_info(search_results)
                    
                    if not snippets:
                        st.error("No relevant salary information found. Please try different job title/location.")
                        return
                    
                    found_salaries = analyze_salaries_with_llm(snippets)
                    
                    if not found_salaries:
                        st.error("Could not determine valid salary information. Please try again.")
                        return
                    
                    average_annual_salary = statistics.mean(found_salaries)
                    
                    # Get automation analysis
                    automation_analysis = analyze_automation_potential(inputs, average_annual_salary)
                    if save_to_google_sheets(automation_analysis):
                        st.success("Analysis completed successfully!")
                    else:
                        st.warning("Analysis completed.")
                    
                    # Display Results
                    # st.success("✨ Analysis completed successfully!")
                    
                    # Metrics Dashboard
                    create_metrics_dashboard(automation_analysis, average_annual_salary)
                    create_metrics_explanation()
                    
                    # Task Analysis
                    st.markdown("<h2 style='width: 100%; text-align: center; margin: 40px 0;'>Task Time Analysis</h2>", 
                              unsafe_allow_html=True)
                    
                    chart = create_vertical_waterfall_chart(automation_analysis.task_steps)
                    st.plotly_chart(chart, use_container_width=True, key="task_waterfall")
                    
                    create_key_insights(automation_analysis)
                    
                    # Add spacing
                    st.markdown("<br>", unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.write("Please try again with different inputs.")
    
    # Case Studies Section
    case_studies = [
        {
            "title": "Share your successes",
            "image": "https://i.ibb.co/fMmCdJZ/bastien-herve-Qeuy-VLx-Jw-BE-unsplash.jpg",
            "role": "Project Manager",
            "location": "Paris",
            "cost": "Cost savings: $9,309 per year",
            "time": "Time saved: 288 hours per year",
            "efficiency": "Efficiency gain: 35% of annual hours",
            "description": "Create case studies automatically to win more clients."
        },
        {
            "title": "Convert more prospects",
            "image": "https://i.ibb.co/34yyhVW/mufid-majnun-v-L5m-CET3i1-U-unsplash.jpg",
            "role": "Strategy Consultant",
            "location": "New York",
            "cost": "Cost savings: $15,240 per year",
            "time": "Time saved: 216 hours per year",
            "efficiency": "Efficiency gain: 42% of annual hours",
            "description": "Automate your pitch creation process to convert more prospects."
        },
        {
            "title": "Validate market demand for your product",
            "image": "https://i.ibb.co/vsBMx1S/charlesdeluvio-7tw1-GLJt7-BU-unsplash.jpg",
            "role": "Product Manager",
            "location": "San Francisco",
            "cost": "Cost savings: $47,690 per year",
            "time": "Time saved: 480 hours per year",
            "efficiency": "Efficiency gain: 23% of annual hours",
            "description": "Validate market demand for your product by automating your research."
        }] 

    st.markdown(create_cta_section(), unsafe_allow_html=True)

    display_case_studies(case_studies)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # st.markdown("<br><br>", unsafe_allow_html=True)
    # st.markdown(create_cta_section(), unsafe_allow_html=True)
    # Add spacing before footer
    # Update the footer section
    st.markdown("""
        <div class="footer-container">
            <div class="footer-content">
                <div class="profile-image-container">
                    <a href="https://ibb.co/hm2yXYy">
                        <img src="https://i.ibb.co/qrmd0Jd/DSC01712.jpg" class="profile-image" alt="Vlad" />
                    </a>
                </div>
                <div class="profile-text">
                    <h3 style="color: white;">👋 Nice to meet you!</h3>
                    <p>
                        Hi, I'm Vlad. I started out building AI agents for Fire Scan. A lead-gen agency in the US. I automated parts of my outreach, content creation, and sales process. I'm now helping other entrepreneurs do the same. Reach out if you want to talk anything about AI, automation, entrepreneurship, or triathlons.
                    </p>
                    <div style='margin-top: 20px; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; display: inline-block;'>
                        <p style='margin: 0; color: white;'>✉️ <span style='font-weight: bold;'>vladimir@fire-scan.com</span></p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()