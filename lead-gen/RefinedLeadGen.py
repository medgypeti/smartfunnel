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
    page_title="Automation ROI Calculator",
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
        "location": "United States",
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
    Extract the first 4 snippet results from the search data
    """
    if not search_results or 'organic' not in search_results:
        return []
        
    snippets = []
    for result in search_results.get('organic', [])[:4]:
        snippets.append(result.get('snippet', ''))
    return snippets

def analyze_salaries_with_llm(snippets: List[str]) -> List[float]:
    """
    Use Groq with LLaMA to analyze salary snippets and extract average total pay
    Returns list of found salaries instead of just the average
    """
    if not snippets:
        return []
        
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    prompt = f"""
    Analyze these salary snippets and extract total compensation figures. Follow these rules:
    1. Only include figures explicitly stated as total pay, total compensation, or total salary
    2. If a range is given, use the average of the range
    3. Convert hourly rates to annual (multiply by 2080)
    4. Ignore experience-based salaries unless they're averages
    5. Return each valid total compensation figure on a new line
    6. Only return the numerical values, no text
    
    For example:
    Input: "The estimated total pay is $100,000 to $120,000"
    Output: 110000
    
    Input: "The average base salary is $80,000 with total compensation of $95,000"
    Output: 95000
    
    Here are the snippets to analyze:
    {json.dumps(snippets, indent=2)}
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama3-70b-8192",
    )
    
    try:
        # Get the response and split it into lines
        response_lines = chat_completion.choices[0].message.content.strip().split('\n')
        
        # Convert each line to a float, removing any non-numeric characters
        salaries = []
        for line in response_lines:
            try:
                cleaned_value = ''.join(c for c in line if c.isdigit() or c == '.')
                if cleaned_value:
                    value = float(cleaned_value)
                    if value > 0:  # Only include positive values
                        salaries.append(value)
            except ValueError:
                continue
        
        return salaries if salaries else []
        
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
        
        time_analysis = {
            "hours_per_task": inputs['hours_per_task'],
            "times_per_month": inputs['times_per_month'],
            "hours_per_year_before": float(''.join(c for c in time_lines[0].split(':')[1] if c.isdigit() or c == '.')),
            "hours_per_year_after": float(''.join(c for c in time_lines[1].split(':')[1] if c.isdigit() or c == '.')),
            "hours_saved_per_year": float(''.join(c for c in time_lines[2].split(':')[1] if c.isdigit() or c == '.'))
        }
        
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
                temperature=0.7
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
            hours_per_year_after=inputs['hours_per_task'] * inputs['times_per_month'] * 12 * 0.2,
            hours_saved_per_year=inputs['hours_per_task'] * inputs['times_per_month'] * 12 * 0.8
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


# def create_styles():
#     return """
#     <style>
#     .hero-container {
#         position: relative;
#         width: 100%;
#         height: 40vh;
#         overflow: hidden;
#         border-radius: 15px;
#         margin-bottom: 2rem;
#     }
#     .hero-image {
#         position: absolute;
#         width: 100%;
#         height: 100%;
#         object-fit: cover;
#         filter: brightness(0.5);
#     }
#     .hero-text {
#         position: absolute;
#         top: 50%;
#         left: 50%;
#         transform: translate(-50%, -50%);
#         text-align: center;
#         color: white;
#         width: 80%;
#         z-index: 10;
#     }
#     .hero-title {
#         font-size: 3rem;
#         font-weight: bold;
#         margin-bottom: 1rem;
#         text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
#     }
#     .hero-subtitle {
#         font-size: 1.2rem;
#         text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
#     }
    
#     /* Case Studies Styling */
#     .case-studies-container {
#         background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
#         padding: 3rem;
#         border-radius: 15px;
#         margin: 2rem 0;
#     }
#     .case-study-card {
#         background: white;
#         border-radius: 15px;
#         box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         overflow: hidden;
#         transition: transform 0.3s ease, box-shadow 0.3s ease;
#         height: 100%;
#         margin: 0 15px;
#     }
#     .case-study-card:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
#     }
#     .case-study-image {
#         width: 100%;
#         height: 200px;
#         object-fit: cover;
#     }
#     .case-study-content {
#         padding: 2rem;
#     }
#     .kpi-button {
#         display: inline-block;
#         padding: 12px 20px;
#         border-radius: 25px;
#         font-size: 1rem;
#         margin: 8px 0;
#         font-weight: 500;
#         width: 100%;
#         text-align: center;
#         color: white;
#         transition: transform 0.2s ease;
#     }
#     .kpi-button:hover {
#         transform: translateY(-2px);
#     }
#     .kpi-cost {
#         background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
#     }
#     .kpi-time {
#         background: linear-gradient(135deg, #7209b7 0%, #560bad 100%);
#     }
#     .kpi-efficiency {
#         background: linear-gradient(135deg, #f72585 0%, #b5179e 100%);
#     }
    
#     /* CTA Styling */
#     .cta-container {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 3rem;
#         border-radius: 15px;
#         color: white;
#         text-align: center;
#         margin: 40px 0;
#     }
#     .cta-button {
#         display: inline-block;
#         padding: 15px 40px;
#         border-radius: 30px;
#         font-weight: bold;
#         margin: 15px;
#         font-size: 1.1rem;
#         text-decoration: none;
#         transition: all 0.3s ease;
#     }
#     .cta-button.primary {
#         background-color: #00ff88;
#         color: #1a1a1a;
#         box-shadow: 0 4px 15px rgba(0,255,136,0.3);
#     }
#     .cta-button.secondary {
#         background-color: #ff3366;
#         color: white;
#         box-shadow: 0 4px 15px rgba(255,51,102,0.3);
#     }
#     .cta-button:hover {
#         transform: translateY(-3px);
#         box-shadow: 0 6px 20px rgba(0,0,0,0.2);
#     }
    
#     /* Footer Styling */
#     .footer-container {
#         background: linear-gradient(135deg, #1a1a1a 0%, #2d3436 100%);
#         padding: 3rem;
#         border-radius: 15px;
#         color: white;
#         margin: 40px 0;
#         display: flex;
#         align-items: center;
#         gap: 30px;
#     }
#     .profile-image {
#         width: 150px;
#         height: 150px;
#         border-radius: 75px;
#         border: 4px solid #00ff88;
#         box-shadow: 0 4px 15px rgba(0,255,136,0.3);
#     }
#     .profile-text {
#         flex: 1;
#     }
#     </style>
#     """

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
    }
    .cta-button {
        display: inline-block;
        padding: 15px 40px;
        border-radius: 30px;
        font-weight: bold;
        margin: 10px 20px;
        font-size: 1.1rem;
        text-decoration: none;
        transition: all 0.3s ease;
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
    .cta-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    
    /* Footer Styling */
    .footer-container {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d3436 100%);
        padding: 3rem;
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
        border: 4px solid #00ff88;
        box-shadow: 0 4px 15px rgba(0,255,136,0.3);
    }
    .profile-text {
        flex: 1;
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

# def create_donut_chart(task_steps):
#     """Create a donut chart for task breakdown"""
#     fig = go.Figure(data=[go.Pie(
#         labels=[step.step for step in task_steps],
#         values=[round(step.percentage) for step in task_steps],  # Rounded values
#         hole=.3,
#         textinfo='label+percent',  # Show labels and percentages
#         hovertemplate="%{label}<br>%{value:.0f}%<extra></extra>"  # Remove decimals in hover
#     )])
#     fig.update_layout(
#         showlegend=False,
#         height=500,
#         margin=dict(t=0, b=0, l=0, r=0)
#     )
#     return fig  


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
            <div class="hero-title">🤖 Automation ROI Calculator</div>
            <div class="hero-subtitle">Transform your business processes with data-driven automation decisions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Update the metrics calculation
def calculate_time_saved_percentage(hours_saved_per_year: float, total_hours: float) -> int:
    """Calculate percentage of time saved per year"""
    return round((hours_saved_per_year / total_hours) * 100)

# def display_task_analysis_section(automation_analysis):
#     """Display the task analysis section with sensitivity slider"""
    
#     st.markdown("<h2 style='width: 100%; text-align: center; margin: 40px 0;'>Task Automation Analysis</h2>", 
#                 unsafe_allow_html=True)
    
#     # Add explanation
#     st.markdown("""
#     <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
#         <h4>📊 How to Read This Chart</h4>
#         <ul>
#             <li>Blue bars show the original time allocation for each task</li>
#             <li>Red bars show the potential time reduction through automation</li>
#             <li>Green bar shows the remaining effort needed after automation</li>
#             <li>Use the slider below to adjust automation effectiveness</li>
#         </ul>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Add sensitivity slider
#     automation_percentage = st.slider(
#         "Automation Effectiveness",
#         min_value=0,
#         max_value=100,
#         value=100,  # Default to 100%
#         step=5,
#         help="Adjust to see how different levels of automation effectiveness impact the results"
#     )
    
#     # Create and display the waterfall chart
#     chart = create_waterfall_chart(automation_analysis.task_steps, automation_percentage)
#     st.plotly_chart(chart, use_container_width=True)
    
#     # Add insights based on selected automation percentage
#     remaining_effort = 100 - automation_percentage
#     st.markdown(f"""
#     <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 20px;'>
#         <h4>💡 Impact Analysis at {automation_percentage}% Automation Effectiveness</h4>
#         <ul>
#             <li>Potential time reduction: <strong>{automation_percentage}%</strong></li>
#             <li>Remaining manual effort: <strong>{remaining_effort}%</strong></li>
#             <li>Estimated annual hours saved: <strong>{(automation_analysis.time_analysis.hours_per_year_before * automation_percentage / 100):.0f} hours</strong></li>
#         </ul>
#     </div>
#     """, unsafe_allow_html=True)

def display_task_analysis_section(automation_analysis):
    """Display the task analysis section"""
    st.markdown("<h2 style='width: 100%; text-align: center; margin: 40px 0;'>Task Time Analysis</h2>", 
                unsafe_allow_html=True)
    chart = create_vertical_waterfall_chart(automation_analysis.task_steps)
    st.plotly_chart(chart, use_container_width=True)
    create_key_insights(automation_analysis)
    
    # st.markdown("<h2 style='width: 100%; text-align: center; margin: 40px 0;'>Task Time Analysis</h2>", 
    #             unsafe_allow_html=True)
    
    # # Add explanation
    # st.markdown("""
    # <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    #     <h4>📊 Understanding the Task Breakdown</h4>
    #     <ul>
    #         <li>Tasks are arranged from top to bottom in sequence</li>
    #         <li>Each bar shows the percentage of total time for that task</li>
    #         <li>Dotted lines show cumulative percentage at each step</li>
    #     </ul>
    # </div>
    # """, unsafe_allow_html=True)
    
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

# def display_case_studies(case_studies):
#     """Display case studies with improved layout"""
#     st.markdown("## Success Stories", unsafe_allow_html=True)
    
#     # Container start
#     st.markdown('<div class="case-studies-grid">', unsafe_allow_html=True)
    
#     # Display each case study
#     for study in case_studies:
#         st.markdown(f"""
#             <div class="case-study-card">
#                 <img class="case-study-image" src="{study['image']}" alt="{study['title']}">
#                 <div class="case-study-content">
#                     <h3>{study['title']}</h3>
#                     <p>{study['description']}</p>
#                     <p><strong>{study['role']}</strong> • {study['location']}</p>
#                     <div class="kpi-button kpi-cost">{study['cost']}</div>
#                     <div class="kpi-button kpi-time">{study['time']}</div>
#                     <div class="kpi-button kpi-efficiency">{study['efficiency']}</div>
#                 </div>
#             </div>
#         """, unsafe_allow_html=True)
    
#     # Container end
#     st.markdown('</div>', unsafe_allow_html=True)

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

    st.markdown("## Success Stories")
    
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


# def create_case_study_cards():
#     """Create enhanced case study cards with consistent design"""
#     case_studies = [
#         {
#             "title": "Marketing Agency Case Study Creation",
#             "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800",
#             "role": "Project Manager",
#             "location": "Paris",
#             "savings": "$9,309/year",
#             "time_saved": "288 hours/year",
#             "roi": "141.15%",
#             "description": "Automated creation of marketing case studies, reducing manual effort and improving consistency.",
#             "color_theme": "#FF6B6B"
#         },
#         {
#             "title": "Private Equity Pitch Deck Automation",
#             "image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800",
#             "role": "Strategy Consultant",
#             "location": "New York",
#             "savings": "$15,240/year",
#             "time_saved": "216 hours/year",
#             "roi": "780%",
#             "description": "Streamlined pitch deck creation process for private equity firms, significantly reducing turnaround time.",
#             "color_theme": "#4ECDC4"
#         },
#         {
#             "title": "Presidential First 100 Days",
#             "image": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=800",
#             "role": "President",
#             "location": "Washington",
#             "savings": "$222,923/year",
#             "time_saved": "1,008 hours/year",
#             "roi": "219.57%",
#             "description": "Optimized executive workflow for the first 100 days in office, enhancing decision-making efficiency.",
#             "color_theme": "#45B7D1"
#         }
#     ]
    
#     st.markdown("""
#     <style>
#     .case-studies-container {
#         background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
#         padding: 2rem;
#         border-radius: 15px;
#         margin: 2rem 0;
#     }
#     .case-study-card {
#         background: white;
#         border-radius: 10px;
#         box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         overflow: hidden;
#         transition: transform 0.3s ease, box-shadow 0.3s ease;
#         height: 100%;
#     }
#     .case-study-card:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
#     }
#     .case-study-image {
#         width: 100%;
#         height: 200px;
#         object-fit: cover;
#     }
#     .case-study-content {
#         padding: 1.5rem;
#     }
#     .metric-pill {
#         display: inline-block;
#         padding: 8px 16px;
#         border-radius: 20px;
#         color: white;
#         font-size: 0.9rem;
#         margin: 5px;
#         font-weight: 500;
#     }
#     .section-title {
#         font-size: 2rem;
#         font-weight: bold;
#         margin-bottom: 1.5rem;
#         text-align: center;
#     }
#     </style>
    
#     <div class="case-studies-container">
#         <div class="section-title">📚 Success Stories</div>
#     """, unsafe_allow_html=True)
    
#     # Create three columns for the cards
#     cols = st.columns(3)
    
#     for col, study in zip(cols, case_studies):
#         with col:
#             st.markdown(f"""
#             <div class="case-study-card">
#                 <img src="{study['image']}" class="case-study-image" alt="{study['title']}">
#                 <div class="case-study-content">
#                     <h3 style="margin-bottom: 1rem;">{study['title']}</h3>
#                     <p style="color: #666; margin-bottom: 1rem;">{study['description']}</p>
#                     <div style="margin-bottom: 1rem;">
#                         <strong>{study['role']}</strong> • {study['location']}
#                     </div>
#                     <div style="margin-bottom: 0.5rem;">
#                         <span class="metric-pill" style="background-color: {study['color_theme']}">
#                             💰 {study['savings']}
#                         </span>
#                     </div>
#                     <div style="margin-bottom: 0.5rem;">
#                         <span class="metric-pill" style="background-color: {study['color_theme']}">
#                             ⏱️ {study['time_saved']}
#                         </span>
#                     </div>
#                     <div>
#                         <span class="metric-pill" style="background-color: {study['color_theme']}">
#                             📈 ROI: {study['roi']}
#                         </span>
#                     </div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)
    
#     st.markdown("</div>", unsafe_allow_html=True)


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

# def create_metrics_dashboard(automation_analysis, average_annual_salary):
#     """Create an enhanced metrics dashboard with better visuals"""
#     st.markdown("""
#     <style>
#     .metric-container {
#         background: linear-gradient(135deg, #f6f8fa, #ffffff);
#         padding: 20px;
#         border-radius: 10px;
#         box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
#     }
#     .highlight-number {
#         font-size: 24px;
#         font-weight: bold;
#         color: #0366d6;
#     }
#     </style>
#     """, unsafe_allow_html=True)
    
#     # Create metrics with enhanced styling
#     cols = st.columns(3)
    
#     metrics_data = [
#         {
#             "icon": "💰",
#             "label": "Annual Cost Savings",
#             "value": f"${automation_analysis.cost_projections.annual_task_cost:,.2f}",
#             "delta": "Through Automation",
#             "color": "#28a745"
#         },
#         {
#             "icon": "⏱️",
#             "label": "Hours Saved Annually",
#             "value": f"{automation_analysis.time_analysis.hours_saved_per_year:,.1f}",
#             "delta": "Productivity Gain",
#             "color": "#0366d6"
#         },
#         {
#             "icon": "📈",
#             "label": "ROI Percentage",
#             "value": f"{automation_analysis.roi_analysis.percentage:.1f}%",
#             "delta": "Return on Investment",
#             "color": "#6f42c1"
#         }
#     ]
    
#     for col, metric in zip(cols, metrics_data):
#         with col:
#             st.markdown(f"""
#             <div class='metric-container' style='border-left: 4px solid {metric["color"]}'>
#                 <div style='font-size: 32px;'>{metric["icon"]}</div>
#                 <div style='color: #666;'>{metric["label"]}</div>
#                 <div class='highlight-number' style='color: {metric["color"]};'>{metric["value"]}</div>
#                 <div style='color: #888; font-size: 14px;'>{metric["delta"]}</div>
#             </div>
#             """, unsafe_allow_html=True)

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
        <img src="/Users/vladimirdeziegler/text_crewai/SmartFunnel/lead-gen/DSC01712.JPG" class="profile-image" alt="Vlad">
        <div class="profile-text">
            <h3 style='margin-bottom: 15px;'>👋 Nice to meet you!</h3>
            <p style='font-size: 1.1rem; line-height: 1.6;'>
                Hi, I'm Vlad. I'm the Founder of Fire Scan. AI agents have completely changed how I run my businesses and I'm excited to help you do the same.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_cta_section():
    return """
    <div class="cta-container">
        <h2 class="cta-title">Ready to Transform Your Business?</h2>
        <p class="cta-description">Let's discuss how we can implement this automation solution for your specific needs.</p>
        <div class="cta-buttons">
            <a href='https://cal.com/vladimir-de-ziegler-uyu7qb/15min' 
               target='_blank' 
               class='cta-button primary'>
                🗓️ Book a Call
            </a>
            <a href='https://www.youtube.com/@CrewYourCompany-q2c' 
               target='_blank' 
               class='cta-button secondary'>
                📺 Watch Our Channel
            </a>
        </div>
    </div>
    """

# def create_cta_section():
#     """Create an eye-catching call-to-action section"""
#     st.markdown("""
#     <style>
#     .cta-container {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 40px;
#         border-radius: 15px;
#         color: white;
#         text-align: center;
#         margin: 40px 0;
#     }
#     .cta-button {
#         display: inline-block;
#         padding: 12px 30px;
#         background-color: white;
#         color: #667eea;
#         text-decoration: none;
#         border-radius: 25px;
#         font-weight: bold;
#         margin: 10px;
#         transition: transform 0.3s ease;
#     }
#     .cta-button:hover {
#         transform: translateY(-2px);
#     }
#     </style>
    
#     <div class='cta-container'>
#         <h2>Ready to Transform Your Business?</h2>
#         <p>Let's discuss how we can implement this automation solution for your specific needs.</p>
#         <div>
#             <a href='https://cal.com/vladimir-de-ziegler-uyu7qb/15min' target='_blank' class='cta-button'>
#                 🗓️ Book a Call
#             </a>
#             <a href='https://www.youtube.com/@CrewYourCompany-q2c' target='_blank' class='cta-button'>
#                 📺 Watch Our Channel
#             </a>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# def main():
#     st.set_page_config(page_title="Automation ROI Calculator", layout="wide")
    
#     # Hero Header
#     st.markdown("""
#     <style>
#     .hero-container {
#         position: relative;
#         width: 100%;
#         height: 300px;
#         overflow: hidden;
#         border-radius: 15px;
#         margin-bottom: 2rem;
#     }
#     .hero-image {
#         width: 100%;
#         height: 100%;
#         object-fit: cover;
#         filter: brightness(0.7);
#     }
#     .hero-text {
#         position: absolute;
#         top: 50%;
#         left: 50%;
#         transform: translate(-50%, -50%);
#         text-align: center;
#         color: white;
#         width: 80%;
#     }
#     .hero-title {
#         font-size: 3rem;
#         font-weight: bold;
#         margin-bottom: 1rem;
#         text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
#     }
#     .hero-subtitle {
#         font-size: 1.2rem;
#         text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
#     }
#     </style>
    
#     <div class="hero-container">
#         <img class="hero-image" src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1500"
#              alt="Digital Transformation">
#         <div class="hero-text">
#             <div class="hero-title">🤖 Automation ROI Calculator</div>
#             <div class="hero-subtitle">Transform your business processes with data-driven automation decisions</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Input form section
#     st.markdown("""
#     <div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
#     """, unsafe_allow_html=True)
    
#     # Create columns for input
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("💼 Job Details")
#         job_query = st.text_input("Job Title", placeholder="e.g., Senior Procurement Manager")
#         location = st.text_input("Location", placeholder="e.g., New York")
#         company_activity = st.text_area("Company's Main Business Activity", 
#                                       placeholder="Please be specific about your company's main business")

#     with col2:
#         st.subheader("📋 Task Details")
#         task_description = st.text_area("Task Description", 
#                                       placeholder="Please describe the specific task that needs automation")
#         hours_per_task = st.number_input("Hours per Task", 
#                                        min_value=1, max_value=100.0, value=1.0)
#         times_per_month = st.number_input("Times per Month", 
#                                         min_value=1, max_value=100, value=1)

#     # Center the button
#     col1, col2, col3 = st.columns([1,2,1])
#     with col2:
#         analyze_button = st.button("🚀 Generate ROI Analysis", type="primary", use_container_width=True)
    
#     st.markdown("</div>", unsafe_allow_html=True)
    
#     # If button is clicked, run analysis
#     if analyze_button:
#         with st.spinner("🔄 Analyzing automation potential..."):
#             try:
#                 # Prepare inputs
#                 inputs = {
#                     "job_query": job_query,
#                     "location": location,
#                     "company_activity": company_activity,
#                     "task_description": task_description,
#                     "hours_per_task": hours_per_task,
#                     "times_per_month": times_per_month
#                 }
                
#                 # Validate inputs
#                 if not all([job_query, location, company_activity, task_description]):
#                     st.error("Please fill in all fields to proceed with the analysis.")
#                     return
                
#                 # Fetch and analyze salary data
#                 with st.spinner("📊 Fetching salary data..."):
#                     search_results = fetch_salary_data(inputs["job_query"], inputs["location"])
                
#                 if not search_results:
#                     st.error("Unable to fetch salary data. Please try again.")
#                     return
                
#                 snippets = extract_salary_info(search_results)
                
#                 if not snippets:
#                     st.error("No relevant salary information found. Please try different job title/location.")
#                     return
                
#                 found_salaries = analyze_salaries_with_llm(snippets)
                
#                 if not found_salaries:
#                     st.error("Could not determine valid salary information. Please try again.")
#                     return
                
#                 average_annual_salary = statistics.mean(found_salaries)
                
#                 # Get automation analysis
#                 with st.spinner("🤖 Generating automation analysis..."):
#                     automation_analysis = analyze_automation_potential(inputs, average_annual_salary)
                
#                 # Display Results in Dashboard Format
#                 st.success("✨ Analysis completed successfully!")
                
#                 # Create enhanced metrics dashboard
#                 create_metrics_dashboard(automation_analysis, average_annual_salary)
                
#                 # Create tabs for different visualizations with icons
#                 tab1, tab2, tab3, tab4 = st.tabs([
#                     "📊 Task Breakdown", 
#                     "⏱️ Time Analysis", 
#                     "💰 Cost Analysis",
#                     "📑 Raw Data"
#                 ])
                
#                 with tab1:
#                     st.markdown("### Task Time Distribution")
#                     st.plotly_chart(create_donut_chart(automation_analysis.task_steps), 
#                                   use_container_width=True)
                
#                 with tab2:
#                     st.markdown("### Time Savings Analysis")
#                     st.plotly_chart(create_time_savings_chart(automation_analysis.time_analysis), 
#                                   use_container_width=True)
                
#                 with tab3:
#                     st.markdown("### Financial Impact")
#                     st.plotly_chart(create_cost_savings_chart(
#                         automation_analysis.cost_projections, 
#                         automation_analysis.time_analysis
#                     ), use_container_width=True)
                
#                 with tab4:
#                     st.markdown("### Detailed Analysis Data")
#                     with st.expander("View Raw JSON Data"):
#                         st.json(json.loads(automation_analysis.model_dump_json()))
                
#                 # AI Recommendations Section
#                 st.markdown("""
#                 <div style='background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
#                            padding: 20px; border-radius: 10px; margin: 20px 0;'>
#                     <h3>🤖 AI Recommendations</h3>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.markdown("### 📈 Process Optimization")
#                     for step in automation_analysis.task_steps:
#                         st.markdown(f"""
#                         - **{step.step}** ({step.percentage:.1f}% of time)
#                         """)
                
#                 with col2:
#                     st.markdown("### 💡 Implementation Insights")
#                     st.markdown(f"""
#                     - Annual time saving potential: {automation_analysis.time_analysis.hours_saved_per_year:.1f} hours
#                     - Estimated cost reduction: ${automation_analysis.cost_projections.annual_task_cost:,.2f}
#                     - ROI: {automation_analysis.roi_analysis.percentage:.1f}%
#                     """)
                
#             except Exception as e:
#                 st.error(f"An error occurred during analysis: {str(e)}")
#                 st.write("Please try again with different inputs.")
#                 st.write("If the error persists, please contact support.")
    
#     # Case Studies Section (always visible)
#     st.markdown("""
#     <style>
#     .case-studies-container {
#         background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
#         padding: 2rem;
#         border-radius: 15px;
#         margin: 2rem 0;
#     }
#     .case-study-card {
#         background: white;
#         border-radius: 10px;
#         box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         overflow: hidden;
#         transition: transform 0.3s ease, box-shadow 0.3s ease;
#         height: 100%;
#     }
#     .case-study-card:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
#     }
#     .case-study-image {
#         width: 100%;
#         height: 200px;
#         object-fit: cover;
#     }
#     .case-study-content {
#         padding: 1.5rem;
#     }
#     .metric-pill {
#         display: inline-block;
#         padding: 8px 16px;
#         border-radius: 20px;
#         color: white;
#         font-size: 0.9rem;
#         margin: 5px;
#         font-weight: 500;
#     }
#     .section-title {
#         font-size: 2rem;
#         font-weight: bold;
#         margin-bottom: 1.5rem;
#         text-align: center;
#     }
#     </style>
#     """, unsafe_allow_html=True)
    
#     # Case Studies Content
#     st.markdown('<div class="case-studies-container">', unsafe_allow_html=True)
#     st.markdown('<div class="section-title">📚 Success Stories</div>', unsafe_allow_html=True)
    
#     # Example cases data
#     case_studies = [
#         {
#             "title": "Marketing Agency Case Study Creation",
#             "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800",
#             "role": "Project Manager",
#             "location": "Paris",
#             "savings": "$9,309/year",
#             "time_saved": "288 hours/year",
#             "roi": "141.15%",
#             "description": "Automated creation of marketing case studies, reducing manual effort and improving consistency.",
#             "color_theme": "#FF6B6B"
#         },
#         {
#             "title": "Private Equity Pitch Deck Automation",
#             "image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800",
#             "role": "Strategy Consultant",
#             "location": "New York",
#             "savings": "$15,240/year",
#             "time_saved": "216 hours/year",
#             "roi": "780%",
#             "description": "Streamlined pitch deck creation process for private equity firms, significantly reducing turnaround time.",
#             "color_theme": "#4ECDC4"
#         },
#         {
#             "title": "Presidential First 100 Days",
#             "image": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=800",
#             "role": "President",
#             "location": "Washington",
#             "savings": "$222,923/year",
#             "time_saved": "1,008 hours/year",
#             "roi": "219.57%",
#             "description": "Optimized executive workflow for the first 100 days in office, enhancing decision-making efficiency.",
#             "color_theme": "#45B7D1"
#         }
#     ]
    
#     # Create three columns for the cards
#     cols = st.columns(3)
    
#     for col, study in zip(cols, case_studies):
#         with col:
#             st.markdown(f"""
#             <div class="case-study-card">
#                 <img src="{study['image']}" class="case-study-image" alt="{study['title']}">
#                 <div class="case-study-content">
#                     <h3 style="margin-bottom: 1rem;">{study['title']}</h3>
#                     <p style="color: #666; margin-bottom: 1rem;">{study['description']}</p>
#                     <div style="margin-bottom: 1rem;">
#                         <strong>{study['role']}</strong> • {study['location']}
#                     </div>
#                     <div style="margin-bottom: 0.5rem;">
#                         <span class="metric-pill" style="background-color: {study['color_theme']}">
#                             💰 {study['savings']}
#                         </span>
#                     </div>
#                     <div style="margin-bottom: 0.5rem;">
#                         <span class="metric-pill" style="background-color: {study['color_theme']}">
#                             ⏱️ {study['time_saved']}
#                         </span>
#                     </div>
#                     <div>
#                         <span class="metric-pill" style="background-color: {study['color_theme']}">
#                             📈 ROI: {study['roi']}
#                         </span>
#                     </div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)
    
#     st.markdown('</div>', unsafe_allow_html=True)
    
#     # Call to Action Section
#     st.markdown("""
#     <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                 padding: 40px;
#                 border-radius: 15px;
#                 color: white;
#                 text-align: center;
#                 margin: 40px 0;'>
#         <h2>Ready to Transform Your Business?</h2>
#         <p style='font-size: 1.2rem; margin: 20px 0;'>Let's discuss how we can implement this automation solution for your specific needs.</p>
#         <div>
#             <a href='https://cal.com/vladimir-de-ziegler-uyu7qb/15min' 
#                target='_blank' 
#                style='display: inline-block;
#                       padding: 12px 30px;
#                       background-color: white;
#                       color: #667eea;
#                       text-decoration: none;
#                       border-radius: 25px;
#                       font-weight: bold;
#                       margin: 10px;
#                       transition: transform 0.3s ease;'>
#                 🗓️ Book a Call
#             </a>
#             <a href='https://www.youtube.com/@CrewYourCompany-q2c' 
#                target='_blank' 
#                style='display: inline-block;
#                       padding: 12px 30px;
#                       background-color: white;
#                       color: #667eea;
#                       text-decoration: none;
#                       border-radius: 25px;
#                       font-weight: bold;
#                       margin: 10px;
#                       transition: transform 0.3s ease;'>
#                 📺 Watch Our Channel
#             </a>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()

# def main():
#     st.markdown(create_case_study_styles(), unsafe_allow_html=True)

#     # st.set_page_config(page_title="Automation ROI Calculator", layout="wide")
    
#     # Hero Header
#     st.markdown("""
#     <style>
#     .hero-container {
#         position: relative;
#         width: 100%;
#         height: 300px;
#         overflow: hidden;
#         border-radius: 15px;
#         margin-bottom: 2rem;
#     }
#     .hero-image {
#         width: 100%;
#         height: 100%;
#         object-fit: cover;
#         filter: brightness(0.7);
#     }
#     .hero-text {
#         position: absolute;
#         top: 50%;
#         left: 50%;
#         transform: translate(-50%, -50%);
#         text-align: center;
#         color: white;
#         width: 80%;
#     }
#     .hero-title {
#         font-size: 3rem;
#         font-weight: bold;
#         margin-bottom: 1rem;
#         text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
#     }
#     .hero-subtitle {
#         font-size: 1.2rem;
#         text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
#     }
#     </style>
    
#     <div class="hero-container">
#         <img class="hero-image" src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1500"
#              alt="Digital Transformation">
#         <div class="hero-text">
#             <div class="hero-title">🤖 Automation ROI Calculator</div>
#             <div class="hero-subtitle">Transform your business processes with data-driven automation decisions</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Input form section
#     st.markdown("""
#     <div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
#     """, unsafe_allow_html=True)
    
#     # Create columns for input
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("💼 Job Details")
#         job_query = st.text_input("Job Title", placeholder="e.g., Senior Procurement Manager")
#         location = st.text_input("Location", placeholder="e.g., New York")
#         company_activity = st.text_input("Company's Main Business Activity", 
#                                        placeholder="Please be specific about your company's main business")

#     with col2:
#         st.subheader("📋 Task Details")
#         task_description = st.text_input("Task Description", 
#                                        placeholder="Please describe the specific task that needs automation")
#         hours_per_task = st.number_input("Hours per Task", 
#                                        min_value=1, max_value=100, value=1,
#                                        step=1)
#         times_per_month = st.number_input("Times per Month", 
#                                         min_value=1, max_value=100, value=1)

#     # Center the button
#     col1, col2, col3 = st.columns([1,2,1])
#     with col2:
#         analyze_button = st.button("🚀 Generate ROI Analysis", type="primary", use_container_width=True)
    
#     st.markdown("</div>", unsafe_allow_html=True)
    
#     if analyze_button:
#         with st.spinner("🔄 Analyzing automation potential..."):
#             try:
#                 # Prepare inputs
#                 inputs = {
#                     "job_query": job_query,
#                     "location": location,
#                     "company_activity": company_activity,
#                     "task_description": task_description,
#                     "hours_per_task": hours_per_task,
#                     "times_per_month": times_per_month
#                 }
                
#                 # Validate inputs
#                 if not all([job_query, location, company_activity, task_description]):
#                     st.error("Please fill in all fields to proceed with the analysis.")
#                     return
                
#                 # Fetch and analyze salary data
#                 with st.spinner("📊 Fetching salary data..."):
#                     search_results = fetch_salary_data(inputs["job_query"], inputs["location"])
                
#                 if not search_results:
#                     st.error("Unable to fetch salary data. Please try again.")
#                     return
                
#                 snippets = extract_salary_info(search_results)
                
#                 if not snippets:
#                     st.error("No relevant salary information found. Please try different job title/location.")
#                     return
                
#                 found_salaries = analyze_salaries_with_llm(snippets)
                
#                 if not found_salaries:
#                     st.error("Could not determine valid salary information. Please try again.")
#                     return
                
#                 average_annual_salary = statistics.mean(found_salaries)
                
#                 # Get automation analysis
#                 with st.spinner("🤖 Generating automation analysis..."):
#                     automation_analysis = analyze_automation_potential(inputs, average_annual_salary)
                
#                 # Display Results in Dashboard Format
#                 st.success("✨ Analysis completed successfully!")
                
#                 # Create enhanced metrics dashboard
#                 create_metrics_dashboard(automation_analysis, average_annual_salary)
#                 create_metrics_explanation()
                
#                 # CTA Before Task Distribution
#                 st.markdown("""
#                 <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                             padding: 40px;
#                             border-radius: 15px;
#                             color: white;
#                             text-align: center;
#                             margin: 40px 0;
#                             width: 100%;'>
#                     <h2 style='font-size: 2.5rem; margin-bottom: 20px;'>Ready to Transform Your Business?</h2>
#                     <p style='font-size: 1.2rem; margin: 20px 0;'>Let's discuss how we can implement this automation solution for your specific needs.</p>
#                     <div style='margin-top: 30px;'>
#                         <a href='https://cal.com/vladimir-de-ziegler-uyu7qb/15min' 
#                            target='_blank' 
#                            style='display: inline-block;
#                                   padding: 15px 40px;
#                                   background-color: #00ff88;
#                                   color: #1a1a1a;
#                                   text-decoration: none;
#                                   border-radius: 30px;
#                                   font-weight: bold;
#                                   margin: 10px 20px;
#                                   font-size: 1.1rem;
#                                   box-shadow: 0 4px 15px rgba(0,255,136,0.3);
#                                   transition: all 0.3s ease;'>
#                             🗓️ Book a Call
#                         </a>
#                         <a href='https://www.youtube.com/@CrewYourCompany-q2c' 
#                            target='_blank' 
#                            style='display: inline-block;
#                                   padding: 15px 40px;
#                                   background-color: #ff3366;
#                                   color: white;
#                                   text-decoration: none;
#                                   border-radius: 30px;
#                                   font-weight: bold;
#                                   margin: 10px 20px;
#                                   font-size: 1.1rem;
#                                   box-shadow: 0 4px 15px rgba(255,51,102,0.3);
#                                   transition: all 0.3s ease;'>
#                             📺 Watch Our Channel
#                         </a>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 # Task Distribution
#                 display_task_analysis_section(automation_analysis)
#                 # st.markdown("<h2 style='width: 100%; text-align: center; margin: 40px 0;'>Task Time Distribution</h2>", unsafe_allow_html=True)
#                 # st.plotly_chart(create_donut_chart(automation_analysis.task_steps), use_container_width=True)
                
#                 # Raw Data (optional, can be removed if not needed)
#                 with st.expander("View Raw Analysis Data"):
#                     st.json(json.loads(automation_analysis.model_dump_json()))
                
#             except Exception as e:
#                 st.error(f"An error occurred during analysis: {str(e)}")
#                 st.write("Please try again with different inputs.")

#     st.markdown("""
#     <style>
#     .case-studies-container {
#         background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
#         padding: 2rem;
#         border-radius: 15px;
#         margin: 2rem 0;
#     }
#     .case-study-card {
#         background: white;
#         border-radius: 10px;
#         box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         overflow: hidden;
#         transition: transform 0.3s ease, box-shadow 0.3s ease;
#         height: 100%;
#     }
#     .case-study-card:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
#     }
#     .case-study-image {
#         width: 100%;
#         height: 200px;
#         object-fit: cover;
#     }
#     .case-study-content {
#         padding: 1.5rem;
#     }
#     .metric-button {
#         display: inline-block;
#         padding: 8px 16px;
#         background-color: rgba(0, 0, 0, 0.1);
#         border-radius: 20px;
#         color: #333;
#         font-size: 0.9rem;
#         margin: 5px;
#         font-weight: 500;
#         width: calc(100% - 10px);
#         text-align: center;
#     }
#     .section-title {
#         font-size: 2rem;
#         font-weight: bold;
#         margin-bottom: 1.5rem;
#         text-align: center;
#     }
#     </style>
    
#     <div class="case-studies-container">
#         <div class="section-title">📚 Success Stories</div>
#     """, unsafe_allow_html=True)
    
#     # Example cases data
#     case_studies = [
#         {
#             "title": "Marketing Agency Case Study Creation",
#             "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800",
#             "role": "Project Manager",
#             "location": "Paris",
#             "savings": "$9,309/year",
#             "time_saved": "288 hours/year",
#             "roi": "141%",
#             "description": "Automated creation of marketing case studies, reducing manual effort and improving consistency.",
#             "color_theme": "#FF6B6B"
#         },
#         {
#             "title": "Private Equity Pitch Deck Automation",
#             "image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800",
#             "role": "Strategy Consultant",
#             "location": "New York",
#             "savings": "$15,240/year",
#             "time_saved": "216 hours/year",
#             "roi": "780%",
#             "description": "Streamlined pitch deck creation process for private equity firms, significantly reducing turnaround time.",
#             "color_theme": "#4ECDC4"
#         },
#         {
#             "title": "Presidential First 100 Days",
#             "image": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=800",
#             "role": "President",
#             "location": "Washington",
#             "savings": "$222,923/year",
#             "time_saved": "1,008 hours/year",
#             "roi": "220%",
#             "description": "Optimized executive workflow for the first 100 days in office, enhancing decision-making efficiency.",
#             "color_theme": "#45B7D1"
#         }
#     ]
    
#     # Create three columns for the cards
#     cols = st.columns(3)
    
#     for col, study in zip(cols, case_studies):
#         with col:
#             st.markdown(f"""
#             <div class="case-study-card">
#                 <img src="{study['image']}" class="case-study-image" alt="{study['title']}">
#                 <div class="case-study-content">
#                     <h3 style="margin-bottom: 1rem;">{study['title']}</h3>
#                     <p style="color: #666; margin-bottom: 1rem;">{study['description']}</p>
#                     <div style="margin-bottom: 1rem;">
#                         <strong>{study['role']}</strong> • {study['location']}
#                     </div>
#                     <div class="metric-button">
#                         💰 {study['savings']}
#                     </div>
#                     <div class="metric-button">
#                         ⏱️ {study['time_saved']}
#                     </div>
#                     <div class="metric-button">
#                         📈 ROI: {study['roi']}
#                     </div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)
    
#     st.markdown('</div>', unsafe_allow_html=True)

#     # # Case Studies Section
#     # st.markdown("""
#     # <div class="case-studies-container">
#     #     <div class="section-title">📚 Success Stories</div>
#     # """, unsafe_allow_html=True)
    
#     # # Example cases data
#     # case_studies = [
#     #     {
#     #         "title": "Marketing Agency Case Study Creation",
#     #         "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800",
#     #         "role": "Project Manager",
#     #         "location": "Paris",
#     #         "savings": "$9,309/year",
#     #         "time_saved": "288 hours/year",
#     #         "roi": "141%",
#     #         "description": "Automated creation of marketing case studies, reducing manual effort and improving consistency.",
#     #         "color_theme": "#FF6B6B"
#     #     },
#     #     {
#     #         "title": "Private Equity Pitch Deck Automation",
#     #         "image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800",
#     #         "role": "Strategy Consultant",
#     #         "location": "New York",
#     #         "savings": "$15,240/year",
#     #         "time_saved": "216 hours/year",
#     #         "roi": "780%",
#     #         "description": "Streamlined pitch deck creation process for private equity firms, significantly reducing turnaround time.",
#     #         "color_theme": "#4ECDC4"
#     #     },
#     #     {
#     #         "title": "Presidential First 100 Days",
#     #         "image": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=800",
#     #         "role": "President",
#     #         "location": "Washington",
#     #         "savings": "$222,923/year",
#     #         "time_saved": "1,008 hours/year",
#     #         "roi": "220%",
#     #         "description": "Optimized executive workflow for the first 100 days in office, enhancing decision-making efficiency.",
#     #         "color_theme": "#45B7D1"
#     #     }
#     # ]
    
#     # # Create three columns for the cards
#     # cols = st.columns(3)
    
#     # for col, study in zip(cols, case_studies):
#     #     with col:
#     #         st.markdown(f"""
#     #         <div class="case-study-card">
#     #             <img src="{study['image']}" class="case-study-image" alt="{study['title']}">
#     #             <div class="case-study-content">
#     #                 <h3 style="margin-bottom: 1rem;">{study['title']}</h3>
#     #                 <p style="color: #666; margin-bottom: 1rem;">{study['description']}</p>
#     #                 <div style="margin-bottom: 1rem;">
#     #                     <strong>{study['role']}</strong> • {study['location']}
#     #                 </div>
#     #                 <div style="margin-bottom: 0.5rem;">
#     #                     <span class="metric-pill" style="background-color: {study['color_theme']}">
#     #                         💰 {study['savings']}
#     #                     </span>
#     #                 </div>
#     #                 <div style="margin-bottom: 0.5rem;">
#     #                     <span class="metric-pill" style="background-color: {study['color_theme']}">
#     #                         ⏱️ {study['time_saved']}
#     #                     </span>
#     #                 </div>
#     #                 <div>
#     #                     <span class="metric-pill" style="background-color: {study['color_theme']}">
#     #                         📈 ROI: {study['roi']}
#     #                     </span>
#     #                 </div>
#     #             </div>
#     #         </div>
#     #         """, unsafe_allow_html=True)
    
#     # st.markdown('</div>', unsafe_allow_html=True)
    
#     # Final Call to Action
#     st.markdown("""
#     <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                 padding: 40px;
#                 border-radius: 15px;
#                 color: white;
#                 text-align: center;
#                 margin: 40px 0;
#                 width: 100%;'>
#         <h2 style='font-size: 2.5rem; margin-bottom: 20px;'>Start Your Automation Journey Today</h2>
#         <p style='font-size: 1.2rem; margin: 20px 0;'>Book a call to discuss your specific needs or check out our success stories on YouTube.</p>
#         <div style='margin-top: 30px;'>
#             <a href='https://cal.com/vladimir-de-ziegler-uyu7qb/15min' 
#                target='_blank' 
#                style='display: inline-block;
#                       padding: 15px 40px;
#                       background-color: #00ff88;
#                       color: #1a1a1a;
#                       text-decoration: none;
#                       border-radius: 30px;
#                       font-weight: bold;
#                       margin: 10px 20px;
#                       font-size: 1.1rem;
#                       box-shadow: 0 4px 15px rgba(0,255,136,0.3);
#                       transition: all 0.3s ease;'>
#                 🗓️ Book a Call
#             </a>
#             <a href='https://www.youtube.com/@CrewYourCompany-q2c' 
#                target='_blank' 
#                style='display: inline-block;
#                       padding: 15px 40px;
#                       background-color: #ff3366;
#                       color: white;
#                       text-decoration: none;
#                       border-radius: 30px;
#                       font-weight: bold;
#                       margin: 10px 20px;
#                       font-size: 1.1rem;
#                       box-shadow: 0 4px 15px rgba(255,51,102,0.3);
#                       transition: all 0.3s ease;'>
#                 📺 Watch Our Channel
#             </a>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# create_footer()

def main():
    # Add custom styles
    st.markdown(create_case_study_styles(), unsafe_allow_html=True)
    st.markdown(create_styles(), unsafe_allow_html=True)

    
    # Hero Header
    st.markdown("""
    <div class="hero-container">
        <img class="hero-image" src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1500"
             alt="Digital Transformation">
        <div class="hero-text">
            <div class="hero-title">🤖 Automation ROI Calculator</div>
            <div class="hero-subtitle">Transform your business processes with data-driven automation decisions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Input Form Container
    with st.container():
        # st.markdown("""
        # <div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        # """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💼 Job Details")
            job_query = st.text_input("Job Title", placeholder="e.g., Senior Procurement Manager", key="job_title")
            location = st.text_input("Location", placeholder="e.g., New York", key="location")
            company_activity = st.text_input("Company's Main Business Activity", 
                                           placeholder="Please be specific about your company's main business",
                                           key="company_activity")

        with col2:
            st.subheader("📋 Task Details")
            task_description = st.text_input("Task Description", 
                                           placeholder="Please describe the specific task that needs automation",
                                           key="task_description")
            hours_per_task = st.number_input("Hours per Task", 
                                           min_value=1, max_value=100, value=1,
                                           step=1,
                                           key="hours_per_task")
            times_per_month = st.number_input("Times per Month", 
                                            min_value=1, max_value=100, value=1,
                                            key="times_per_month")

        # Center the button
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            analyze_button = st.button("🚀 Generate ROI Analysis", type="primary", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
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
                    
                    # Display Results
                    st.success("✨ Analysis completed successfully!")
                    
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
            "title": "Marketing Agency Case Study Creation",
            "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800",
            "role": "Project Manager",
            "location": "Paris",
            "cost": "Cost savings: $9,309 per year",
            "time": "Time saved: 288 hours per year",
            "efficiency": "Efficiency gain: 35% of annual hours",
            "description": "Automated creation of marketing case studies, reducing manual effort and improving consistency."
        },
        {
            "title": "Private Equity Pitch Deck Automation",
            "image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800",
            "role": "Strategy Consultant",
            "location": "New York",
            "cost": "Cost savings: $15,240 per year",
            "time": "Time saved: 216 hours per year",
            "efficiency": "Efficiency gain: 42% of annual hours",
            "description": "Streamlined pitch deck creation process for private equity firms, significantly reducing turnaround time."
        },
        {
            "title": "Presidential First 100 Days",
            "image": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=800",
            "role": "President",
            "location": "Washington",
            "cost": "Cost savings: $222,923 per year",
            "time": "Time saved: 1,008 hours per year",
            "efficiency": "Efficiency gain: 48% of annual hours",
            "description": "Optimized executive workflow for the first 100 days in office, enhancing decision-making efficiency."
        }
    ]
    
    display_case_studies(case_studies)
    # case_studies = [
    #     {
    #         "title": "Marketing Agency Case Study Creation",
    #         "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800",
    #         "role": "Project Manager",
    #         "location": "Paris",
    #         "cost": "Cost savings: $9,309 per year",
    #         "time": "Time saved: 288 hours per year",
    #         "efficiency": "Efficiency gain: 35% of annual hours",
    #         "description": "Automated creation of marketing case studies, reducing manual effort and improving consistency."
    #     },
    #     {
    #         "title": "Private Equity Pitch Deck Automation",
    #         "image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800",
    #         "role": "Strategy Consultant",
    #         "location": "New York",
    #         "cost": "Cost savings: $15,240 per year",
    #         "time": "Time saved: 216 hours per year",
    #         "efficiency": "Efficiency gain: 42% of annual hours",
    #         "description": "Streamlined pitch deck creation process for private equity firms, significantly reducing turnaround time."
    #     },
    #     {
    #         "title": "Presidential First 100 Days",
    #         "image": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=800",
    #         "role": "President",
    #         "location": "Washington",
    #         "cost": "Cost savings: $222,923 per year",
    #         "time": "Time saved: 1,008 hours per year",
    #         "efficiency": "Efficiency gain: 48% of annual hours",
    #         "description": "Optimized executive workflow for the first 100 days in office, enhancing decision-making efficiency."
    #     }
    # ]
    # # Case Studies Section
    # st.markdown("<h2 style='font-size: 2.8rem; text-align: center; margin: 3rem 0; font-weight: bold;'>📚 Success Stories</h2>", 
    #             unsafe_allow_html=True)
    
    # st.markdown('<div class="case-studies-grid">', unsafe_allow_html=True)
    
    # for study in case_studies:
    #     st.markdown(f"""
    #         <div class="case-study-card">
    #             <img src="{study['image']}" class="case-study-image" alt="{study['title']}">
    #             <div class="case-study-content">
    #                 <h3 style="font-size: 1.4rem; margin-bottom: 1rem;">{study['title']}</h3>
    #                 <p style="color: #666; margin-bottom: 1.5rem;">{study['description']}</p>
    #                 <div style="margin-bottom: 1.5rem;">
    #                     <strong>{study['role']}</strong> • {study['location']}
    #                 </div>
    #                 <div class="kpi-button kpi-cost">
    #                     💰 {study['cost']}
    #                 </div>
    #                 <div class="kpi-button kpi-time">
    #                     ⏱️ {study['time']}
    #                 </div>
    #                 <div class="kpi-button kpi-efficiency">
    #                     📈 {study['efficiency']}
    #                 </div>
    #             </div>
    #         </div>
    #     """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(create_cta_section(), unsafe_allow_html=True)
    # Add spacing before footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div class="footer-container">
        <a href="https://ibb.co/vwWs3np">
            <img src="https://i.ibb.co/LkyQx7m/DSC01712.jpg" class="profile-image" alt="Vlad" />
        </a>
        <div class="profile-text">
            <h3 style="color: white;">👋 Nice to meet you!</h3>
            <p>
            Hi, I'm Vlad. I've been running my own lead-gen businesses. AI agents have changed how I run my businesses
            and realised this could apply to so many other people. I started helping out friends who were entrepreneurs
            and decided to turn this into an agency. Reach out if you want to talk anything about AI, automation,
            entrepreneurship, running, or surfing.
            </p>
        </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()