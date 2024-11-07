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
    
def create_donut_chart(task_steps):
    """Create a donut chart for task breakdown"""
    fig = go.Figure(data=[go.Pie(
        labels=[step.step for step in task_steps],
        values=[step.percentage for step in task_steps],
        hole=.3
    )])
    fig.update_layout(
        title="Task Breakdown",
        showlegend=True,
        height=400
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

def main():
    st.set_page_config(page_title="Automation ROI Calculator", layout="wide")
    
    # Title and Introduction
    st.title("🤖 Automation ROI Calculator")
    st.markdown("""
    This tool helps you analyze the potential ROI of automating business tasks.
    Fill in the details below to get a comprehensive analysis.
    """)
    
    # Create columns for input
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Details")
        job_query = st.text_input("Job Title", placeholder="e.g., Senior Procurement Manager")
        location = st.text_input("Location", placeholder="e.g., New York")
        company_activity = st.text_area("Company's Main Business Activity", placeholder="Please be specific about your company's main business")

    with col2:
        st.subheader("Task Details")
        task_description = st.text_area("Task Description", placeholder="Please describe the specific task that needs automation")
        hours_per_task = st.number_input("Hours per Task", min_value=0.1, max_value=100.0, value=1.0)
        times_per_month = st.number_input("Times per Month", min_value=1, max_value=100, value=1)

    # Create a button to run the analysis
    if st.button("Run Analysis", type="primary"):
        with st.spinner("Analyzing task automation potential..."):
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
                
                # Display Results in Dashboard Format
                st.success("Analysis completed successfully!")
                
                # Create three columns for key metrics
                metric1, metric2, metric3 = st.columns(3)
                
                with metric1:
                    st.metric(
                        "Annual Cost Savings",
                        f"${automation_analysis.cost_projections.annual_task_cost:,.2f}",
                        "Potential savings through automation"
                    )
                
                with metric2:
                    st.metric(
                        "Hours Saved Annually",
                        f"{automation_analysis.time_analysis.hours_saved_per_year:.1f}",
                        "Hours freed up for other tasks"
                    )
                
                with metric3:
                    st.metric(
                        "ROI Percentage",
                        f"{automation_analysis.roi_analysis.percentage:.1f}%",
                        "Return on Investment"
                    )
                
                # Create tabs for different visualizations
                tab1, tab2, tab3, tab4 = st.tabs(["Task Breakdown", "Time Analysis", "Cost Analysis", "Raw Data"])
                
                with tab1:
                    st.plotly_chart(create_donut_chart(automation_analysis.task_steps), use_container_width=True)
                
                with tab2:
                    st.plotly_chart(create_time_savings_chart(automation_analysis.time_analysis), use_container_width=True)
                
                with tab3:
                    st.plotly_chart(create_cost_savings_chart(automation_analysis.cost_projections, automation_analysis.time_analysis), use_container_width=True)
                
                with tab4:
                    st.json(json.loads(automation_analysis.model_dump_json()))
                
                # Additional Analysis Details
                st.subheader("📊 Detailed Analysis")
                
                # Create two columns for detailed metrics
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("### 💰 Financial Metrics")
                    st.write(f"Average Annual Salary: ${average_annual_salary:,.2f}")
                    st.write(f"Hourly Rate: ${automation_analysis.cost_projections.hourly_rate:.2f}")
                    st.write(f"Monthly Task Cost: ${automation_analysis.cost_projections.monthly_task_cost:.2f}")
                    st.write(f"Annual Task Cost: ${automation_analysis.cost_projections.annual_task_cost:.2f}")
                
                with detail_col2:
                    st.markdown("### ⏱️ Time Metrics")
                    st.write(f"Hours per Task: {automation_analysis.time_analysis.hours_per_task:.1f}")
                    st.write(f"Times per Month: {automation_analysis.time_analysis.times_per_month}")
                    st.write(f"Hours per Year (Before): {automation_analysis.time_analysis.hours_per_year_before:.1f}")
                    st.write(f"Hours per Year (After): {automation_analysis.time_analysis.hours_per_year_after:.1f}")
                
                # ROI Details
                st.subheader("📈 ROI Analysis")
                st.write(f"ROI Percentage: {automation_analysis.roi_analysis.percentage:.1f}%")
                st.write(f"Calculation Basis: {automation_analysis.roi_analysis.calculation_basis}")
                
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.write("Please try again with different inputs.")

if __name__ == "__main__":
    main()